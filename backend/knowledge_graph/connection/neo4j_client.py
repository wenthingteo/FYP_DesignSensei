# knowledge_graph/connection/neo4j_client.py
from neo4j import GraphDatabase, Driver
from typing import Dict, List, Optional, Any
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

class Neo4jClient:
    # --- FIX: Changed _init_ to __init__ (double underscores) ---
    def __init__(self):
        self._driver: Optional[Driver] = None 

        load_dotenv()
        self._uri = os.getenv("NEO4J_URI")
        self._username = os.getenv("NEO4J_USERNAME")
        self._password = os.getenv("NEO4J_PASSWORD")

        if not self._uri:
            logger.error("NEO4J_URI environment variable is not set.")
            raise ValueError("NEO4J_URI environment variable is required.")
        if not self._username:
            logger.error("NEO4J_USERNAME environment variable is not set.")
            raise ValueError("NEO4J_USERNAME environment variable is required.")
        if not self._password:
            logger.error("NEO4J_PASSWORD environment variable is not set.")
            raise ValueError("NEO4J_PASSWORD environment variable is required.")

        try:
            self._driver = GraphDatabase.driver(self._uri, auth=(self._username, self._password))
            self._driver.verify_connectivity()
            logger.info("Neo4j Driver initialized and connected successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j at {self._uri}: {e}", exc_info=True)
            self._driver = None 
            raise ConnectionError(f"Could not connect to Neo4j database. Error: {e}")

    def test_connection(self) -> int:
        """Tests the connection to Neo4j and returns the count of nodes."""
        if not self._driver:
            raise ConnectionError("Neo4j driver is not connected. Cannot test connection.")
        
        try:
            with self._driver.session() as session:
                result = session.run("MATCH (n) RETURN count(n) as count")
                return result.single()["count"]
        except Exception as e:
            logger.error(f"Error testing Neo4j connection: {e}", exc_info=True)
            raise RuntimeError(f"Failed to test Neo4j connection: {e}")
    
    def run_cypher(self, cypher_query: str, parameters: Optional[Dict] = None) -> List[Dict]:
        """
        Executes a Cypher query and returns the results as a list of dictionaries.
        Each dictionary represents a row/record, with keys being the returned variable names.
        Neo4j Node/Relationship objects in results are converted to dictionaries.

        Args:
            cypher_query (str): The Cypher query string.
            parameters (Dict, optional): Dictionary of parameters for the query. Defaults to None.
            
        Returns:
            List[Dict]: A list of dictionaries, where each dictionary represents a row/record.
        """
        if not self._driver:
            raise ConnectionError("Neo4j driver is not connected. Cannot run query.")

        results_list = []
        try:
            with self._driver.session() as session:
                result = session.run(cypher_query, parameters or {})
                for record in result:
                    row_dict = {}
                    for key, value in record.items():
                        # Handle Neo4j Node/Relationship objects, converting them to plain dicts
                        if hasattr(value, 'properties') and hasattr(value, 'labels') or hasattr(value, 'type'):
                            obj_dict = dict(value.properties)
                            if hasattr(value, 'labels'):
                                obj_dict['_labels_'] = list(value.labels)
                            if hasattr(value, 'element_id'):
                                obj_dict['_id_'] = value.element_id
                            if hasattr(value, 'type'):
                                obj_dict['_type_'] = value.type
                            row_dict[key] = obj_dict
                        else:
                            row_dict[key] = value
                    results_list.append(row_dict)
        except Exception as e:
            logger.error(f"Error executing Cypher query: '{cypher_query}'. Parameters: {parameters}. Error: {e}", exc_info=True)
            raise RuntimeError(f"Failed to execute Cypher query: {e}")
        return results_list
            
    def close(self):
        """Closes the Neo4j driver connection."""
        if self._driver:
            self._driver.close()
            logger.info("Neo4j Driver connection closed.")

# Test it works (for standalone execution of this file)
if __name__ == "__main__": # Also fixed typo here from "_main_" to "__main__"
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    load_dotenv() 

    client = None
    try:
        client = Neo4jClient()
        node_count = client.test_connection()
        print(f"Total nodes in the graph: {node_count}")
        
        print("\nRunning example query: MATCH (n:DesignPattern) RETURN n.name AS name, n.description AS description LIMIT 2")
        result_nodes = client.run_cypher("MATCH (n:DesignPattern) RETURN n.name AS name, n.description AS description LIMIT 2")
        for node in result_nodes:
            print(f"Node Name: {node.get('name', 'N/A')}, Description: {node.get('description', 'N/A')}")

        print("\nRunning example query to return full node objects:")
        result_full_nodes = client.run_cypher("MATCH (n:DesignPrinciple) RETURN n LIMIT 1")
        for record in result_full_nodes:
            node_data = record.get('n')
            if node_data:
                print(f"Full Node Data: {node_data.get('name', 'N/A')}, Labels: {node_data.get('_labels_', [])}, ID: {node_data.get('_id_', 'N/A')}")
            else:
                print("No node data found in record.")
            
    except ConnectionError as ce:
        print(f"Connection error: {ce}")
        logger.error(f"Connection error in main test block: {ce}", exc_info=True)
    except ValueError as ve:
        print(f"Configuration error: {ve}")
        logger.error(f"Configuration error in main test block: {ve}", exc_info=True)
    except RuntimeError as re:
        print(f"Runtime error during query: {re}")
        logger.error(f"Runtime error in main test block: {re}", exc_info=True)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        logger.critical(f"Unexpected error in main test block: {e}", exc_info=True)
    finally:
        if client:
            client.close()