class Neo4jClient:
    def __init__(self, driver):
        self.driver = driver

    def run_query(self, query, parameters=None):
        if self.driver is None:
            raise ConnectionError("Neo4j driver is not initialized.")
        with self.driver.session() as session:
            return session.run(query, parameters or {}).data()


class GraphSearch:
    def __init__(self, neo4j_client: Neo4jClient):
        self.neo4j_client = neo4j_client

    def search_design_patterns_by_keyword(self, keyword: str):
        cypher_query = """
        MATCH (p:DesignPattern)
        WHERE toLower(p.name) CONTAINS toLower($keyword) OR toLower(p.description) CONTAINS toLower($keyword)
        RETURN p.name AS name, p.description AS description, p.category AS category
        LIMIT 5
        """
        parameters = {"keyword": keyword}
        return self.neo4j_client.run_query(cypher_query, parameters)

    def get_related_concepts(self, concept_name: str):
        cypher_query = """
        MATCH (c {name: $concept_name})-[r]-(related)
        RETURN related.name AS related_name, type(r) AS relationship_type, labels(related) AS related_labels
        LIMIT 10
        """
        parameters = {"concept_name": concept_name}
        return self.neo4j_client.run_query(cypher_query, parameters)
