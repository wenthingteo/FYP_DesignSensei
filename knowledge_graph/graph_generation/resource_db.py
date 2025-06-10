# resource_db.py
import sqlite3
import json
from typing import List, Dict, Optional

class ResourceDB:
    def __init__(self, db_path: str = "knowledge_graph/graph_generation/resources.db"):
        self.conn = sqlite3.connect(db_path)
        self._create_tables()
    
    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT UNIQUE NOT NULL,
            file_type TEXT NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processing_status TEXT DEFAULT 'pending',
            metadata JSON,
            last_processed TIMESTAMP
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resource_id INTEGER REFERENCES resources(id),
            chunk_id TEXT NOT NULL,
            content TEXT,
            domains JSON,
            UNIQUE(resource_id, chunk_id)
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS graph_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resources_hash TEXT NOT NULL,
            cypher_script TEXT NOT NULL
        )
        """)
        self.conn.commit()

    def add_resource(self, file_name: str, file_type: str, metadata: dict = None):
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT INTO resources (file_name, file_type, metadata) 
        VALUES (?, ?, ?)
        ON CONFLICT(file_name) DO UPDATE SET
            file_type = excluded.file_type,
            metadata = excluded.metadata,
            processing_status = 'pending'
        """, (file_name, file_type, json.dumps(metadata) if metadata else None))
        self.conn.commit()
        return cursor.lastrowid

    def update_processing_status(self, resource_id: int, status: str):
        cursor = self.conn.cursor()
        cursor.execute("""
        UPDATE resources 
        SET processing_status = ?, last_processed = CURRENT_TIMESTAMP
        WHERE id = ?
        """, (status, resource_id))
        self.conn.commit()

    def save_chunks(self, resource_id: int, chunks: List[Dict]):
        cursor = self.conn.cursor()
        for chunk in chunks:
            cursor.execute("""
            INSERT INTO chunks (resource_id, chunk_id, content, domains)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(resource_id, chunk_id) DO UPDATE SET
                content = excluded.content,
                domains = excluded.domains
            """, (
                resource_id,
                chunk.get('chunk_id', ''),
                chunk.get('text', ''),
                json.dumps(chunk.get('domains', []))
            ))
        self.conn.commit()

    def get_pending_resources(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT id, file_name, file_type, metadata 
        FROM resources 
        WHERE processing_status = 'pending'
        """)
        return [
            {
                'id': row[0],
                'file_name': row[1],
                'file_type': row[2],
                'metadata': json.loads(row[3]) if row[3] else {}
            }
            for row in cursor.fetchall()
        ]

    def get_chunks_for_resource(self, resource_id: int) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT chunk_id, content, domains 
        FROM chunks 
        WHERE resource_id = ?
        """, (resource_id,))
        return [
            {
                'chunk_id': row[0],
                'text': row[1],
                'domains': json.loads(row[2]) if row[2] else []
            }
            for row in cursor.fetchall()
        ]
    
    def save_graph_version(self, resources_hash: str, cypher_script: str):
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT INTO graph_versions (resources_hash, cypher_script)
        VALUES (?, ?)
        """, (resources_hash, cypher_script))
        self.conn.commit()