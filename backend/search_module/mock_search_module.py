import re
from typing import Dict, List, Any

# --- Mock Knowledge Graph Data ---
# This dictionary simulates your knowledge graph. In a real system, this would be
# queried from a graph database (e.g., Neo4j, ArangoDB, Amazon Neptune).
# Nodes have 'name', 'label', 'description', 'source', 'page', and 'relationships'.
# Relationships connect nodes and have a 'type' and 'target_node_name'.
MOCK_KNOWLEDGE_GRAPH_DATA = {
    "Singleton Pattern": {
        "node_id": "n_12345",
        "name": "Singleton Pattern",
        "label": "DesignPattern",
        "description": "Ensures a class has only one instance and provides a global point of access to it. Useful for logging, configuration, or managing a single database connection.",
        "source": "DesignPatterns_GangOfFour.pdf",
        "page": 127,
        "relationships": [
            {"type": "PART_OF", "target_node_name": "Creational Patterns"},
            {"type": "RELATED_TO", "target_node_name": "Global State"},
            {"type": "IMPLEMENTS", "target_node_name": "Lazy Initialization"}
        ]
    },
    "Factory Method Pattern": {
        "node_id": "n_12346",
        "name": "Factory Method Pattern",
        "label": "DesignPattern",
        "description": "Defines an interface for creating an object, but lets subclasses alter the type of objects that will be created. Promotes loose coupling.",
        "source": "DesignPatterns_GangOfFour.pdf",
        "page": 107,
        "relationships": [
            {"type": "PART_OF", "target_node_name": "Creational Patterns"},
            {"type": "CONTRASTS_WITH", "target_node_name": "Abstract Factory Pattern"}
        ]
    },
    "Abstract Factory Pattern": {
        "node_id": "n_12347",
        "name": "Abstract Factory Pattern",
        "label": "DesignPattern",
        "description": "Provides an interface for creating families of related or dependent objects without specifying their concrete classes.",
        "source": "DesignPatterns_GangOfFour.pdf",
        "page": 87,
        "relationships": [
            {"type": "PART_OF", "target_node_name": "Creational Patterns"},
            {"type": "CONTRASTS_WITH", "target_node_name": "Factory Method Pattern"}
        ]
    },
    "Observer Pattern": {
        "node_id": "n_12348",
        "name": "Observer Pattern",
        "label": "DesignPattern",
        "description": "Defines a one-to-many dependency between objects so that when one object changes state, all its dependents are notified and updated automatically.",
        "source": "DesignPatterns_GangOfFour.pdf",
        "page": 293,
        "relationships": [
            {"type": "PART_OF", "target_node_name": "Behavioral Patterns"},
            {"type": "USES", "target_node_name": "Loose Coupling"}
        ]
    },
    "Dependency Inversion Principle (DIP)": {
        "node_id": "n_67890",
        "name": "Dependency Inversion Principle",
        "label": "SOLIDPrinciple",
        "description": "High-level modules should not depend on low-level modules. Both should depend on abstractions (interfaces). Promotes flexibility and reusability.",
        "source": "SOLID_Principles_Guide.pdf",
        "page": 30,
        "relationships": [
            {"type": "RELATED_TO", "target_node_name": "Loose Coupling"},
            {"type": "REDUCES", "target_node_name": "Tight Coupling"}
        ]
    },
    "Single Responsibility Principle (SRP)": {
        "node_id": "n_67891",
        "name": "Single Responsibility Principle",
        "label": "SOLIDPrinciple",
        "description": "A class should have only one reason to change, meaning it should have only one responsibility.",
        "source": "SOLID_Principles_Guide.pdf",
        "page": 5,
        "relationships": []
    },
    "Open/Closed Principle (OCP)": {
        "node_id": "n_67892",
        "name": "Open/Closed Principle",
        "label": "SOLIDPrinciple",
        "description": "Software entities (classes, modules, functions, etc.) should be open for extension, but closed for modification.",
        "source": "SOLID_Principles_Guide.pdf",
        "page": 10,
        "relationships": [
            {"type": "IMPLEMENTS", "target_node_name": "Polymorphism"}
        ]
    },
    "MVC Pattern": {
        "node_id": "n_88888",
        "name": "Model-View-Controller (MVC) Pattern",
        "label": "ArchitecturePattern",
        "description": "Separates an application into three main components: the Model (data/business logic), the View (user interface), and the Controller (handles user input).",
        "source": "SoftwareArchitecture_Patterns.pdf",
        "page": 45,
        "relationships": [
            {"type": "CONTRASTS_WITH", "target_node_name": "MVP Pattern"},
            {"type": "USED_IN", "target_node_name": "Web Applications"}
        ]
    },
    "MVP Pattern": {
        "node_id": "n_88889",
        "name": "Model-View-Presenter (MVP) Pattern",
        "label": "ArchitecturePattern",
        "description": "Similar to MVC, but the Presenter mediates between the Model and the View. The View is more passive.",
        "source": "SoftwareArchitecture_Patterns.pdf",
        "page": 55,
        "relationships": [
            {"type": "CONTRASTS_WITH", "target_node_name": "MVC Pattern"},
            {"type": "USED_IN", "target_node_name": "Desktop Applications"}
        ]
    },
    "Creational Patterns": {
        "node_id": "cat_c1",
        "name": "Creational Patterns",
        "label": "DesignPatternCategory",
        "description": "Design patterns that deal with object creation mechanisms, trying to create objects in a manner suitable to the situation.",
        "source": "DesignPatterns_Overview.pdf",
        "page": 5,
        "relationships": []
    },
    "Behavioral Patterns": {
        "node_id": "cat_b1",
        "name": "Behavioral Patterns",
        "label": "DesignPatternCategory",
        "description": "Design patterns that deal with algorithms and the assignment of responsibilities between objects.",
        "source": "DesignPatterns_Overview.pdf",
        "page": 7,
        "relationships": []
    },
    "Loose Coupling": {
        "node_id": "prop_lc",
        "name": "Loose Coupling",
        "label": "DesignProperty",
        "description": "A design goal to reduce the interdependencies between modules.",
        "source": "SoftwareDesign_Fundamentals.pdf",
        "page": 20,
        "relationships": []
    },
    "Tight Coupling": {
        "node_id": "prop_tc",
        "name": "Tight Coupling",
        "label": "DesignProperty",
        "description": "High interdependencies between modules, making changes difficult.",
        "source": "SoftwareDesign_Fundamentals.pdf",
        "page": 21,
        "relationships": []
    },
    "Polymorphism": {
        "node_id": "concept_poly",
        "name": "Polymorphism",
        "label": "ProgrammingConcept",
        "description": "The ability of an object to take on many forms. Most common use is when a parent class reference is used to refer to a child class object.",
        "source": "OOP_Concepts.pdf",
        "page": 15,
        "relationships": []
    },
    "Lazy Initialization": {
        "node_id": "concept_lazy",
        "name": "Lazy Initialization",
        "label": "ProgrammingConcept",
        "description": "A technique to defer the creation of an object until it is needed.",
        "source": "Performance_Optimizations.pdf",
        "page": 30,
        "relationships": []
    },
    "Global State": {
        "node_id": "concept_global",
        "name": "Global State",
        "label": "ProgrammingConcept",
        "description": "Data that is accessible and modifiable from anywhere in a program, often leading to hard-to-track bugs.",
        "source": "SoftwareDesign_Pitfalls.pdf",
        "page": 10,
        "relationships": []
    }
}


