# IMPORTANT: Load environment variables at the very beginning of your application
from dotenv import load_dotenv
load_dotenv() # This makes NEO4J_URI, etc., available to os.getenv()

from knowledge_graph.connection.neo4j_client import Neo4jClient
from search_module.graph_search import GraphSearch

def main():
    neo4j_client = None # Initialize to None for finally block
    try:
        print("Connecting to Neo4j...")
        neo4j_client = Neo4jClient()
        node_count = neo4j_client.test_connection()
        print(f"Successfully connected! Total nodes in graph: {node_count}")

        graph_search = GraphSearch(neo4j_client)

        # --- Example Usage of Search Module ---
        search_term = "singleton"
        print(f"\nSearching for design patterns related to '{search_term}'...")
        patterns = graph_search.search_design_patterns_by_keyword(search_term)
        if patterns:
            print(f"Found {len(patterns)} patterns:")
            for p in patterns:
                print(f"- {p['name']} ({p['category']}): {p['description'][:70]}...")
        else:
            print("No patterns found.")
            
        related_concept = "Factory Method"
        print(f"\nGetting concepts related to '{related_concept}'...")
        related_items = graph_search.get_related_concepts(related_concept)
        if related_items:
            print(f"Found {len(related_items)} related items:")
            for item in related_items:
                print(f"- {item['related_name']} ({item['relationship_type']}, {item['related_labels']})")
        else:
            print("No related concepts found.")


    except Exception as e:
        print(f"An error occurred during application execution: {e}")
    finally:
        if neo4j_client:
            print("Closing Neo4j connection.")
            neo4j_client.close()

if _name_ == "_main_":
    main()