from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI()

class SearchQuery(BaseModel):
    query: str

mock_db = {
    "2024 annual client report": [
        {
            "id": "doc-001",
            "source": "NTH_DB",
            "content": "The 2024 annual report shows a 15% increase in revenue, primarily driven by the new SaaS division. Key challenges include supply chain disruptions.",
            "metadata": {"year": 2024, "type": "Annual Report"}
        }
    ],
    "tax implications document xyz": [
        {
            "id": "doc-002",
            "source": "NTH_DB",
            "content": "Document XYZ outlines that increased revenue from digital services may be subject to a new 5% digital services tax.",
            "metadata": {"document_id": "XYZ", "type": "Tax Advisory"}
        }
    ]
}

@app.post("/search")
def search_nth_database(search_query: SearchQuery):
    query_text = search_query.query.lower()
    for key, value in mock_db.items():
        if key in query_text:
            return {"status": "success", "results": value}
    return {"status": "not_found", "results": []}

if __name__ == "__main__":
    print("Starting NTH Placeholder API server on http://127.0.0.1:8002")
    uvicorn.run(app, host="127.0.0.1", port=8002)
