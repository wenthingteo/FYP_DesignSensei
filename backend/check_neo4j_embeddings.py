"""
Quick diagnostic script to check Neo4j graph embeddings
Run this to verify if your graph nodes have embeddings populated
"""
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
import django
django.setup()

from knowledge_graph.connection.neo4j_client import Neo4jClient

def check_embeddings():
    print("=" * 60)
    print("🔍 NEO4J EMBEDDING DIAGNOSTIC")
    print("=" * 60)
    
    client = Neo4jClient()
    
    # Check 1: Count nodes with embeddings
    query1 = """
    MATCH (n)
    WHERE n.embedding IS NOT NULL
    RETURN count(n) AS nodes_with_embeddings
    """
    
    result1 = client.run_cypher(query1)
    nodes_with_emb = result1[0]['nodes_with_embeddings'] if result1 else 0
    print(f"\n✅ Nodes WITH embeddings: {nodes_with_emb}")
    
    # Check 2: Count nodes without embeddings
    query2 = """
    MATCH (n)
    WHERE n.embedding IS NULL
    RETURN count(n) AS nodes_without_embeddings
    """
    
    result2 = client.run_cypher(query2)
    nodes_without_emb = result2[0]['nodes_without_embeddings'] if result2 else 0
    print(f"❌ Nodes WITHOUT embeddings: {nodes_without_emb}")
    
    # Check 3: Sample nodes with embeddings
    query3 = """
    MATCH (n)
    WHERE n.embedding IS NOT NULL
    RETURN labels(n) AS labels, n.name AS name, size(n.embedding) AS embedding_size
    LIMIT 5
    """
    
    result3 = client.run_cypher(query3)
    if result3:
        print(f"\n📊 Sample nodes with embeddings:")
        for record in result3:
            print(f"  - {record['labels']}: {record['name']} (dim: {record['embedding_size']})")
    
    # Check 4: Sample nodes without embeddings
    query4 = """
    MATCH (n)
    WHERE n.embedding IS NULL
    RETURN labels(n) AS labels, n.name AS name
    LIMIT 5
    """
    
    result4 = client.run_cypher(query4)
    if result4:
        print(f"\n⚠️  Sample nodes WITHOUT embeddings:")
        for record in result4:
            print(f"  - {record['labels']}: {record['name']}")
    
    # Check 5: DDD-specific nodes
    query5 = """
    MATCH (n)
    WHERE any(label IN labels(n) WHERE label IN ['DDD', 'DDDConcept', 'DDDconcept'])
    RETURN 
        count(n) AS total_ddd_nodes,
        sum(CASE WHEN n.embedding IS NOT NULL THEN 1 ELSE 0 END) AS ddd_with_embeddings
    """
    
    result5 = client.run_cypher(query5)
    if result5:
        record = result5[0]
        total = record['total_ddd_nodes']
        with_emb = record['ddd_with_embeddings']
        print(f"\n🎯 DDD Nodes: {with_emb}/{total} have embeddings ({(with_emb/total*100) if total > 0 else 0:.1f}%)")
    
    # Summary
    print("\n" + "=" * 60)
    total_nodes = nodes_with_emb + nodes_without_emb
    if nodes_without_emb > 0:
        print("⚠️  ACTION REQUIRED:")
        print("   Run embedding generation script:")
        print("   python backend/knowledge_graph/graph_generation/add_embeddings_to_existing_graph.py")
    else:
        print("✅ All nodes have embeddings - graph search should work!")
    print("=" * 60)
    
    client.close()

if __name__ == "__main__":
    try:
        check_embeddings()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("1. Neo4j is running")
        print("2. .env file has correct NEO4J credentials")
        print("3. You're in the backend directory")
