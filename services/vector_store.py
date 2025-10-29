import os
import uuid
import numpy as np

# Optional imports - handle gracefully if not available
try:
    from qdrant_client import QdrantClient, models
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    print("WARNING: Qdrant not available")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("WARNING: Sentence transformers not available")

class MockSentenceTransformer:
    """Mock sentence transformer for development without Hugging Face"""
    def encode(self, texts):
        """Return mock embeddings"""
        if isinstance(texts, str):
            texts = [texts]
        return np.random.rand(len(texts), 384).astype(np.float32)
    
    def to(self, device):
        """Mock to method"""
        return self

def normalize_name(name):
    # Helper to normalize names for matching
    return name.lower().replace('_', '').replace(' ', '')

def collection_name_from_document(document_name):
    # Helper to create collection name from document name (used for upload and search)
    return document_name.replace(' ', '_').lower()

class VectorStore:
    def __init__(self, document_name=None, user_id=None):
        # Store user_id for data separation  
        self.user_id = user_id
        
        # Create collection name based on document and user
        if document_name and user_id:
            self.collection_name = f"user_{user_id}_{collection_name_from_document(document_name)}"
            self.document_name = document_name  # Store original name
        else:
            self.collection_name = None
            self.document_name = None
        
        # Initialize Qdrant client and model only when needed
        self.client = None
        self.model = None
    
    def _init_client_if_needed(self):
        """Initialize Qdrant client only when needed"""
        if self.client is None:
            if QDRANT_AVAILABLE:
                try:
                    self.client = QdrantClient(
                        url=os.getenv("QDRANT_URL", "http://localhost:6333"),
                        api_key=os.getenv("QDRANT_API_KEY"),
                        timeout=60
                    )
                    print("INFO: Qdrant client initialized successfully")
                except Exception as e:
                    print(f"WARNING: Could not initialize Qdrant client: {e}")
                    self.client = "disabled"  # Mark as disabled instead of None
            else:
                print("WARNING: Qdrant not available, vector operations disabled")
                self.client = "disabled"  # Mark as disabled instead of None
    
    def _init_model_if_needed(self):
        """Initialize sentence transformer model only when needed"""
        if self.model is None:
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                try:
                    import torch
                    torch.set_default_device('cpu')
                    self.model = SentenceTransformer('all-MiniLM-L6-v2')
                    self.model = self.model.to('cpu')
                    print("INFO: Sentence transformer model loaded successfully")
                except Exception as e:
                    print(f"WARNING: Could not load sentence transformer model: {e}")
                    # Fallback to mock model
                    self.model = MockSentenceTransformer()
            else:
                print("WARNING: Using mock sentence transformer model")
                self.model = MockSentenceTransformer()
    
    def _create_collection_if_not_exists(self):
        """Create collection if it doesn't exist"""
        self._init_client_if_needed()
        if self.client == "disabled" or self.client is None:
            print("WARNING: Qdrant client disabled, skipping collection creation")
            return
            
        if self.client and QDRANT_AVAILABLE:
            try:
                collections = [c.name for c in self.client.get_collections().collections]
                if self.collection_name not in collections:
                    self.client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
                    )
                    print(f"INFO: Created collection {self.collection_name}")
                else:
                    print(f"INFO: Collection {self.collection_name} already exists")
            except Exception as e:
                print(f"WARNING: Could not create collection: {e}")
    
    def add_documents(self, chunks, filename, tags="", document_date=None, created_date=None, upload_date=None):
        """Add document chunks to user-specific vector store"""
        if not self.user_id:
            raise ValueError("user_id is required for document operations")
        
        # Initialize client and model
        self._init_client_if_needed()
        self._init_model_if_needed()
        
        # If vector storage is disabled, return minimal success
        if self.client == "disabled" or self.client is None:
            print("WARNING: Vector storage disabled, document uploaded to database only")
            return len(chunks)  # Return number of chunks for compatibility
            
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
        # Create collection if needed
        self._create_collection_if_not_exists()
        
        batch_size = 50
        total_points = 0
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            print(f"DEBUG: Upserting batch with payloads: {[p.payload for p in batch]}")
            
            # Only upsert if client is available
            if self.client != "disabled" and self.client is not None:
                self.client.upsert(collection_name=self.collection_name, points=batch)
            else:
                print("WARNING: Skipping vector upsert as client is disabled")
            total_points += len(batch)
        return total_points
    
    def search(self, query, limit=10, document_name=None):
        """Search for a query in user-specific vector store"""
        if not self.user_id:
            raise ValueError("user_id is required for search operations")
        
        # Initialize client and model
        self._init_client_if_needed()
        self._init_model_if_needed()
        
        # If vector search is disabled, return empty results
        if self.client == "disabled" or self.client is None:
            print("WARNING: Vector search disabled, returning empty results")
            return []
            
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
    
    def search_in_collection(self, query, collection_name, limit=5):
        """Search directly in a specific collection by collection name"""
        try:
            # Initialize client and model
            self._init_client_if_needed()
            self._init_model_if_needed()
            
            # If vector search is disabled, return empty results
            if self.client == "disabled" or self.client is None:
                print("WARNING: Vector search disabled, returning empty results")
                return []
                
            print(f"🔍 Searching in specific collection: {collection_name}")
            
            # Generate query embedding
            query_embedding = self.model.encode([query])
            print(f"Generated embedding for query: {query}")
            
            # Check if collection exists
            collections = [c.name for c in self.client.get_collections().collections]
            if collection_name not in collections:
                print(f"❌ Collection '{collection_name}' does not exist")
                return []
            
            # Search directly in the specified collection
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_embedding[0].tolist(),
                limit=limit,
                with_payload=True
            )
            
            print(f"✅ Found {len(results)} results in collection '{collection_name}'")
            
            search_results = []
            for hit in results:
                result_data = {
                    "text": hit.payload["text"],
                    "page": hit.payload.get("page"),
                    "filename": hit.payload["filename"],
                    "document_name": hit.payload.get("document_name", "Unknown"),
                    "score": hit.score,
                    "collection_name": collection_name
                }
                search_results.append(result_data)
                print(f"Result score {hit.score:.3f}: {hit.payload['text'][:100]}...")
            
            return search_results
            
        except Exception as e:
            print(f"❌ Error searching in collection '{collection_name}': {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
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
            # Initialize client and check if available
            self._init_client_if_needed()
            
            # If client is disabled, return data from database instead
            if self.client == "disabled" or self.client is None:
                print("WARNING: Qdrant client disabled, using database fallback for documents")
                return self._get_documents_from_database(search, limit, offset, sort_by)
            
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
            print("WARNING: Falling back to database for documents")
            return self._get_documents_from_database(search, limit, offset, sort_by)
    
    def _get_documents_from_database(self, search=None, limit=10, offset=0, sort_by="recent"):
        """Fallback method to get documents from database when Qdrant is unavailable"""
        try:
            from db_operations import DatabaseOperations
            
            print(f"DEBUG: Getting documents from database for user {self.user_id}")
            
            # Get user documents from database
            documents = DatabaseOperations.get_user_documents_for_chat(self.user_id)
            
            if not documents:
                print("DEBUG: No documents found in database")
                return [], 0
            
            # Convert database format to expected format
            all_documents = []
            for doc in documents:
                document_info = {
                    "collection_name": doc.get('collection_name', ''),
                    "document_name": doc.get('filename', doc.get('document_name', 'Unknown')),
                    "clean_name": doc.get('filename', doc.get('document_name', 'Unknown')),
                    "upload_date": doc.get('upload_date', 'Unknown'),
                    "document_date": doc.get('document_date', 'Unknown'),
                    "tags": doc.get('tags', '').split(',') if doc.get('tags') else [],
                    "points_count": doc.get('chunk_count', 0)
                }
                
                # Apply search filter if provided
                if search and search.strip() and search != "None":
                    search_lower = search.lower()
                    doc_name_lower = document_info["document_name"].lower()
                    
                    if search_lower not in doc_name_lower:
                        continue  # Skip this document if it doesn't match search
                
                all_documents.append(document_info)
            
            # Apply sorting
            if sort_by == "recent":
                all_documents.sort(key=lambda x: x.get("upload_date", ""), reverse=True)
            elif sort_by == "alphabetical":
                all_documents.sort(key=lambda x: x.get("document_name", "").lower())
            
            # Apply pagination
            total_count = len(all_documents)
            paginated_docs = all_documents[offset:offset + limit]
            
            print(f"DEBUG: Database fallback returned {len(paginated_docs)} documents (total: {total_count})")
            return paginated_docs, total_count
            
        except Exception as e:
            print(f"ERROR: Database fallback failed: {e}")
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