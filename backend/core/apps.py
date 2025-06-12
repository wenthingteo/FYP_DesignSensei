from django.apps import AppConfig
from knowledge_graph.connection.neo4j_client import Neo4jClient
from search_module.graph_search_service import GraphSearchService


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

neo4j_client = Neo4jClient()
graph_search = GraphSearchService(neo4j_client)