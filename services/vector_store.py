import os
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
import uuid

class VectorStore:
    def __init__(self, document_name=None):
        # Initialize Qdrant client
        self.client = QdrantClient(
            url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        # Create collection name based on document
        base_name = os.getenv("QDRANT_COLLECTION", "legaleagle_docs")
        if document_name:
            # Clean filename for collection name
            clean_name = document_name.replace('.pdf', '').replace('.txt', '').replace(' ', '_').replace('-', '_').lower()
            self.collection_name = f"{base_name}_{clean_name}"
            # Only create collection if document name is provided
            self._create_collection_if_not_exists()
        else:
            self.collection_name = None
            
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def _create_collection_if_not_exists(self):
        """Create collection if it doesn't exist"""
        collections = [c.name for c in self.client.get_collections().collections]
        if self.collection_name not in collections:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
            )
    
    def add_documents(self, chunks, filename):
        """Add document chunks to document-specific vector store"""
        texts = [chunk["text"] for chunk in chunks]
        embeddings = self.model.encode(texts)
        
        points = []
        for i, chunk in enumerate(chunks):
            # Convert UUID to int for point ID
            point_id = int(uuid.uuid4().int & (1<<63)-1)
            points.append(models.PointStruct(
                id=point_id,
                vector=embeddings[i].tolist(),
                payload={
                    "text": chunk["text"],
                    "page": chunk.get("page"),
                    "filename": filename
                }
            ))
        
        self.client.upsert(collection_name=self.collection_name, points=points)
        return len(points)
    
    def search(self, query, limit=3, document_filter=None):
        """Search for similar documents across all collections or specific document"""
        query_embedding = self.model.encode([query])
        all_results = []
        
        # Get all collections
        collections = self.client.get_collections().collections
        base_name = os.getenv("QDRANT_COLLECTION", "legaleagle_docs")
        
        # Filter collections to search - only search document-specific collections
        collections_to_search = []
        for collection in collections:
            # Only search collections that have document names (contain underscore after base name)
            if collection.name.startswith(f"{base_name}_"):
                if document_filter:
                    # Search only in specific document collection
                    clean_filter = document_filter.replace('.pdf', '').replace('.txt', '').replace(' ', '_').replace('-', '_').lower()
                    if clean_filter in collection.name:
                        collections_to_search.append(collection.name)
                else:
                    # Search all document collections
                    collections_to_search.append(collection.name)
        
        # Search in selected collections
        for collection_name in collections_to_search:
            try:
                results = self.client.search(
                    collection_name=collection_name,
                    query_vector=query_embedding[0].tolist(),
                    limit=limit,
                    with_payload=True
                )
                
                for hit in results:
                    all_results.append({
                        "text": hit.payload["text"],
                        "page": hit.payload.get("page"),
                        "filename": hit.payload["filename"],
                        "score": hit.score
                    })
            except Exception as e:
                print(f"Error searching collection {collection_name}: {e}")
        
        # Sort by score and return top results
        all_results.sort(key=lambda x: x["score"], reverse=True)
        return all_results[:limit]

def get_embedding(text):
    """Get embedding for a single text"""
    model = SentenceTransformer('all-MiniLM-L6-v2')
    return model.encode([text])[0].tolist()