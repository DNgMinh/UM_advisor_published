import sqlite3
import json
import numpy as np
from typing import List, Optional, Dict, Any, Set
from langchain_core.documents import Document
from tqdm import tqdm
import os
from datetime import datetime
import cohere  # Import the Cohere client

class SQLiteVectorStore:
    def __init__(self, db_file: str = "vectors.db", table_name: str = "vectors"):
        self.db_file = db_file
        self.table_name = table_name
        self._db_initialized = False
        self.embeddings_model = None
        self.reranker = None  # To store the Cohere reranker client

    def set_reranker(self, api_key: str, model: str = "rerank-english-v2.0"):
        """Initialize the Cohere reranker with the provided API key and model."""
        self.reranker = cohere.Client(api_key=api_key)
        self.reranker_model = model

    def _initialize_db(self):
        """Initialize the SQLite database with source tracking."""
        if self._db_initialized:
            return

        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                metadata TEXT,
                embedding_id INTEGER,
                source_file TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.table_name}_embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vector BLOB NOT NULL
            )
        ''')
        
        # Create sources table to track indexed files
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.table_name}_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_file TEXT UNIQUE,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        self._db_initialized = True

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        a = np.array(a)
        b = np.array(b)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    def L2_distance(self, a: List[float], b: List[float]) -> float:
        """Calculate L2 distance between two vectors."""
        a = np.array(a)
        b = np.array(b)
        return np.linalg.norm(a - b)

    def get_indexed_sources(self) -> List[Dict[str, Any]]:
        """Get list of all indexed source files."""
        self._initialize_db()
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute(f'''
            SELECT s.source_file, s.indexed_at, COUNT(d.id) as document_count
            FROM {self.table_name}_sources s
            LEFT JOIN {self.table_name} d ON s.source_file = d.source_file
            GROUP BY s.source_file, s.indexed_at
        ''')
        
        sources = []
        for row in cursor.fetchall():
            sources.append({
                'source_file': row[0],
                'indexed_at': row[1],
                'document_count': row[2]
            })
            
        conn.close()
        return sources

    def is_file_indexed(self, source_file: str) -> bool:
        """Check if a file has already been indexed."""
        self._initialize_db()
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute(f'''
            SELECT 1 FROM {self.table_name}_sources 
            WHERE source_file = ?
        ''', (source_file,))
        
        result = cursor.fetchone() is not None
        conn.close()
        return result

    def add_documents(self, documents: List[Document], source_file: str, batch_size: int = 32, force_reindex: bool = False) -> None:
        """Add documents to the vector store with source tracking."""
        if not self.embeddings_model:
            raise ValueError("Embeddings model not set")

        self._initialize_db()
        
        # Check if source is already indexed
        if self.is_file_indexed(source_file) and not force_reindex:
            print(f"Source {source_file} is already indexed. Use force_reindex=True to reindex.")
            return
            
        # If force_reindex, remove existing entries for this source
        if force_reindex:
            self.remove_source(source_file)
        
        # Add source to sources table
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute(f'''
            INSERT INTO {self.table_name}_sources (source_file)
            VALUES (?)
        ''', (source_file,))
        conn.commit()
        conn.close()
        
        # Process in batches
        for i in tqdm(range(0, len(documents), batch_size), desc=f"Processing {source_file}"):
            batch = documents[i:i + batch_size]
            
            # Prepare texts and metadata
            texts = [doc.page_content for doc in batch]
            metadatas = [doc.metadata for doc in batch]
            
            # Generate embeddings
            embeddings = self.embeddings_model.embed_documents(texts)
            
            # Store in database
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            for text, metadata, embedding in zip(texts, metadatas, embeddings):
                # Store embedding
                cursor.execute(
                    f'INSERT INTO {self.table_name}_embeddings (vector) VALUES (?)',
                    (json.dumps(embedding),)
                )
                embedding_id = cursor.lastrowid
                
                # Update metadata with source information
                if metadata is None:
                    metadata = {}
                metadata['source_file'] = source_file
                
                # Store document
                cursor.execute(
                    f'INSERT INTO {self.table_name} (content, metadata, embedding_id, source_file) VALUES (?, ?, ?, ?)',
                    (text, json.dumps(metadata), embedding_id, source_file)     # convert metadata dictionary into json to store
                )
            
            conn.commit()
            conn.close()

    def remove_source(self, source_file: str) -> None:
        """Remove all documents from a specific source."""
        self._initialize_db()
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Get embedding IDs to remove
        cursor.execute(f'''
            SELECT embedding_id FROM {self.table_name}
            WHERE source_file = ?
        ''', (source_file,))
        embedding_ids = [row[0] for row in cursor.fetchall()]
        
        # Remove documents
        cursor.execute(f'''
            DELETE FROM {self.table_name}
            WHERE source_file = ?
        ''', (source_file,))
        
        # Remove embeddings
        if embedding_ids:
            placeholder = ','.join('?' * len(embedding_ids))
            cursor.execute(f'''
                DELETE FROM {self.table_name}_embeddings
                WHERE id IN ({placeholder})
            ''', embedding_ids)
        
        # Remove from sources
        cursor.execute(f'''
            DELETE FROM {self.table_name}_sources
            WHERE source_file = ?
        ''', (source_file,))
        
        conn.commit()
        conn.close()

    def similarity_search(self, query: str, count: int = 0, k: int = 4, source_filter: Optional[List[str]] = None, rerank: bool = False, rerank_top_k: int = 20) -> List[Document]:
        """
        Search for similar documents, optionally filtering by source and reranking with Cohere.
        
        Args:
            query: The query string to search for
            count: Offset for pagination
            k: Number of results to return
            source_filter: Optional list of source files to filter by
            rerank: Whether to apply Cohere reranking
            rerank_top_k: Number of top results to consider for reranking (if rerank is True)
        
        Returns:
            List of Document objects sorted by relevance
        """
        if not self.embeddings_model:
            raise ValueError("Embeddings model not set")

        # Generate query embedding
        query_embedding = self.embeddings_model.embed_query(query)
        
        # Search in database
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Build query based on source filter
        if source_filter:
            placeholder = ','.join('?' * len(source_filter))
            cursor.execute(f'''
                SELECT d.content, d.metadata, e.vector, d.source_file
                FROM {self.table_name} d 
                JOIN {self.table_name}_embeddings e ON d.embedding_id = e.id
                WHERE d.source_file IN ({placeholder})
            ''', source_filter)
        else:
            cursor.execute(f'''
                SELECT d.content, d.metadata, e.vector, d.source_file
                FROM {self.table_name} d 
                JOIN {self.table_name}_embeddings e ON d.embedding_id = e.id
            ''')
        
        results = cursor.fetchall()
        
        # Calculate similarities
        similarities = []
        for content, metadata_str, vector_str, source_file in results:
            vector = json.loads(vector_str)

            similarity = self._cosine_similarity(query_embedding, vector)
            # similarity = self.L2_distance(query_embedding, vector)

            # load back metadata into dictionary
            metadata = json.loads(metadata_str) if metadata_str else {}
            metadata['similarity_score'] = round(similarity, 4)
            metadata['source_file'] = source_file
            similarities.append((similarity, content, metadata))
        
        # Sort by similarity (cosine) and get top k
        similarities.sort(key=lambda x: x[0], reverse=True)

        # If reranking is enabled, use Cohere to rerank the top results
        if rerank:
            if not self.reranker:
                raise ValueError("Reranker not set. Call set_reranker() with your Cohere API key first.")
            
            # Get the top candidates for reranking (more than k to give reranker enough options)
            top_candidates = similarities[:rerank_top_k]
            
            if top_candidates:
                # Extract documents for reranking
                documents_to_rerank = [content for _, content, _ in top_candidates]
                
                # Call Cohere reranking API
                try:
                    rerank_results = self.reranker.rerank(
                        model=self.reranker_model,
                        query=query,
                        documents=documents_to_rerank,
                        top_n=k
                    )
                    
                    # Create new reranked list
                    reranked_results = []
                    for result in rerank_results.results:
                        # Find the original metadata for this document
                        original_idx = result.index
                        _, content, metadata = top_candidates[original_idx]
                        
                        # Update with new relevance score
                        metadata['rerank_score'] = round(result.relevance_score, 4)
                        reranked_results.append((result.relevance_score, content, metadata))
                    
                    # Replace similarities with reranked results
                    top_k = reranked_results
                except Exception as e:
                    print(f"Reranking failed: {e}. Falling back to vector search.")
                    # Fallback to vector search if reranking fails
                    top_k = top_candidates[:k]
            else:
                top_k = []
        else:
            # No reranking, just get the top k from vector similarity search
            top_k = similarities[k*count:k*count+k]
        
        # Convert to Documents
        documents = []
        for _, content, metadata in top_k:
            documents.append(Document(
                page_content=content,
                metadata=metadata
            ))
        
        conn.close()
        return documents


    def drop_tables(self):
        """Drop all tables and reinitialize the database."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Drop existing tables
        cursor.execute(f'DROP TABLE IF EXISTS {self.table_name}')
        cursor.execute(f'DROP TABLE IF EXISTS {self.table_name}_embeddings')
        cursor.execute(f'DROP TABLE IF EXISTS {self.table_name}_sources')
        
        conn.commit()
        conn.close()
        
        # Reset initialization flag
        self._db_initialized = False
        
        # Reinitialize the database
        self._initialize_db()

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        stats = {}
        
        # Get document count per source
        cursor.execute(f'''
            SELECT source_file, COUNT(*) 
            FROM {self.table_name}
            GROUP BY source_file
        ''')
        stats['documents_per_source'] = dict(cursor.fetchall())
        
        # Get total document count
        stats['total_documents'] = sum(stats['documents_per_source'].values())
        
        # Get total size per source
        cursor.execute(f'''
            SELECT source_file, SUM(LENGTH(content)) 
            FROM {self.table_name}
            GROUP BY source_file
        ''')
        stats['size_per_source'] = dict(cursor.fetchall())
        
        # Get date ranges
        cursor.execute(f'''
            SELECT source_file, MIN(created_at), MAX(created_at)
            FROM {self.table_name}
            GROUP BY source_file
        ''')
        stats['date_ranges'] = {row[0]: {'first': row[1], 'last': row[2]} 
                              for row in cursor.fetchall()}
        
        conn.close()
        return stats