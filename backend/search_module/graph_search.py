from knowledge_graph.connection.neo4j_client import Neo4jClient

class GraphSearch:
    def _init_(self, neo4j_client: Neo4jClient):
        self.neo4j_client = neo4j_client

    def search_design_patterns_by_keyword(self, keyword: str):
        """
        Searches for design patterns related to a given keyword in the graph.
        """
        cypher_query = """
        MATCH (p:DesignPattern)
        WHERE toLower(p.name) CONTAINS toLower($keyword) OR toLower(p.description) CONTAINS toLower($keyword)
        RETURN p.name AS name, p.description AS description, p.category AS category
        LIMIT 5
        """
        parameters = {"keyword": keyword}
        
        try:
            results = self.neo4j_client.run_query(cypher_query, parameters)
            return results
        except Exception as e:
            print(f"Error searching for design patterns: {e}")
            return []

    def get_related_concepts(self, concept_name: str):
        """
        Finds concepts related to a given concept (e.g., related patterns, principles, or problems).
        """
        cypher_query = """
        MATCH (c {name: $concept_name})-[r]-(related)
        RETURN related.name AS related_name, type(r) AS relationship_type, labels(related) AS related_labels
        LIMIT 10
        """
        parameters = {"concept_name": concept_name}
        
        try:
            results = self.neo4j_client.run_query(cypher_query, parameters)
            return results
        except Exception as e:
            print(f"Error getting related concepts: {e}")
            return []

    # Add more specific search methods as needed for your chatbot
    # e.g., search_problems_solved_by_pattern, get_pattern_examples, etc.