class MockSearchModule:
    """
    A mock search module that simulates knowledge graph traversal and semantic
    matching for testing the prompt engineering module.
    """

    def __init__(self, knowledge_graph_data: Dict[str, Dict]):
        self.knowledge_graph = knowledge_graph_data

    def _normalize_query(self, query: str) -> str:
        """Simple normalization: lowercase and remove non-alphanumeric."""
        return re.sub(r'[^a-zA-Z0-9\s]', '', query).lower()

    def _get_relevance_score(self, query_tokens: List[str], text: str) -> float:
        """Calculates a simple keyword-based relevance score."""
        if not text:
            return 0.0
        normalized_text = self._normalize_query(text)
        score = sum(1 for token in query_tokens if token in normalized_text)
        return score / len(query_tokens) if query_tokens else 0.0

    def search(self, user_query: str) -> Dict[str, Any]:
        """
        Simulates searching and traversing a knowledge graph based on the user query.
        Returns results in the format expected by GraphRAG (prompt templates).
        """
        normalized_query = self._normalize_query(user_query)
        query_tokens = normalized_query.split()
        
        found_nodes = {}  # Use a dict to avoid duplicate nodes by node_id
        
        # Phase 1: Direct keyword matching on node names and descriptions
        for node_name, node_data in self.knowledge_graph.items():
            name_score = self._get_relevance_score(query_tokens, node_data.get("name", ""))
            desc_score = self._get_relevance_score(query_tokens, node_data.get("description", ""))
            
            # Simple combined score, you could use more sophisticated logic here
            relevance_score = max(name_score, desc_score)
            
            if relevance_score > 0.3:  # Threshold for considering a match
                # Deep copy to ensure modifications don't affect original mock data
                result_node = node_data.copy()
                result_node['relevance_score'] = relevance_score
                
                # Format relationships for the output
                formatted_relationships = []
                for rel in result_node.get('relationships', []):
                    # Only include relationships where the target node exists in our mock graph
                    if rel['target_node_name'] in self.knowledge_graph:
                        formatted_relationships.append({
                            'related_node': rel['target_node_name'],
                            'relationship_type': rel['type']
                        })
                result_node['relationships'] = formatted_relationships
                
                found_nodes[result_node['node_id']] = result_node

        # Phase 2: Simple "traversal" - find related nodes to the directly found ones
        # This is a very basic simulation of graph traversal. In a real graph,
        # you'd perform multi-hop queries.
        initial_found_node_ids = list(found_nodes.keys())
        for node_id in initial_found_node_ids:
            node_data = found_nodes[node_id]
            for relationship in node_data.get('relationships', []):
                target_name = relationship['related_node']
                if target_name in self.knowledge_graph:
                    target_node_data = self.knowledge_graph[target_name]
                    if target_node_data['node_id'] not in found_nodes:
                        # Add related node with a lower relevance score
                        related_node = target_node_data.copy()
                        related_node['relevance_score'] = 0.5 # Example lower score
                        
                        formatted_relationships = []
                        for rel in related_node.get('relationships', []):
                             if rel['target_node_name'] in self.knowledge_graph:
                                formatted_relationships.append({
                                    'related_node': rel['target_node_name'],
                                    'relationship_type': rel['type']
                                })
                        related_node['relationships'] = formatted_relationships

                        found_nodes[related_node['node_id']] = related_node


        # Sort results by relevance score (descending)
        sorted_results = sorted(
            found_nodes.values(), 
            key=lambda x: x.get('relevance_score', 0.0), 
            reverse=True
        )

        return {
            'results': sorted_results,
            'query_info': {
                'keywords': query_tokens,
                'entities': [node['name'] for node in sorted_results], # Simple entity extraction
                'original_query': user_query
            }
        }

