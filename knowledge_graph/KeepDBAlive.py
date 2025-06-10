import os
from neo4j import GraphDatabase, basic_auth
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_keep_alive_query():
    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    database_name = "Instance01" 

    if not all([uri, username, password]):
        logging.error("Neo4j credentials (URI, Username, Password) are not set as environment variables.")
        logging.error("Please set NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD.")
        return

    logging.info(f"Attempting to connect to Neo4j AuraDB: {uri}")

    try:
        driver = GraphDatabase.driver(uri, auth=basic_auth(username, password))
        driver.verify_connectivity()
        logging.info("Neo4j driver connectivity verified.")

        with driver.session(database=database_name) as session:
            # This is a very simple write query.
            # It will MERGE a node called 'Heartbeat' and update its 'lastUpdated' timestamp.
            # This counts as a write operation and will reset the 72-hour inactivity timer.
            timestamp = datetime.utcnow().isoformat() + "Z"
            query = """
            MERGE (h:Heartbeat {id: "aura_keep_alive"})
            SET h.lastUpdated = $timestamp, h.status = 'active'
            RETURN h
            """
            result = session.run(query, timestamp=timestamp)
            logging.info(f"Keep-alive query executed successfully. Result: {result.single()}")

    except Exception as e:
        logging.error(f"Failed to execute keep-alive query: {e}")
    finally:
        if 'driver' in locals() and driver:
            driver.close()
            logging.info("Neo4j driver closed.")

if __name__ == "__main__":
    run_keep_alive_query()