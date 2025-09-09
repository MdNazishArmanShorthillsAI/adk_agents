# Google ADK: Sessions, Events, Databases, and APIs

> Version: 1.1 • Scope: Session lifecycle, event persistence, DB setup (SQLite/Postgres), APIs, ops, FAQs

[Image: High-level architecture diagram showing Client → ADK Web → Session Service (DB) and Agent Runner producing Events]

```mermaid
flowchart LR
  A[Client] --> B[ADK Web / API]
  B --> C[Session Service]
  C --> D[(Database)]
  B --> E[Agent Runner]
  E -->|Events| C
  C -->|Append Events & State Merge| D
```

## Session Service: Interfaces and Wiring

- **Base contract**
  - **Methods (async)**: `create_session`, `get_session`, `list_sessions`, `delete_session`.
  - **append_event(session, event)** merges `EventActions.state_delta` into `session.state` and appends the event.

- **Implementations**
  - **InMemorySessionService**: dev-only.
  - **DatabaseSessionService**: SQLAlchemy-based, supports SQLite, Postgres, MySQL.

- **Wiring**
  - **CLI**: `adk web --session_service_uri=sqlite:///...` or `postgresql+psycopg2://...`
  - **Programmatic**: `get_fast_api_app` builds session service based on URI.

- **State merging**
  - State delta keys may be plain (session), `State.USER_PREFIX`, `State.APP_PREFIX` for scoping.

[Image: Sequence diagram: /run request → load session → runner generates events → append_event → state merge → store events]

```mermaid
sequenceDiagram
  autonumber
  participant Client
  participant ADK as ADK Web
  participant SVC as Session Service
  participant DB as DB
  participant Runner

  Client->>ADK: POST /run(newMessage)
  ADK->>SVC: get_session(app,user,session)
  SVC-->>ADK: Session (events,state)
  ADK->>Runner: run_async(newMessage, prior events)
  loop for each emitted Event
    Runner-->>ADK: Event
    ADK->>SVC: append_event(session, Event)
    SVC->>SVC: merge actions.state_delta → session.state
    SVC->>DB: persist session + event
    ADK-->>Client: Event (SSE frame or batched)
  end
```

## Event Model and State Delta

- **Event core fields**
  - **author**: "user" or agent name
  - **content**: `parts` array (text, tool calls/responses)
  - **actions**: `EventActions { state_delta, artifact_delta, ... }`
  - **timestamp, id, invocation_id**

- **Final response behavior**
  - `is_final_response()` true when not a function call/response and not partial.

- **State delta**
  - Use to persist derived values (e.g., `search_results`) into `session.state`.
  - Agents can set `output_key` to automatically save final output into state.

[Image: JSON sample of an Event with content.parts and actions.state_delta callout]

```json
{
  "id": "a1b2c3",
  "author": "orchestration_agent",
  "timestamp": 1724250000.123,
  "content": {
    "parts": [
      { "text": "Final answer about the 2024 annual report challenges..." }
    ]
  },
  "actions": {
    "stateDelta": {
      "search_results": { "report": "2024", "challenges": ["supply chain", "cost pressure"] }
    }
  }
}
```

## Database Backends and Schema

- **SQLite**
  - **URI**: `sqlite:///relative.db` or `sqlite:////abs/path.db`
  - Local dev, simple file-based.

- **Postgres**
  - **URI**: `postgresql+psycopg2://user:pass@host:5432/db`
  - Requires installing `psycopg2-binary` (or psycopg v3).

- **Tables (conceptual)**
  - **sessions**: `(app_name, user_id, id, state, create_time, update_time)`
  - **events**: `(app_name, user_id, session_id, id, author, content, actions, timestamp, branch, etc.)`

- **Migrations**
  - ADK auto-creates tables. If you used a legacy schema, start with a fresh DB or drop conflicting tables.

[Image: ER diagram: sessions 1-to-many events; events include author/content/actions]

```mermaid
erDiagram
  SESSIONS {
    string app_name PK
    string user_id PK
    string id PK
    jsonb state
    datetime create_time
    datetime update_time
  }
  EVENTS {
    string app_name
    string user_id
    string session_id
    string id
    string author
    jsonb content
    jsonb actions
    float timestamp
    string branch
  }
  SESSIONS ||--o{ EVENTS : contains
```

