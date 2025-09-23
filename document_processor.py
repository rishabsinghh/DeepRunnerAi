"""
Document Processing and Ingestion Module for CLM Automation System.
Handles document loading, chunking, and indexing with ChromaDB.
"""
import os
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import re

# Try to import required libraries
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("Warning: ChromaDB not available. Using mock vector database.")

try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.schema import Document
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("Warning: LangChain not available. Using basic text splitting.")

from config import Config
from loguru import logger

class DocumentProcessor:
    """
    Handles document ingestion, processing, and indexing for the CLM system.
    Uses ChromaDB for vector storage and LangChain for text processing.
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.documents_dir = config.DOCUMENTS_DIRECTORY
        self.chunk_size = config.CHUNK_SIZE
        self.chunk_overlap = config.CHUNK_OVERLAP
        
        # Initialize text splitter
        if LANGCHAIN_AVAILABLE:
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
        else:
            self.text_splitter = None
        
        # Initialize vector database
        self.vector_db = self._initialize_vector_db()
        
        # Document registry for tracking
        self.document_registry = {}
        
        logger.info("DocumentProcessor initialized successfully")

    def _initialize_vector_db(self):
        """Initialize ChromaDB vector database"""
        if not CHROMADB_AVAILABLE:
            logger.warning("ChromaDB not available, using mock database")
            return MockVectorDB()
        
        try:
            # Create persistent directory if it doesn't exist
            os.makedirs(self.config.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
            
            # Initialize ChromaDB client
            client = chromadb.PersistentClient(
                path=self.config.CHROMA_PERSIST_DIRECTORY,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Get or create collection
            collection = client.get_or_create_collection(
                name="contract_documents",
                metadata={"description": "Contract lifecycle management documents"}
            )
            
            logger.info(f"ChromaDB initialized with collection: {collection.name}")
            return collection
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            return MockVectorDB()

    def load_documents(self) -> List[Dict[str, Any]]:
        """
        Load all documents from the documents directory.
        Returns a list of document dictionaries with content and metadata.
        """
        documents = []
        
        # Walk through all subdirectories
        for root, dirs, files in os.walk(self.documents_dir):
            for file in files:
                if file.endswith(('.txt', '.docx', '.pdf')) and not file.endswith('_metadata.json'):
                    file_path = os.path.join(root, file)
                    doc = self._load_single_document(file_path)
                    if doc:
                        documents.append(doc)
                        self.document_registry[doc['id']] = doc
        
        logger.info(f"Loaded {len(documents)} documents")
        return documents

    def _load_single_document(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Load a single document and its metadata"""
        try:
            # Generate document ID
            doc_id = self._generate_doc_id(file_path)
            
            # Load content
            content = self._extract_text(file_path)
            if not content:
                logger.warning(f"No content extracted from {file_path}")
                return None
            
            # Load metadata
            metadata = self._load_metadata(file_path)
            
            # Extract additional metadata from content
            extracted_metadata = self._extract_metadata_from_content(content)
            metadata.update(extracted_metadata)
            
            # Add file information
            metadata.update({
                'file_path': file_path,
                'file_name': os.path.basename(file_path),
                'file_type': os.path.splitext(file_path)[1][1:],
                'directory': os.path.basename(os.path.dirname(file_path)),
                'file_size': os.path.getsize(file_path),
                'last_modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                'doc_id': doc_id
            })
            
            return {
                'id': doc_id,
                'content': content,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Error loading document {file_path}: {e}")
            return None

    def _extract_text(self, file_path: str) -> str:
        """Extract text content from various file formats"""
        try:
            if file_path.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            elif file_path.endswith('.docx'):
                # For now, read as text since we created them as text files
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            elif file_path.endswith('.pdf'):
                # For now, read as text since we created them as text files
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            else:
                logger.warning(f"Unsupported file format: {file_path}")
                return ""
                
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            return ""

    def _load_metadata(self, file_path: str) -> Dict[str, Any]:
        """Load metadata from JSON file if it exists"""
        metadata_path = file_path.replace('.txt', '_metadata.json').replace('.docx', '_metadata.json')
        
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error loading metadata from {metadata_path}: {e}")
        
        return {}

    def _extract_metadata_from_content(self, content: str) -> Dict[str, Any]:
        """Extract metadata from document content"""
        metadata = {}
        
        # Extract contract ID
        contract_id_match = re.search(r'Contract ID:\s*([A-Z0-9-]+)', content, re.IGNORECASE)
        if contract_id_match:
            metadata['contract_id'] = contract_id_match.group(1)
        
        # Extract dates
        date_patterns = [
            r'Effective Date:\s*([A-Za-z0-9\s,]+)',
            r'Expiration Date:\s*([A-Za-z0-9\s,]+)',
            r'Start Date:\s*([A-Za-z0-9\s,]+)',
            r'End Date:\s*([A-Za-z0-9\s,]+)'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                key = pattern.split(':')[0].strip().lower().replace(' ', '_')
                metadata[key] = match.group(1).strip()
        
        # Extract company names
        company_patterns = [
            r'Client:\s*([^\n]+)',
            r'Company:\s*([^\n]+)',
            r'Vendor:\s*([^\n]+)',
            r'Service Provider:\s*([^\n]+)'
        ]
        
        companies = []
        for pattern in company_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                companies.append(match.group(1).strip())
        
        if companies:
            metadata['companies'] = companies
        
        # Extract contract type
        type_patterns = [
            r'Service Agreement',
            r'Software License',
            r'Consulting Contract',
            r'Non-Disclosure Agreement',
            r'Employment Contract',
            r'Vendor Agreement'
        ]
        
        for pattern in type_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                metadata['contract_type'] = pattern
                break
        
        # Extract monetary values
        money_pattern = r'\$[\d,]+(?:\.\d{2})?'
        money_matches = re.findall(money_pattern, content)
        if money_matches:
            metadata['monetary_values'] = money_matches
        
        return metadata

    def _generate_doc_id(self, file_path: str) -> str:
        """Generate a unique document ID"""
        # Use file path and modification time to create a unique ID
        stat = os.stat(file_path)
        unique_string = f"{file_path}_{stat.st_mtime}_{stat.st_size}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:16]

    def chunk_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Split documents into chunks for vector indexing"""
        all_chunks = []
        
        for doc in documents:
            if self.text_splitter and LANGCHAIN_AVAILABLE:
                # Use LangChain text splitter
                chunks = self.text_splitter.split_text(doc['content'])
            else:
                # Simple chunking fallback
                chunks = self._simple_chunk_text(doc['content'])
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc['id']}_chunk_{i}"
                chunk_doc = {
                    'id': chunk_id,
                    'content': chunk,
                    'metadata': {
                        **doc['metadata'],
                        'chunk_index': i,
                        'total_chunks': len(chunks),
                        'parent_doc_id': doc['id']
                    }
                }
                all_chunks.append(chunk_doc)
        
        logger.info(f"Created {len(all_chunks)} chunks from {len(documents)} documents")
        return all_chunks

    def _simple_chunk_text(self, text: str) -> List[str]:
        """Simple text chunking fallback"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = ' '.join(chunk_words)
            if chunk_text.strip():
                chunks.append(chunk_text)
        
        return chunks

    def index_documents(self, chunks: List[Dict[str, Any]]) -> bool:
        """Index document chunks in the vector database"""
        try:
            if not chunks:
                logger.warning("No chunks to index")
                return False
            
            # Prepare data for indexing
            ids = [chunk['id'] for chunk in chunks]
            documents = [chunk['content'] for chunk in chunks]
            
            # Convert metadata values to strings (ChromaDB requirement)
            metadatas = []
            for chunk in chunks:
                metadata = {}
                for key, value in chunk['metadata'].items():
                    if isinstance(value, list):
                        metadata[key] = ', '.join(str(v) for v in value)
                    else:
                        metadata[key] = str(value) if value is not None else ""
                metadatas.append(metadata)
            
            # Add to vector database
            if hasattr(self.vector_db, 'add'):
                # ChromaDB
                self.vector_db.add(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )
            else:
                # Mock database
                self.vector_db.add_documents(ids, documents, metadatas)
            
            logger.info(f"Successfully indexed {len(chunks)} chunks")
            return True
            
        except Exception as e:
            logger.error(f"Error indexing documents: {e}")
            return False

    def search_documents(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant document chunks"""
        try:
            if hasattr(self.vector_db, 'query'):
                # ChromaDB
                results = self.vector_db.query(
                    query_texts=[query],
                    n_results=n_results
                )
                
                # Format results
                formatted_results = []
                for i in range(len(results['ids'][0])):
                    formatted_results.append({
                        'id': results['ids'][0][i],
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if 'distances' in results else 0.0
                    })
                
                return formatted_results
            else:
                # Mock database
                return self.vector_db.search(query, n_results)
                
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []

    def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific document by ID"""
        return self.document_registry.get(doc_id)

    def get_similar_documents(self, doc_id: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Find documents similar to a given document"""
        doc = self.get_document_by_id(doc_id)
        if not doc:
            return []
        
        # Use the document content as query
        return self.search_documents(doc['content'], n_results)

    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Get all documents in the registry"""
        return list(self.document_registry.values())

    def process_all_documents(self) -> bool:
        """Complete pipeline: load, chunk, and index all documents"""
        try:
            logger.info("Starting document processing pipeline...")
            
            # Load documents
            documents = self.load_documents()
            if not documents:
                logger.error("No documents found to process")
                return False
            
            # Chunk documents
            chunks = self.chunk_documents(documents)
            if not chunks:
                logger.error("No chunks created from documents")
                return False
            
            # Index chunks
            success = self.index_documents(chunks)
            if not success:
                logger.error("Failed to index documents")
                return False
            
            logger.info("Document processing pipeline completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error in document processing pipeline: {e}")
            return False


class MockVectorDB:
    """Mock vector database for when ChromaDB is not available"""
    
    def __init__(self):
        self.documents = {}
        self.embeddings = {}
        logger.info("Using mock vector database")
    
    def add(self, ids, documents, metadatas):
        """Add documents to mock database"""
        for i, doc_id in enumerate(ids):
            self.documents[doc_id] = {
                'content': documents[i],
                'metadata': metadatas[i]
            }
            # Simple mock embedding (just use document length as "embedding")
            self.embeddings[doc_id] = [len(documents[i])]
    
    def query(self, query_texts, n_results):
        """Mock query - returns documents based on simple text matching"""
        query = query_texts[0].lower()
        results = []
        
        for doc_id, doc in self.documents.items():
            content = doc['content'].lower()
            # Simple similarity based on word overlap
            query_words = set(query.split())
            content_words = set(content.split())
            similarity = len(query_words.intersection(content_words)) / len(query_words) if query_words else 0
            
            if similarity > 0:
                results.append({
                    'id': doc_id,
                    'content': doc['content'],
                    'metadata': doc['metadata'],
                    'similarity': similarity
                })
        
        # Sort by similarity and return top results
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return {
            'ids': [[r['id'] for r in results[:n_results]]],
            'documents': [[r['content'] for r in results[:n_results]]],
            'metadatas': [[r['metadata'] for r in results[:n_results]]],
            'distances': [[1 - r['similarity'] for r in results[:n_results]]]
        }
    
    def add_documents(self, ids, documents, metadatas):
        """Add documents (for compatibility)"""
        self.add(ids, documents, metadatas)
    
    def search(self, query, n_results):
        """Search documents (for compatibility)"""
        result = self.query([query], n_results)
        return [
            {
                'id': result['ids'][0][i],
                'content': result['documents'][0][i],
                'metadata': result['metadatas'][0][i],
                'distance': result['distances'][0][i]
            }
            for i in range(len(result['ids'][0]))
        ]


if __name__ == "__main__":
    # Test the document processor
    from config import Config
    
    config = Config()
    processor = DocumentProcessor(config)
    
    # Process all documents
    success = processor.process_all_documents()
    
    if success:
        print("Document processing completed successfully!")
        
        # Test search
        results = processor.search_documents("contract expiration", n_results=3)
        print(f"\nSearch results for 'contract expiration':")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['metadata'].get('file_name', 'Unknown')} (similarity: {1-result['distance']:.3f})")
            print(f"   {result['content'][:100]}...")
            print()
    else:
        print("Document processing failed!")
