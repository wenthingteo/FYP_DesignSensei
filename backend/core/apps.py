from django.apps import AppConfig
from knowledge_graph.connection.neo4j_client import Neo4jClient
from search_module.graph_search_service import GraphSearchService
import os
import threading
import logging

# Import the new keep_alive_task
# Make sure core is recognized as a package for this import to work
from . import keep_alive_task 

logger = logging.getLogger(__name__)

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    # Initialize these globally or as class attributes if you need them accessible elsewhere
    # Note: For thread safety and proper Django patterns, dependency injection
    # or request-scoped instances are generally preferred for database clients.
    # For a simplified setup, initializing here works but be mindful in highly concurrent apps.
    neo4j_client = None
    graph_search = None

    def ready(self):
        if os.environ.get('RUN_MAIN') == 'true':
            try:
                CoreConfig.neo4j_client = Neo4jClient()
                logger.info("✅ Neo4j connected successfully")
            except Exception as e:
                logger.warning(f"⚠️ Neo4j connection failed (non-critical): {e}")
                CoreConfig.neo4j_client = None  # Set to None instead of crashing
