from neo4j import GraphDatabase, Driver
from neo4j.exceptions import SessionExpired
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

class Neo4jClient:
    """
    A lightweight Neo4j client that creates a short-lived driver/session.
    Designed for per-request use in web apps to avoid stale or expired connections.
    """

    def __init__(self):
        load_dotenv()
        self._uri = os.getenv("NEO4J_URI")
        self._username = os.getenv("NEO4J_USERNAME")
        self._password = os.getenv("NEO4J_PASSWORD")

        if not self._uri or not self._username or not self._password:
            raise ValueError("Missing Neo4j connection environment variables (URI/USERNAME/PASSWORD).")

        self._driver: Optional[Driver] = None

        try:
            self._driver = GraphDatabase.driver(self._uri, auth=(self._username, self._password))
            self._driver.verify_connectivity()
            logger.info("✅ Neo4j Driver initialized and connected successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Neo4j at {self._uri}: {e}", exc_info=True)
            self._driver = None
            raise ConnectionError(f"Could not connect to Neo4j database. Error: {e}")

    # --- Context manager support ---
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    # --- Query methods ---
    def run_cypher(self, cypher_query: str, parameters: Optional[Dict] = None) -> List[Dict]:
        """Executes a Cypher query and returns results as list of dicts."""
        if not self._driver:
            raise ConnectionError("Neo4j driver is not connected. Cannot run query.")

        results_list = []
        try:
            with self._driver.session() as session:
                result = session.run(cypher_query, parameters or {})
                for record in result:
                    row_dict = {}
                    for key, value in record.items():
                        # Convert Node/Relationship objects to plain dicts
                        if hasattr(value, "properties"):
                            obj = dict(value.properties)
                            if hasattr(value, "labels"):
                                obj["labels"] = list(value.labels)
                            if hasattr(value, "element_id"):
                                obj["id"] = value.element_id
                            if hasattr(value, "type"):
                                obj["type"] = value.type
                            row_dict[key] = obj
                        else:
                            row_dict[key] = value
                    results_list.append(row_dict)
        except SessionExpired:
            logger.warning("⚠️ Neo4j session expired. Connection will be refreshed.")
            self.reconnect()
            return self.run_cypher(cypher_query, parameters)
        except Exception as e:
            logger.error(f"Error executing Cypher query '{cypher_query}': {e}", exc_info=True)
            raise RuntimeError(f"Failed to execute Cypher query: {e}")
        return results_list

    def reconnect(self):
        """Reinitialize the driver if connection has expired."""
        logger.info("🔄 Reconnecting Neo4j driver...")
        self.close()
        # ✅ Corrected line below
        self.__init__()  # reinitialize properly

    def close(self):
        """Closes the Neo4j driver connection."""
        if self._driver:
            self._driver.close()
            self._driver = None
            logger.info("🧹 Neo4j Driver connection closed.")

    def test_connection(self) -> int:
        """Tests the connection to Neo4j and returns node count."""
        if not self._driver:
            raise ConnectionError("Neo4j driver is not connected. Cannot test connection.")
        with self._driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) AS count")
            return result.single()["count"]

    def get_all_labels(self):
        """Return a list of all node labels in the database."""
        with self._driver.session() as session:
            result = session.run("CALL db.labels()")
            labels = [record["label"] for record in result]
            logger.info(f"📚 Existing labels in Neo4j: {labels}")
            return labels

# --- Standalone test block ---
if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
	try:
		with Neo4jClient() as client:
			count = client.test_connection()
			print(f"Connected successfully. Node count: {count}")
	except Exception as e:
		print(f"Connection failed: {e}")
