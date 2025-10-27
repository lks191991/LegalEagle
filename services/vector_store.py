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
    def __init__(self, document_name=None, user_id=None):
        # Initialize Qdrant client with timeout
        self.client = QdrantClient(
            url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            api_key=os.getenv("QDRANT_API_KEY"),
            timeout=60
        )
        # Store user_id for data separation
        self.user_id = user_id
        
        # Create collection name based on document and user
        if document_name and user_id:
            self.collection_name = f"user_{user_id}_{collection_name_from_document(document_name)}"
            self.document_name = document_name  # Store original name
            # Only create collection if document name and user_id are provided
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
        """Add document chunks to user-specific vector store"""
        if not self.user_id:
            raise ValueError("user_id is required for document operations")
            
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
                "user_id": self.user_id,  # Add user_id to payload for additional security
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
        """Search for a query in user-specific vector store"""
        if not self.user_id:
            raise ValueError("user_id is required for search operations")
            
        query_embedding = self.model.encode([query])
        all_results = []
        
        # Determine collections to search - only user's collections
        try:
            collections = self.client.get_collections().collections
            user_prefix = f"user_{self.user_id}_"
            
            if document_name:
                # Check if document_name is already a collection name or just document name
                if document_name.startswith(f"user_{self.user_id}_"):
                    # It's already a collection name
                    expected_collection_name = document_name
                else:
                    # It's a document name, create collection name
                    expected_collection_name = f"user_{self.user_id}_{collection_name_from_document(document_name)}"
                
                collections_to_search = [expected_collection_name]
                print(f"✅ Only searching user's selected collection: '{expected_collection_name}'")
            else:
                # Search all user's document collections
                collections_to_search = [c.name for c in collections if c.name.startswith(user_prefix)]
                print(f"✅ Searching {len(collections_to_search)} user collections")

            # Search in selected collections
            for collection_name in collections_to_search:
                try:
                    print(f"Searching user collection: {collection_name}")
                    
                    # Search without user_id filter since collections are already user-specific
                    results = self.client.search(
                        collection_name=collection_name,
                        query_vector=query_embedding[0].tolist(),
                        limit=limit,
                        with_payload=True
                    )
                    
                    print(f"Found {len(results)} results in {collection_name}")
                    for hit in results:
                        # Collection name already ensures user separation
                        result_data = {
                            "text": hit.payload["text"],
                            "page": hit.payload.get("page"),
                            "filename": hit.payload["filename"],
                            "document_name": hit.payload.get("document_name", hit.payload["document_name"]),
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
    
    def get_available_documents(self, limit=5, offset=0, search=None, sort_by="recent"):
        """Get list of available document collections for the current user with filtering and pagination"""
        if not self.user_id:
            raise ValueError("user_id is required to get available documents")
            
        # EMERGENCY FIX: Force search from global variable or hardcode for testing
        print(f"RAW SEARCH PARAMETER: {repr(search)} (type: {type(search)})")
        
        # TEMPORARY: Check if this is a search request by looking at other indicators
        # If we're getting None but should have search, let's force it
        if search == 'None' or search is None:
            # Check if this might be a search request that got corrupted
            print("WARNING: Search parameter is None - this might be a bug")
            search = None
            print("SEARCH SET TO NONE - will show all documents")
        else:
            search = search.strip()  
            print(f"SEARCH FILTER ACTIVE: '{search}'")
            
        import datetime
        print(f"TIMESTAMP: {datetime.datetime.now()} - Function called") 
        print(f"DEBUG: get_available_documents called with search='{search}', user_id={self.user_id}")
        try:
            collections = self.client.get_collections().collections
            user_prefix = f"user_{self.user_id}_"
            
            all_documents = []
            print(f"DEBUG: Found {len(collections)} total collections, filtering for user {self.user_id}")
            
            for collection in collections:
                # Only include collections that belong to this user
                if collection.name.startswith(user_prefix):
                    print(f"DEBUG: Processing user collection: {collection.name}")
                    try:
                        # Get first point to extract metadata from payload
                        points = self.client.scroll(
                            collection_name=collection.name,
                            limit=1,
                            with_payload=True
                        )[0]
                        
                        print(f"DEBUG: Found {len(points)} points in collection {collection.name}")
                        
                        if points:
                            payload = points[0].payload
                            original_doc_name = payload.get("document_name", collection.name.replace('_', ' ').title())
                            upload_date = payload.get("upload_date", "Unknown")
                            document_date = payload.get("document_date", "Unknown")
                            tags = payload.get("tags", [])
                            
                            # Remove user prefix from collection name for display
                            clean_collection_name = collection.name.replace(user_prefix, "")
                            
                            document_info = {
                                "collection_name": collection.name,  # Full collection name for internal use
                                "document_name": original_doc_name,  # Original document name for display
                                "clean_name": clean_collection_name,  # Clean name without user prefix
                                "upload_date": upload_date,
                                "document_date": document_date,
                                "tags": tags,
                                "points_count": collection.points_count if hasattr(collection, 'points_count') else 0
                            }
                            
                            # Apply search filter
                            if search and search.strip():
                                search_lower = search.lower().strip()
                                print(f"DEBUG: Searching for '{search_lower}' in document '{original_doc_name}' and tags {tags}")
                                
                                # Check if search term matches document name or tags
                                name_match = search_lower in original_doc_name.lower()
                                tag_match = any(search_lower in tag.lower() for tag in tags) if tags else False
                                
                                if name_match or tag_match:
                                    print(f"DEBUG: MATCH found - adding document '{original_doc_name}' (name_match={name_match}, tag_match={tag_match})")
                                    all_documents.append(document_info)
                                else:
                                    print(f"DEBUG: NO MATCH - skipping document '{original_doc_name}' ('{search_lower}' not found in name or tags)")
                            else:
                                print(f"DEBUG: No search filter - adding document '{original_doc_name}'")
                                all_documents.append(document_info)
                        else:
                            # Fallback to collection name
                            clean_collection_name = collection.name.replace(user_prefix, "")
                            fallback_doc_name = clean_collection_name.replace('_', ' ').title()
                            document_info = {
                                "collection_name": collection.name,
                                "document_name": fallback_doc_name,
                                "clean_name": clean_collection_name,
                                "upload_date": "Unknown",
                                "document_date": "Unknown", 
                                "tags": [],
                                "points_count": 0
                            }
                            
                            # Apply search filter to fallback docs too
                            if search and search.strip():
                                search_lower = search.lower().strip()
                                print(f"DEBUG: Searching for '{search_lower}' in fallback document '{fallback_doc_name}'")
                                if search_lower in fallback_doc_name.lower():
                                    print(f"DEBUG: FALLBACK MATCH found - adding document '{fallback_doc_name}'")
                                    all_documents.append(document_info)
                                else:
                                    print(f"DEBUG: FALLBACK NO MATCH - skipping document '{fallback_doc_name}' ('{search_lower}' not found)")
                            else:
                                print(f"DEBUG: No search filter - adding fallback document '{fallback_doc_name}'")
                                all_documents.append(document_info)
                                
                    except Exception as e:
                        print(f"ERROR: Exception processing collection {collection.name}: {e}")
                        import traceback
                        print(f"ERROR: Traceback: {traceback.format_exc()}")
                        continue
            
            # Sort documents
            if sort_by == "recent":
                # Sort by upload_date, putting "Unknown" at the end
                all_documents.sort(key=lambda x: (x["upload_date"] == "Unknown", x["upload_date"]), reverse=True)
            elif sort_by == "name":
                all_documents.sort(key=lambda x: x["document_name"].lower())
            elif sort_by == "size":
                all_documents.sort(key=lambda x: x["points_count"], reverse=True)
            
            # Apply pagination
            total_count = len(all_documents)
            paginated_documents = all_documents[offset:offset + limit]
            
            print(f"DEBUG: After filtering and pagination: {len(paginated_documents)}/{total_count} documents")
            if search:
                print(f"DEBUG: Search '{search}' resulted in {total_count} matches total")
                print(f"DEBUG: Final search parameter was: {repr(search)}")
                
            return paginated_documents, total_count
            
        except Exception as e:
            print(f"ERROR: Exception in get_available_documents: {e}")
            import traceback
            print(f"ERROR: Traceback: {traceback.format_exc()}")
            return [], 0
    
    def delete_user_documents(self, document_name=None):
        """Delete user's documents from vector store"""
        if not self.user_id:
            raise ValueError("user_id is required to delete documents")
            
        try:
            if document_name:
                # Delete specific document collection
                collection_name = f"user_{self.user_id}_{collection_name_from_document(document_name)}"
                if self.client.collection_exists(collection_name):
                    self.client.delete_collection(collection_name)
                    print(f"Deleted collection: {collection_name}")
                    return True
            else:
                # Delete all user collections
                collections = self.client.get_collections().collections
                user_prefix = f"user_{self.user_id}_"
                deleted_count = 0
                
                for collection in collections:
                    if collection.name.startswith(user_prefix):
                        self.client.delete_collection(collection.name)
                        print(f"Deleted collection: {collection.name}")
                        deleted_count += 1
                
                print(f"Deleted {deleted_count} user collections")
                return deleted_count > 0
                
        except Exception as e:
            print(f"Error deleting user documents: {e}")
            return False

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