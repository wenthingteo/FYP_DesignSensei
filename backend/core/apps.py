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
        """
        This method is called when Django starts up and is ready to serve requests.
        It's the ideal place to perform startup tasks like initializing external clients
        and starting background threads.
        """
        logger.info("CoreConfig ready() method called.")
        
        # Ensure environment variables are loaded
        # (though load_dotenv should ideally be at the very entry point, e.g., wsgi.py or manage.py)
        # from dotenv import load_dotenv
        # load_dotenv() # It's good practice for it to be loaded once at the very start of the application.

        if os.environ.get('RUN_MAIN', None) != 'true':
            # This check prevents running startup code multiple times in Django's development server
            # which often spawns a main process and a reload process.
            logger.info("Skipping duplicate startup logic in CoreConfig.ready().")
            return
        
        try:
            # Initialize Neo4jClient and GraphSearchService once on startup
            # This is where your application's connection to Neo4j is established
            global neo4j_client, graph_search
            if CoreConfig.neo4j_client is None:
                CoreConfig.neo4j_client = Neo4jClient()
                logger.info("Neo4jClient initialized.")
            
            if CoreConfig.graph_search is None:
                CoreConfig.graph_search = GraphSearchService(CoreConfig.neo4j_client)
                logger.info("GraphSearchService initialized.")
            
            # Start the Neo4j keep-alive scheduler in a background thread
            # This prevents your AuraDB instance from shutting down due to inactivity.
            # Only start if not already started (e.g., if Django reloads during development)
            if not hasattr(self, '_keep_alive_started'):
                keep_alive_task.start_keep_alive_scheduler()
                self._keep_alive_started = True # Flag to prevent re-starting the thread
                logger.info("Neo4j keep-alive scheduler started from CoreConfig.")

        except Exception as e:
            logger.error(f"Error during CoreConfig startup: {e}", exc_info=True)

# You can keep these global assignments outside the class as well,
# but if you want them truly managed by the AppConfig lifecycle,
# initializing them in `ready()` and making them class attributes (or global)
# is a common pattern for singletons.
# neo4j_client = Neo4jClient() # Moved to ready() for controlled initialization
# graph_search = GraphSearchService(neo4j_client) # Moved to ready() for controlled initialization