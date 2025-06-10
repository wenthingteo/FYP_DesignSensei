# knowledge_graph/connection/neo4j_client.py
from neo4j import GraphDatabase
from config.neo4j_config import NEO4J_CONFIG

class Neo4jClient:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            NEO4J_CONFIG["uri"],
            auth=(NEO4J_CONFIG["username"], NEO4J_CONFIG["password"])
        )
    
    def test_connection(self):
        with self.driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) as count")
            return result.single()["count"]
    
    def close(self):
        self.driver.close()

# Test it works
if __name__ == "__main__":
    client = Neo4jClient()
    print(f"Total nodes: {client.test_connection()}")
    client.close()