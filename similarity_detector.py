"""
Document Similarity Detection Module for CLM Automation System.
Implements semantic similarity search and document comparison features.
"""
import os
import json
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import re

from config import Config
from document_processor import DocumentProcessor
from loguru import logger

class DocumentSimilarityDetector:
    """
    Advanced document similarity detection and analysis.
    Uses multiple similarity metrics and clustering techniques.
    """
    
    def __init__(self, config: Config, document_processor: DocumentProcessor):
        self.config = config
        self.document_processor = document_processor
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.document_vectors = None
        self.document_texts = []
        self.document_metadata = []
        
        logger.info("Document Similarity Detector initialized successfully")

    def build_similarity_index(self) -> bool:
        """Build the similarity index for all documents"""
        try:
            logger.info("Building document similarity index...")
            
            # Get all documents
            all_docs = self.document_processor.get_all_documents()
            if not all_docs:
                logger.error("No documents found for similarity indexing")
                return False
            
            # Prepare texts and metadata
            self.document_texts = []
            self.document_metadata = []
            
            for doc in all_docs:
                # Clean and prepare text
                clean_text = self._clean_text(doc['content'])
                self.document_texts.append(clean_text)
                self.document_metadata.append(doc['metadata'])
            
            # Create TF-IDF vectors
            self.document_vectors = self.vectorizer.fit_transform(self.document_texts)
            
            logger.info(f"Similarity index built for {len(all_docs)} documents")
            return True
            
        except Exception as e:
            logger.error(f"Error building similarity index: {e}")
            return False

    def _clean_text(self, text: str) -> str:
        """Clean and preprocess text for similarity analysis"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,;:!?-]', '', text)
        
        # Convert to lowercase
        text = text.lower()
        
        return text.strip()

    def find_similar_documents(self, doc_id: str, n_results: int = 5, 
                             similarity_threshold: float = 0.3) -> List[Dict[str, Any]]:
        """
        Find documents similar to a given document.
        
        Args:
            doc_id: ID of the reference document
            n_results: Maximum number of similar documents to return
            similarity_threshold: Minimum similarity score threshold
            
        Returns:
            List of similar documents with similarity scores
        """
        try:
            if self.document_vectors is None:
                logger.warning("Similarity index not built, building now...")
                if not self.build_similarity_index():
                    return []
            
            # Find the document index
            doc_index = self._find_document_index(doc_id)
            if doc_index is None:
                logger.error(f"Document {doc_id} not found")
                return []
            
            # Calculate similarities
            similarities = self._calculate_similarities(doc_index)
            
            # Get top similar documents
            similar_docs = []
            for i, similarity in enumerate(similarities):
                if i != doc_index and similarity >= similarity_threshold:
                    similar_docs.append({
                        'document_id': self.document_metadata[i].get('doc_id', f'doc_{i}'),
                        'file_name': self.document_metadata[i].get('file_name', 'Unknown'),
                        'contract_type': self.document_metadata[i].get('contract_type', 'Unknown'),
                        'companies': self.document_metadata[i].get('companies', []),
                        'similarity_score': float(similarity),
                        'content_preview': self.document_texts[i][:200] + "...",
                        'metadata': self.document_metadata[i]
                    })
            
            # Sort by similarity score (descending)
            similar_docs.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            return similar_docs[:n_results]
            
        except Exception as e:
            logger.error(f"Error finding similar documents: {e}")
            return []

    def _find_document_index(self, doc_id: str) -> Optional[int]:
        """Find the index of a document in the similarity index"""
        for i, metadata in enumerate(self.document_metadata):
            if metadata.get('doc_id') == doc_id:
                return i
        return None

    def _calculate_similarities(self, doc_index: int) -> np.ndarray:
        """Calculate cosine similarities for a document"""
        if self.document_vectors is None:
            return np.array([])
        
        # Get the document vector
        doc_vector = self.document_vectors[doc_index]
        
        # Calculate cosine similarities with all documents
        similarities = cosine_similarity(doc_vector, self.document_vectors).flatten()
        
        return similarities

    def search_by_content(self, query: str, n_results: int = 5, 
                         similarity_threshold: float = 0.1) -> List[Dict[str, Any]]:
        """
        Search for documents by content similarity.
        
        Args:
            query: Search query
            n_results: Maximum number of results to return
            similarity_threshold: Minimum similarity score threshold
            
        Returns:
            List of matching documents with similarity scores
        """
        try:
            if self.document_vectors is None:
                logger.warning("Similarity index not built, building now...")
                if not self.build_similarity_index():
                    return []
            
            # Vectorize the query
            query_vector = self.vectorizer.transform([self._clean_text(query)])
            
            # Calculate similarities
            similarities = cosine_similarity(query_vector, self.document_vectors).flatten()
            
            # Get matching documents
            matching_docs = []
            for i, similarity in enumerate(similarities):
                if similarity >= similarity_threshold:
                    matching_docs.append({
                        'document_id': self.document_metadata[i].get('doc_id', f'doc_{i}'),
                        'file_name': self.document_metadata[i].get('file_name', 'Unknown'),
                        'contract_type': self.document_metadata[i].get('contract_type', 'Unknown'),
                        'companies': self.document_metadata[i].get('companies', []),
                        'similarity_score': float(similarity),
                        'content_preview': self.document_texts[i][:200] + "...",
                        'metadata': self.document_metadata[i]
                    })
            
            # Sort by similarity score (descending)
            matching_docs.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            return matching_docs[:n_results]
            
        except Exception as e:
            logger.error(f"Error searching by content: {e}")
            return []

    def find_duplicate_documents(self, similarity_threshold: float = 0.9) -> List[List[Dict[str, Any]]]:
        """
        Find potential duplicate documents.
        
        Args:
            similarity_threshold: Minimum similarity score to consider as duplicate
            
        Returns:
            List of document groups that are potential duplicates
        """
        try:
            if self.document_vectors is None:
                logger.warning("Similarity index not built, building now...")
                if not self.build_similarity_index():
                    return []
            
            # Calculate similarity matrix
            similarity_matrix = cosine_similarity(self.document_vectors)
            
            # Find duplicate groups
            duplicate_groups = []
            processed = set()
            
            for i in range(len(similarity_matrix)):
                if i in processed:
                    continue
                
                # Find documents similar to document i
                similar_indices = []
                for j in range(i + 1, len(similarity_matrix)):
                    if similarity_matrix[i][j] >= similarity_threshold:
                        similar_indices.append(j)
                
                if similar_indices:
                    # Create group with document i and similar documents
                    group = [{
                        'document_id': self.document_metadata[i].get('doc_id', f'doc_{i}'),
                        'file_name': self.document_metadata[i].get('file_name', 'Unknown'),
                        'similarity_score': 1.0
                    }]
                    
                    for j in similar_indices:
                        group.append({
                            'document_id': self.document_metadata[j].get('doc_id', f'doc_{j}'),
                            'file_name': self.document_metadata[j].get('file_name', 'Unknown'),
                            'similarity_score': float(similarity_matrix[i][j])
                        })
                        processed.add(j)
                    
                    duplicate_groups.append(group)
                
                processed.add(i)
            
            logger.info(f"Found {len(duplicate_groups)} potential duplicate groups")
            return duplicate_groups
            
        except Exception as e:
            logger.error(f"Error finding duplicate documents: {e}")
            return []

    def cluster_documents(self, n_clusters: int = 5) -> Dict[int, List[Dict[str, Any]]]:
        """
        Cluster documents based on content similarity.
        
        Args:
            n_clusters: Number of clusters to create
            
        Returns:
            Dictionary mapping cluster IDs to lists of documents
        """
        try:
            if self.document_vectors is None:
                logger.warning("Similarity index not built, building now...")
                if not self.build_similarity_index():
                    return {}
            
            # Perform K-means clustering
            kmeans = KMeans(n_clusters=min(n_clusters, len(self.document_vectors)), 
                           random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(self.document_vectors)
            
            # Group documents by cluster
            clusters = {}
            for i, label in enumerate(cluster_labels):
                if label not in clusters:
                    clusters[label] = []
                
                clusters[label].append({
                    'document_id': self.document_metadata[i].get('doc_id', f'doc_{i}'),
                    'file_name': self.document_metadata[i].get('file_name', 'Unknown'),
                    'contract_type': self.document_metadata[i].get('contract_type', 'Unknown'),
                    'companies': self.document_metadata[i].get('companies', []),
                    'metadata': self.document_metadata[i]
                })
            
            logger.info(f"Clustered {len(self.document_metadata)} documents into {len(clusters)} clusters")
            return clusters
            
        except Exception as e:
            logger.error(f"Error clustering documents: {e}")
            return {}

    def analyze_contract_versions(self, contract_base_name: str) -> List[Dict[str, Any]]:
        """
        Analyze different versions of the same contract.
        
        Args:
            contract_base_name: Base name of the contract (e.g., "service_agreement")
            
        Returns:
            List of contract versions with similarity analysis
        """
        try:
            # Find documents with similar names
            matching_docs = []
            for i, metadata in enumerate(self.document_metadata):
                file_name = metadata.get('file_name', '').lower()
                if contract_base_name.lower() in file_name:
                    matching_docs.append({
                        'index': i,
                        'document_id': metadata.get('doc_id', f'doc_{i}'),
                        'file_name': metadata.get('file_name', 'Unknown'),
                        'metadata': metadata
                    })
            
            if len(matching_docs) < 2:
                logger.info(f"Found only {len(matching_docs)} documents matching '{contract_base_name}'")
                return []
            
            # Calculate pairwise similarities
            versions = []
            for i, doc1 in enumerate(matching_docs):
                version_info = {
                    'file_name': doc1['file_name'],
                    'document_id': doc1['document_id'],
                    'similarities': {},
                    'metadata': doc1['metadata']
                }
                
                for j, doc2 in enumerate(matching_docs):
                    if i != j:
                        if self.document_vectors is not None:
                            similarity = cosine_similarity(
                                self.document_vectors[doc1['index']:doc1['index']+1],
                                self.document_vectors[doc2['index']:doc2['index']+1]
                            )[0][0]
                            version_info['similarities'][doc2['file_name']] = float(similarity)
                
                versions.append(version_info)
            
            # Sort by file name to get chronological order
            versions.sort(key=lambda x: x['file_name'])
            
            logger.info(f"Analyzed {len(versions)} versions of '{contract_base_name}'")
            return versions
            
        except Exception as e:
            logger.error(f"Error analyzing contract versions: {e}")
            return []

    def get_similarity_statistics(self) -> Dict[str, Any]:
        """Get statistics about document similarities"""
        try:
            if self.document_vectors is None:
                return {"error": "Similarity index not built"}
            
            # Calculate pairwise similarities
            similarity_matrix = cosine_similarity(self.document_vectors)
            
            # Get upper triangle (excluding diagonal)
            upper_triangle = similarity_matrix[np.triu_indices_from(similarity_matrix, k=1)]
            
            stats = {
                'total_documents': len(self.document_metadata),
                'average_similarity': float(np.mean(upper_triangle)),
                'max_similarity': float(np.max(upper_triangle)),
                'min_similarity': float(np.min(upper_triangle)),
                'std_similarity': float(np.std(upper_triangle)),
                'high_similarity_count': int(np.sum(upper_triangle > 0.8)),
                'medium_similarity_count': int(np.sum((upper_triangle > 0.5) & (upper_triangle <= 0.8))),
                'low_similarity_count': int(np.sum(upper_triangle <= 0.5))
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating similarity statistics: {e}")
            return {"error": str(e)}

    def export_similarity_matrix(self, output_file: str) -> bool:
        """Export the similarity matrix to a file"""
        try:
            if self.document_vectors is None:
                logger.error("Similarity index not built")
                return False
            
            # Calculate similarity matrix
            similarity_matrix = cosine_similarity(self.document_vectors)
            
            # Prepare data for export
            data = {
                'document_names': [meta.get('file_name', f'doc_{i}') for i, meta in enumerate(self.document_metadata)],
                'similarity_matrix': similarity_matrix.tolist(),
                'export_date': datetime.now().isoformat()
            }
            
            # Save to file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Similarity matrix exported to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting similarity matrix: {e}")
            return False


if __name__ == "__main__":
    # Test the similarity detector
    from config import Config
    from document_processor import DocumentProcessor
    
    config = Config()
    processor = DocumentProcessor(config)
    
    # Process documents first
    processor.process_all_documents()
    
    # Initialize similarity detector
    detector = DocumentSimilarityDetector(config, processor)
    
    # Build similarity index
    if detector.build_similarity_index():
        print("Similarity index built successfully!")
        
        # Test similarity search
        all_docs = processor.get_all_documents()
        if all_docs:
            test_doc_id = all_docs[0]['id']
            similar_docs = detector.find_similar_documents(test_doc_id, n_results=3)
            
            print(f"\nSimilar documents to {all_docs[0]['metadata'].get('file_name', 'Unknown')}:")
            for doc in similar_docs:
                print(f"  - {doc['file_name']} (similarity: {doc['similarity_score']:.3f})")
        
        # Test content search
        search_results = detector.search_by_content("contract expiration", n_results=3)
        print(f"\nSearch results for 'contract expiration':")
        for doc in search_results:
            print(f"  - {doc['file_name']} (similarity: {doc['similarity_score']:.3f})")
        
        # Get statistics
        stats = detector.get_similarity_statistics()
        print(f"\nSimilarity Statistics:")
        print(f"  - Total documents: {stats['total_documents']}")
        print(f"  - Average similarity: {stats['average_similarity']:.3f}")
        print(f"  - High similarity pairs: {stats['high_similarity_count']}")
    else:
        print("Failed to build similarity index")

