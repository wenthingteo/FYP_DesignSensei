# core/keep_alive_task.py
import os
import logging
import time
from datetime import datetime, timedelta, timezone 
from neo4j import GraphDatabase, basic_auth
import threading

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def _run_single_keep_alive_query():
    """Executes a single keep-alive query to Neo4j."""
    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    database_name = "neo4j" 

    if not all([uri, username, password]):
        logger.error("Neo4j credentials (URI, Username, Password) are not set as environment variables for keep-alive task.")
        return False

    logger.info(f"Attempting keep-alive connection to Neo4j AuraDB: {uri}")
    driver = None

    try:
        driver = GraphDatabase.driver(uri, auth=basic_auth(username, password))
        driver.verify_connectivity()
        logger.info("Neo4j driver connectivity verified for keep-alive task.")

        with driver.session(database=database_name) as session:
            # Get current UTC time and make it timezone aware
            utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
            
            # Define Malaysia timezone offset (+8 hours)
            malaysia_offset = timedelta(hours=8)
            
            # Apply offset to get Malaysia local time (still timezone-aware)
            malaysia_time = utc_now + malaysia_offset
            
            # Neo4j's DateTime type can handle timezone-aware Python datetime objects directly.
            # No need for .isoformat() here if passing datetime object directly.
            timestamp_for_db = malaysia_time 

            query = """
            MERGE (h:Heartbeat {id: "aura_keep_alive"})
            SET h.lastUpdated = $timestamp, h.status = 'active'
            RETURN h
            """
            # Pass the timezone-aware datetime object directly as a parameter.
            result = session.run(query, timestamp=timestamp_for_db)
            logger.info(f"Keep-alive query executed successfully. Result: {result.single()}")
            return True

    except Exception as e:
        logger.error(f"Failed to execute keep-alive query: {e}", exc_info=True)
        return False
    finally:
        if driver:
            driver.close()
            logger.info("Neo4j driver closed for keep-alive task.")

def start_keep_alive_scheduler():
    """Starts a background thread to run the keep-alive query periodically."""
    interval_hours = int(os.getenv("NEO4J_KEEP_ALIVE_INTERVAL_HOURS", 70))
    interval_seconds = interval_hours * 3600

    # For debugging, you can keep a shorter interval like 5 minutes (300 seconds)
    # interval_seconds = 300 

    def scheduler_loop():
        logger.info(f"Neo4j keep-alive scheduler started. Will run every {interval_hours} hours ({interval_seconds} seconds).")
        _run_single_keep_alive_query() # Run immediately on start
        while True:
            time.sleep(interval_seconds)
            _run_single_keep_alive_query()

    keep_alive_thread = threading.Thread(target=scheduler_loop, daemon=True)
    keep_alive_thread.start()
    logger.info("Neo4j keep-alive background thread initiated.")

if __name__ == "__main__":
    _run_single_keep_alive_query()
