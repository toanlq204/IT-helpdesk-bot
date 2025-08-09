# routers/chroma_router.py
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from db.chroma_config import get_collection
from openai import OpenAI
import os

router = APIRouter()
openai_client = OpenAI(api_key=os.getenv("AZOPENAI_API_KEY"))

class AddDocumentRequest(BaseModel):
    id: Optional[str]
    text: str
    metadata: Optional[dict] = None

@router.post("/chroma/add")
async def add_document(req: AddDocumentRequest):
    """Add a document to ChromaDB"""
    collection = get_collection()
    # Create embeddings
    embedding = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=req.text
    ).data[0].embedding

    doc_id = req.id or f"doc_{collection.count() + 1}"
    collection.add(
        ids=[doc_id],
        documents=[req.text],
        embeddings=[embedding],
        metadatas=[req.metadata or {}]
    )
    return {"message": "Document added", "id": doc_id}

@router.get("/chroma/search")
async def search_documents(query: str, top_k: int = 3):
    """Semantic search on ChromaDB collection"""
    collection = get_collection()
    embedding = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    ).data[0].embedding

    results = collection.query(
        query_embeddings=[embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )
    return results
