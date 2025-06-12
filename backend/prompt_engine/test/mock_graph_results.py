# backend/prompt_engine/test/mock_graph_results.py
"""
Mock GraphRAG search results for testing prompt templates
"""

class MockGraphResult:
    def __init__(self, content, source, relevance_score, node_type):
        self.content = content
        self.source = source
        self.relevance_score = relevance_score
        self.node_type = node_type

# Mock search results for different software design topics
MOCK_SEARCH_RESULTS = {
    'results': [
        {
            'node_id': 'n_12345',
            'name': 'Singleton Pattern',
            'label': 'DesignPattern',
            'description': 'Ensures a class has only one instance and provides a global point of access to it.',
            'source': 'DesignPatterns_GangOfFour.pdf',
            'page': 127,
            'relevance_score': 0.95,
            'relationships': [
                {'related_node': 'Creational Patterns', 'relationship_type': 'PART_OF'}
            ]
        },
        {
            'node_id': 'n_67890',
            'name': 'Dependency Inversion Principle',
            'label': 'SOLIDPrinciple',
            'description': 'High-level modules should not depend on low-level modules. Both should depend on abstractions.',
            'source': 'SOLID_Principles_Guide.pdf',
            'page': 30,
            'relevance_score': 0.88,
            'relationships': [
                {'related_node': 'Coupling', 'relationship_type': 'REDUCES'}
            ]
        }
    ],
    'query_info': {
        'keywords': ['singleton', 'design pattern'],
        'entities': ['Singleton Pattern']
    }
}

def get_mock_search_results(search_key: str):
    """
    Returns mock search results based on a key.
    For the current testing setup, it returns the main MOCK_SEARCH_RESULTS.
    You can extend this function to return different mock data sets
    based on the 'search_key' argument if your tests require specific
    mock data for different queries (e.g., 'mvc_pattern' returning MVC-specific mock data).
    """
    # For now, we'll return the general MOCK_SEARCH_RESULTS dictionary.
    # If you have specific mock data for 'mvc_pattern', you could add a condition here:
    # if search_key == "mvc_pattern":
    #     return {'results': [...MVC specific results...]}
    # else:
    #     return MOCK_SEARCH_RESULTS
    print(f"DEBUG: get_mock_search_results called with key: {search_key}. Returning MOCK_SEARCH_RESULTS.")
    return MOCK_SEARCH_RESULTS