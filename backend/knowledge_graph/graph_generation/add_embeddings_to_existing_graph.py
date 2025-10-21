"""
Script to add embeddings to existing Neo4j nodes
Run this ONCE to migrate your existing graph
"""

from openai import OpenAI
from neo4j import GraphDatabase
import time
from typing import List
import os
from dotenv import load_dotenv


# Load environment variables (supports a .env file if python-dotenv is installed)
try:
    load_dotenv()
except Exception:
    pass

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

missing = [name for name, val in (("NEO4J_PASSWORD", NEO4J_PASSWORD), ("OPENAI_API_KEY", OPENAI_API_KEY)) if not val]
if missing:
    raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}. Set them or add a .env file.")

# Initialize clients
openai_client = OpenAI(api_key=OPENAI_API_KEY)
neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))


def generate_embedding(text: str) -> List[float]:
    """Generate embedding using OpenAI API"""
    try:
        response = openai_client.embeddings.create(
            input=text,
            model="text-embedding-3-small"  # Fast and cost-effective
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None


def get_nodes_without_embeddings(session, batch_size=100, skip=0):
    """Get nodes that don't have embeddings yet"""
    query = """
    MATCH (n)
    WHERE n.embedding IS NULL
    RETURN elementId(n) as node_id, 
           labels(n) as labels,
           coalesce(n.name, '') as name,
           coalesce(n.description, '') as description
    SKIP $skip
    LIMIT $batch_size
    """
    result = session.run(query, skip=skip, batch_size=batch_size)
    return [dict(record) for record in result]


def update_node_embedding(session, node_id: str, embedding: List[float]):
    """Update a specific node with its embedding"""
    query = """
    MATCH (n)
    WHERE elementId(n) = $node_id
    SET n.embedding = $embedding
    """
    session.run(query, node_id=node_id, embedding=embedding)


def count_nodes_without_embeddings(session):
    """Count total nodes without embeddings"""
    query = """
    MATCH (n)
    WHERE n.embedding IS NULL
    RETURN count(n) as count
    """
    result = session.run(query)
    return result.single()["count"]


def add_embeddings_to_graph(batch_size=100):
    """Main function to add embeddings to all nodes"""
    
    with neo4j_driver.session() as session:
        # Get total count
        total_nodes = count_nodes_without_embeddings(session)
        print(f"📊 Total nodes without embeddings: {total_nodes}")
        
        if total_nodes == 0:
            print("✅ All nodes already have embeddings!")
            return
        
        processed = 0
        skip = 0
        errors = 0
        
        while processed < total_nodes:
            # Get batch of nodes
            nodes = get_nodes_without_embeddings(session, batch_size, skip)
            
            if not nodes:
                break
            
            print(f"\n📦 Processing batch: {processed + 1} to {processed + len(nodes)}")
            
            for node in nodes:
                try:
                    # Create text representation of node
                    text_parts = []
                    
                    if node['name']:
                        text_parts.append(f"Name: {node['name']}")
                    
                    if node['description']:
                        text_parts.append(f"Description: {node['description']}")
                    
                    # Add label information
                    if node['labels']:
                        text_parts.append(f"Type: {', '.join(node['labels'])}")
                    
                    text = ". ".join(text_parts)
                    
                    if not text.strip():
                        print(f"⚠️  Skipping node {node['node_id']} - no text content")
                        skip += 1
                        continue
                    
                    # Generate embedding
                    embedding = generate_embedding(text)
                    
                    if embedding:
                        # Update node
                        update_node_embedding(session, node['node_id'], embedding)
                        processed += 1
                        
                        if processed % 50 == 0:
                            print(f"✅ Processed {processed}/{total_nodes} nodes")
                    else:
                        errors += 1
                        print(f"❌ Failed to generate embedding for node {node['node_id']}")
                    
                    # Rate limiting - OpenAI has limits
                    time.sleep(0.1)  # Adjust based on your API tier
                    
                except Exception as e:
                    errors += 1
                    print(f"❌ Error processing node {node['node_id']}: {e}")
            
            skip += batch_size
        
        print(f"\n" + "="*50)
        print(f"✅ Migration Complete!")
        print(f"📊 Successfully processed: {processed} nodes")
        print(f"❌ Errors: {errors} nodes")
        print("="*50)


def verify_embeddings(sample_size=5):
    """Verify that embeddings were added correctly"""
    with neo4j_driver.session() as session:
        query = """
        MATCH (n)
        WHERE n.embedding IS NOT NULL
        RETURN labels(n) as labels, 
               n.name as name,
               size(n.embedding) as embedding_size
        LIMIT $sample_size
        """
        result = session.run(query, sample_size=sample_size)
        
        print("\n🔍 Sample of nodes with embeddings:")
        for record in result:
            print(f"  - {record['name']} ({record['labels']}): {record['embedding_size']} dimensions")


if __name__ == "__main__":
    print("🚀 Starting embedding migration process...")
    print("="*50)
    
    try:
        # Add embeddings
        add_embeddings_to_graph(batch_size=50)  # Adjust batch size as needed
        
        # Verify
        verify_embeddings()
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
    finally:
        neo4j_driver.close()
        print("\n✅ Neo4j connection closed")