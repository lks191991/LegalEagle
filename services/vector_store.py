import os
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
import uuid

def normalize_name(name):
    # Helper to normalize names for matching
    return name.lower().replace('_', '').replace(' ', '')

def collection_name_from_document(document_name):
    # Helper to create collection name from document name (used for upload and search)
    return document_name.replace(' ', '_').lower()

class VectorStore:
    def __init__(self, document_name=None):
        # Initialize Qdrant client with timeout
        self.client = QdrantClient(
            url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            api_key=os.getenv("QDRANT_API_KEY"),
            timeout=60
        )
        # Create collection name based on document
        if document_name:
            self.collection_name = collection_name_from_document(document_name)
            self.document_name = document_name  # Store original name
            # Only create collection if document name is provided
            self._create_collection_if_not_exists()
        else:
            self.collection_name = None
            self.document_name = None
            
        # Initialize model with proper device handling
        import torch
        torch.set_default_device('cpu')
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.model = self.model.to('cpu')
    
    def _create_collection_if_not_exists(self):
        """Create collection if it doesn't exist"""
        collections = [c.name for c in self.client.get_collections().collections]
        if self.collection_name not in collections:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
            )
    
    def add_documents(self, chunks, filename, tags="", document_date=None, created_date=None, upload_date=None):
        """Add document chunks to document-specific vector store"""
        texts = [chunk["text"] for chunk in chunks]
        embeddings = self.model.encode(texts)
        
        # Process tags
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else []
        
        points = []
        # Ensure dates are always strings
        print(f"DEBUG: add_documents received document_date: '{document_date}', created_date: '{created_date}', upload_date: '{upload_date}'")
        
        # Use the document_date parameter directly, not from chunks
        if not document_date or document_date in ["None", "null", "undefined", ""]:
            final_document_date = "Unknown"
        else:
            final_document_date = str(document_date)
            
        # Use created_date or current date as fallback
        if not created_date or created_date in ["None", "null", "undefined", ""]:
            from datetime import datetime
            final_created_date = datetime.now().strftime("%d-%m-%Y")
        else:
            final_created_date = str(created_date)
            
        # Use upload_date or current date as fallback
        if not upload_date:
            from datetime import datetime
            final_upload_date = datetime.now().strftime("%d-%m-%Y")
        else:
            final_upload_date = str(upload_date)
        
        print(f"DEBUG: Final dates to store - document_date: '{final_document_date}', created_date: '{final_created_date}', upload_date: '{final_upload_date}'")
        
        for i, chunk in enumerate(chunks):
            # Convert UUID to int for point ID
            point_id = int(uuid.uuid4().int & (1<<63)-1)
            payload = {
                "text": chunk["text"],
                "page": chunk.get("page"),
                "filename": filename,
                "document_name": self.document_name,
                "tags": tag_list,
                "document_date": final_document_date,
                "created_date": final_created_date,
                "upload_date": final_upload_date
            }
            print(f"DEBUG: Payload for point {i}: {payload}")
            points.append(models.PointStruct(
                id=point_id,
                vector=embeddings[i].tolist(),
                payload=payload
            ))
        batch_size = 50
        total_points = 0
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            print(f"DEBUG: Upserting batch with payloads: {[p.payload for p in batch]}")
            self.client.upsert(collection_name=self.collection_name, points=batch)
            total_points += len(batch)
        return total_points
    
    def search(self, query, limit=10, document_name=None):
        """Search for a query in the vector store"""
        query_embedding = self.model.encode([query])
        all_results = []
        
        # Determine collections to search
        try:
            collections = self.client.get_collections().collections
            base_name = os.getenv("QDRANT_COLLECTION", "legaleagle_docs")
            
            if document_name:
                # Specific document search
                expected_collection_name = collection_name_from_document(document_name)
                collections_to_search = [expected_collection_name]
                print(f"✅ Only searching selected collection: '{expected_collection_name}'")
            else:
                # No filter, search all document collections except base
                collections_to_search = [c.name for c in collections if c.name != base_name]

            # Search in selected collections
            for collection_name in collections_to_search:
                try:
                    print(f"Searching collection: {collection_name}")
                    results = self.client.search(
                        collection_name=collection_name,
                        query_vector=query_embedding[0].tolist(),
                        limit=limit,
                        with_payload=True
                    )
                    
                    print(f"Found {len(results)} results in {collection_name}")
                    for hit in results:
                        result_data = {
                            "text": hit.payload["text"],
                            "page": hit.payload.get("page"),
                            "filename": hit.payload["filename"],
                            "document_name": hit.payload.get("document_name", hit.payload["document_name"]),  # <-- add this line
                            "score": hit.score
                        }
                        all_results.append(result_data)
                        print(f"Result score {hit.score:.3f}: {hit.payload['text'][:100]}...")
                        
                except Exception as e:
                    print(f"Error searching collection {collection_name}: {e}")
            
            # Sort by score and return top results
            all_results.sort(key=lambda x: x["score"], reverse=True)
            final_results = all_results[:limit]
            print(f"Returning {len(final_results)} final results")
            return final_results
        except Exception as e:
            print(f"Error in search: {e}")
            return []
    
    def get_available_documents(self):
        """Get list of available document collections with actual document names"""
        try:
            collections = self.client.get_collections().collections
            base_name = os.getenv("QDRANT_COLLECTION", "legaleagle_docs")
            
            documents = []
            for collection in collections:
                # Skip the base collection, only include document-specific collections
                if collection.name != base_name:
                    try:
                        # Get first point to extract original document name from payload
                        points = self.client.scroll(
                            collection_name=collection.name,
                            limit=1,
                            with_payload=True
                        )[0]
                        
                        if points:
                            original_doc_name = points[0].payload.get("document_name", collection.name.replace('_', ' ').title())
                            documents.append({
                                "collection_name": collection.name,  # This is the cleaned name like "labor_law"
                                "document_name": original_doc_name   # This is the original name like "Labor Law"
                            })
                        else:
                            # Fallback to collection name
                            documents.append({
                                "collection_name": collection.name,
                                "document_name": collection.name.replace('_', ' ').title()
                            })
                    except Exception as e:
                        print(f"Error processing collection {collection.name}: {e}")
                        continue
            
            return documents[:10]
        except Exception as e:
            print(f"Error in get_available_documents: {e}")
            return []

# In your Flask/FastAPI upload route, make sure you do:
# document_date = request.form.get("document_date")
# vector_store.add_documents(chunks, filename, tags, document_date=document_date)

def get_embedding(text):
    """Get embedding for a single text"""
    import torch
    torch.set_default_device('cpu')
    model = SentenceTransformer('all-MiniLM-L6-v2')
    model = model.to('cpu')
    return model.encode([text])[0].tolist()