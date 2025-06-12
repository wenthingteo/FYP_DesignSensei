from django.test import TestCase
from rest_framework.test import APIClient
from search.graph_search import GraphSearch
from knowledge_graph.connection.neo4j_client import Neo4jClient
from search_module.embedding_service import get_embedding
from search_module.searchAPIView import SearchAPIView
import numpy as np

class SearchTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.neo4j_client = Neo4jClient()
        self.graph_search = GraphSearch(self.neo4j_client)
        self.view = SearchAPIView()

    def test_get_embedding(self):
        embedding = get_embedding("test query")
        self.assertEqual(len(embedding), 384)
        self.assertIsInstance(embedding, list)

    def test_keyword_search(self):
        results = self.graph_search.search_by_keyword("singleton", ["DesignPattern"])
        self.assertIsInstance(results, list)
        if results:
            self.assertIn("labels", results[0])
            self.assertIn("DesignPattern", results[0]["labels"])

    def test_embedding_search(self):
        embedding = np.zeros(384)
        results = self.graph_search.search_by_embedding(embedding, ["DesignPattern"])
        self.assertIsInstance(results, list)

    def test_process_query_nlp(self):
        tokens = self.view._process_query_nlp("Singleton design pattern")
        self.assertIn("singleton", tokens)
        self.assertIn("design", tokens)
        self.assertIn("pattern", tokens)

    def test_api_endpoint(self):
        response = self.client.post('/api/search/', {
            "user_query": "singleton pattern",
            "session_id": "test_session"
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn("results", response.data)
        self.assertIsInstance(response.data["results"], list)

    def test_ambiguity_handling(self):
        params = [{"match_text": "design", "node_label": ["DesignPattern", "Principle", "Architecture"], "confidence": 0.6}]
        resolved = self.view._handle_ambiguity(params)
        self.assertTrue(resolved[0]["needs_clarification"])
        self.assertIn("clarification_prompt", resolved[0])

    def tearDown(self):
        self.neo4j_client.close()