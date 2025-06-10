from neo4j import GraphDatabase
import csv

class Neo4jImporter:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def clear_database(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
    
    def import_from_csv(self, nodes_file, relationships_file):
        # Import nodes
        with open(nodes_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            nodes = list(reader)
        
        with self.driver.session() as session:
            for node in nodes:
                session.run(
                    f"MERGE (:{node['label']} {{name: $name}})",
                    name=node['name']
                )
        
        # Import relationships
        with open(relationships_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            relationships = list(reader)
        
        with self.driver.session() as session:
            for rel in relationships:
                session.run(
                    f"""
                    MATCH (source {{name: $source}})
                    MATCH (target {{name: $target}})
                    MERGE (source)-[:{rel['relationship_type']}]->(target)
                    """,
                    source=rel['source'],
                    target=rel['target']
                )

# Usage
importer = Neo4jImporter("neo4j+s://025d7462.databases.neo4j.io", "neo4j", "D26smsX1j8nNNlAsf5jKANwlfcm0K94vh6dFY2o9dj0")
importer.clear_database()
importer.import_from_csv(
    "./knowledge_graph/graph_generation/versionKG/VER3knowledge_graph_semantically_enhanced_nodes.csv",
    "./knowledge_graph/graph_generation/versionKG/VER3knowledge_graph_semantically_enhanced_relationships.csv"
)