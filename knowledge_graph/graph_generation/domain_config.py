# domain_config.py

DOMAIN_FOCUS = {
    # These are abstract categories you want your KG to focus on.
    # They align directly with the keys in 'node_types' and 'keywords'.
    'topics': [
        'design_patterns',
        'solid_principles',
        'architecture',
        'ddd',
        'quality',
        'code_structure'
    ],

    # Node labels used in the Neo4j Cypher output and classification.
    'node_types': {
        'design_patterns': 'DesignPattern',
        'solid_principles': 'DesignPrinciple',
        'architecture': 'ArchPattern',
        'ddd': 'DDDConcept',
        'quality': 'QualityAttribute',
        'code_structure': 'CodeStructure'
    },

    # Expanded keyword mapping used to classify content chunks or entity labels.
    # These are used for semantic detection, classification, and filtering.
    'keywords': {
        'design_patterns': [
            'observer', 'factory', 'singleton', 'strategy', 'composite', 'adapter',
            'decorator', 'command', 'template method', 'proxy', 'builder',
            'state', 'mediator', 'memento', 'bridge', 'flyweight', 'interpreter',
            'chain of responsibility'
        ],

        'solid_principles': [
            'single responsibility', 'open closed', 'liskov',
            'interface segregation', 'dependency inversion',
            'srp', 'ocp', 'lsp', 'isp', 'dip'
        ],

        'architecture': [
            'mvc', 'microservices', 'layered', 'event-driven', 'client-server',
            'monolith', 'service-oriented', 'soa', 'n-tier', 'hexagonal', 'clean architecture'
        ],

        'ddd': [
            'bounded context', 'aggregate', 'entity', 'value object', 'repository',
            'domain service', 'ubiquitous language', 'domain event', 'factory'
        ],

        'quality': [
            'maintainability', 'scalability', 'testability', 'performance',
            'security', 'availability', 'reliability', 'extensibility', 'modifiability',
            'usability', 'fault tolerance'
        ],

        'code_structure': [
            'class', 'interface', 'module', 'component', 'package',
            'method', 'inheritance', 'composition', 'abstraction', 'encapsulation'
        ]
    }
}

# Optional reverse mapping for convenience: keyword => domain type
KEYWORD_TO_TYPE = {
    keyword: type_key
    for type_key, keywords in DOMAIN_FOCUS['keywords'].items()
    for keyword in keywords
}
