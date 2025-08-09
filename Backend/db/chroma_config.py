# db/chroma_config.py
import os
from dotenv import load_dotenv
import chromadb

load_dotenv()

CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "helpdesk_kb")


chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIRECTORY)

if CHROMA_COLLECTION_NAME in [c.name for c in chroma_client.list_collections()]:
    collection = chroma_client.get_collection(CHROMA_COLLECTION_NAME)
else:
    collection = chroma_client.create_collection(
        name=CHROMA_COLLECTION_NAME,
        metadata={"description": "IT HelpDesk chatbot knowledge base"}
    )

def get_collection():
    return collection
