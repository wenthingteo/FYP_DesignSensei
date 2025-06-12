# knowledge_graph/connection/neo4j_client.py
from neo4j import GraphDatabase
import os

class Neo4jClient:
    def __init__(self):
        uri = os.getenv("NEO4J_URI")
        username = os.getenv("NEO4J_USERNAME")
        password = os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(
            uri,
            auth=(username, password)
        )
    
    def test_connection(self):
        with self.driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) as count")
            return result.single()["count"]
    
    # --- NEW: Generic method to run Cypher queries ---
    def run_query(self, cypher_query, parameters=None):
        """
        Executes a Cypher query and returns the results.
        :param cypher_query: The Cypher query string.
        :param parameters: Dictionary of parameters for the query.
        :return: A list of records from the query result.
        """
        with self.driver.session() as session:
            result = session.run(cypher_query, parameters)
            return [record for record in result] # Convert result cursor to a list
            
    def close(self):
        self.driver.close()

# Test it works
if __name__ == "__main__":
    from dotenv import load_dotenv # Import here for standalone testing
    load_dotenv() # Load env vars for this script when run directly

    client = Neo4jClient()
    try:
        print(f"Total nodes: {client.test_connection()}")
        
        # Example of using run_query
        # result_nodes = client.run_query("MATCH (n) RETURN n.name AS name LIMIT 3")
        # for node in result_nodes:
        #     print(f"Node Name: {node['name']}")
            
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        client.close()