# --- Example Usage ---
if __name__ == "__main__":
    search_module = MockSearchModule(MOCK_KNOWLEDGE_GRAPH_DATA)

    print("--- Test Case 1: Explanation Query ---")
    query1 = "What is the Singleton pattern?"
    results1 = search_module.search(query1)
    print(f"Query: '{query1}'")
    for r in results1['results']:
        print(f"  - Node: {r['name']} ({r['label']}), Score: {r['relevance_score']:.2f}")
        if r.get('relationships'):
            print("    Relationships:")
            for rel in r['relationships']:
                print(f"      - {rel['relationship_type']} -> {rel['related_node']}")
    print("\n" + "="*50 + "\n")

    print("--- Test Case 2: Comparison Query ---")
    query2 = "Compare Factory Method and Abstract Factory"
    results2 = search_module.search(query2)
    print(f"Query: '{query2}'")
    for r in results2['results']:
        print(f"  - Node: {r['name']} ({r['label']}), Score: {r['relevance_score']:.2f}")
        if r.get('relationships'):
            print("    Relationships:")
            for rel in r['relationships']:
                print(f"      - {rel['relationship_type']} -> {rel['related_node']}")
    print("\n" + "="*50 + "\n")

    print("--- Test Case 3: Relationship Query ---")
    query3 = "What principles relate to loose coupling?"
    results3 = search_module.search(query3)
    print(f"Query: '{query3}'")
    for r in results3['results']:
        print(f"  - Node: {r['name']} ({r['label']}), Score: {r['relevance_score']:.2f}")
        if r.get('relationships'):
            print("    Relationships:")
            for rel in r['relationships']:
                print(f"      - {rel['relationship_type']} -> {rel['related_node']}")
    print("\n" + "="*50 + "\n")

    print("--- Test Case 4: General Concept Query ---")
    query4 = "Tell me about SOLID principles"
    results4 = search_module.search(query4)
    print(f"Query: '{query4}'")
    for r in results4['results']:
        print(f"  - Node: {r['name']} ({r['label']}), Score: {r['relevance_score']:.2f}")
        if r.get('relationships'):
            print("    Relationships:")
            for rel in r['relationships']:
                print(f"      - {rel['relationship_type']} -> {rel['related_node']}")
    print("\n" + "="*50 + "\n")

    print("--- Integration with PromptManager (Conceptual Example) ---")
    # To integrate this with your PromptManager, you would use it like this:
    # from backend.prompt_engine.managers.prompt_manager import PromptManager
    # # Assuming your PromptManager is set up to take graphrag_results
    # # from mock_search_module import MockSearchModule, MOCK_KNOWLEDGE_GRAPH_DATA
    #
    # prompt_manager_instance = PromptManager(openai_api_key="YOUR_OPENAI_API_KEY")
    # mock_search_module_instance = MockSearchModule(MOCK_KNOWLEDGE_GRAPH_DATA)
    #
    # user_query_for_prompt = "What is the Singleton pattern?"
    # # Simulate the search module providing results
    # search_results_for_prompt = mock_search_module_instance.search(user_query_for_prompt)
    #
    # # Now pass these results to your PromptManager's process_query method
    # # You'll need to adapt the conversation_context and user_expertise as per your PromptManager's method signature.
    # # result = prompt_manager_instance.process_query(
    # #     user_query=user_query_for_prompt,
    # #     graphrag_results=search_results_for_prompt,
    # #     conversation_context={}, # Provide actual context from your ContextManager
    # #     user_expertise="INTERMEDIATE" # Provide actual expertise from your system
    # # )
    # # print("Generated Prompt (from PromptManager, conceptual):")
    # # print(result.get('prompt'))