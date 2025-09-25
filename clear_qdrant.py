import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

load_dotenv()

# Connect to Qdrant
client = QdrantClient(
    url=os.getenv("QDRANT_URL", "http://localhost:6333"),
    api_key=os.getenv("QDRANT_API_KEY")
)

collection_name = os.getenv("QDRANT_COLLECTION", "legaleagle_docs")

try:
    # Delete the collection
    client.delete_collection(collection_name)
    print(f"✅ Deleted collection: {collection_name}")
    print("Now re-upload your documents to get clean data!")
except Exception as e:
    print(f"Error: {e}")