## API Endpoints

- **Create session with server-generated ID**
  - `POST /apps/{app_name}/users/{user_id}/sessions`

- **Create session with client ID**
  - `POST /apps/{app_name}/users/{user_id}/sessions/{session_id}`

- **List sessions**
  - `GET /apps/{app_name}/users/{user_id}/sessions`

- **Delete session**
  - `DELETE /apps/{app_name}/users/{user_id}/sessions/{session_id}`

- **Run once (batched)**
  - `POST /run` with `{appName, userId, sessionId, newMessage, streaming:false}`
  - Returns `list[Event]`

- **Run with SSE streaming**
  - `POST /run_sse` with `{appName, userId, sessionId, newMessage, streaming:true}`
  - Returns `text/event-stream` with per-event JSON frames

[Image: API flow diagram: client hitting /apps/* for session then /run or /run_sse]

```mermaid
flowchart TD
  CS[Create Session] --> R1[POST /run]
  CS --> R2[POST /run_sse]
  R2 -->|SSE Frames| Client
  R1 -->|Events Array| Client
```

## Chat History Usage Patterns

- **Implicit context**
  - ADK injects prior Events for the same session into agent runs.

- **Explicit state**
  - Use `output_key` or `EventActions.state_delta` to store structured outputs.

- **Summarization pattern**
  - Prepend summaries of last N events into state (`conversation_summary`) for long sessions.

- **Branching**
  - `Event.branch` allows sub-agent scoping so peers don’t see each other’s history.

[Image: Flow showing prior Events funneling into an agent’s prompt/context]

```mermaid
flowchart LR
  H[(Prior Events)] --> P[Prompt Builder]
  S[session.state] --> P
  P --> M[Model Call]
  M --> E[New Event]
  E --> H
  E --> S
```

## Operations and Observability

- **Running locally**
  - `adk web --session_service_uri=sqlite:///adk_sessions.db --port=8010`

- **Logging**
  - Use `--log_level DEBUG`; stream events via `/run_sse` for live traces.
  - Client-side: write SSE frames to JSONL (as in `http_call_sse.py`).

- **SQL checks (Postgres)**
  - **List sessions by recency:**
    - `SELECT id, update_time FROM sessions WHERE app_name='agents' AND user_id='user' ORDER BY update_time DESC;`
  - **Count events per session:**
    - `SELECT session_id, COUNT(*) FROM events WHERE app_name='agents' AND user_id='user' GROUP BY session_id ORDER BY 2 DESC;`
  - **Full history:**
    - `SELECT * FROM events WHERE app_name='agents' AND user_id='user' AND session_id='<id>' ORDER BY timestamp ASC;`

[Image: Screenshot placeholder of psql results for sessions/events]

## Troubleshooting

- **SQLite “no such column: sessions.id”**
  - You’re using an old custom schema. Use a fresh DB or drop old tables.

- **Postgres driver errors**
  - Install `psycopg2-binary` or `psycopg[binary]` and match the URL scheme.

- **Port already in use**
  - Change `--port` or kill the process holding the port.

- **Tool errors “not found”**
  - Start dependent services (e.g., `placeholder_nth_api.py` on 8002).

## FAQs

- **Does ADK store chat history automatically?**
  - Yes, Events are persisted per session in the configured database.

- **How do agents see history?**
  - ADK retrieves prior Events for the session and provides them to the runner.

- **How do I save structured outputs?**
  - Use `output_key` on an agent or populate `actions.state_delta` in an Event.

- **Can I shard state across app/user/session?**
  - Yes: `EventActions` supports app/user prefixes; ADK merges accordingly.

- **How big can history get?**
  - Use list/get with config (e.g., `num_recent_events`) and summarization to manage size.

- **How to export a session?**
  - List events for the session and dump as JSON; artifacts are accessible via artifact service APIs.

- **Can I query by author/tool?**
  - Filter events by author; function calls/responses are in `content.parts`.

---

**Suggested images (placeholders)**
- Architecture diagram: high-level system (PNG/SVG).
- Sequence diagram: run request to DB persistence (SSE path too).
- Event JSON callout: annotated event with `actions.state_delta`.
- ER diagram: sessions and events tables.
- API flow: create session then run/run_sse.
- DB screenshots: psql queries output.
- Web UI screenshots: session list, event stream. 