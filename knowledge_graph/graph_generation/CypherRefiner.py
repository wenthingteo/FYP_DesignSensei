"""
Enhanced Semantic Cypher Refiner with Duplicate Handling and Relevance Score Preservation
Combines weak relationship replacement with comprehensive semantic relationship enrichment
for software architecture knowledge graphs while maintaining data integrity
"""

import os
import re
import json
import hashlib
from typing import List, Dict, Set, Tuple
from collections import defaultdict

class ComprehensiveSemanticMappings:
    """Comprehensive semantic relationship mappings for software architecture domain"""
    
    def __init__(self):
        self.semantic_rules = self._build_comprehensive_mappings()
        self.weak_patterns = [
            "RELATES_TO", "CONNECTED_TO", "ASSOCIATED_WITH", 
            "LINKED_TO", "HAS_RELATIONSHIP", "IS_RELATED"
        ]
    
    def _build_comprehensive_mappings(self) -> Dict:
        """Build comprehensive semantic mappings"""
        return {
            # SOLID Principles -> Code Structures
            ("open/closed", "parser"): ("EXEMPLIFIES", 0.95, "Parser exemplifies OCP through extensible implementations"),
            ("open/closed", "abstract"): ("IMPLEMENTS", 0.9, "Abstract classes implement OCP by enabling extension"),
            ("open/closed", "interface"): ("ENABLES", 0.9, "Interfaces enable OCP through contracts"),
            ("open/closed", "class"): ("GUIDES", 0.8, "OCP guides class design for extensibility"),
            ("open/closed", "method"): ("APPLIES_TO", 0.75, "OCP applies to method design"),
            
            ("liskov", "substitution"): ("DEFINES", 0.95, "LSP defines substitution requirements"),
            ("liskov", "inheritance"): ("CONSTRAINS", 0.9, "LSP constrains inheritance relationships"),
            ("liskov", "polymorphism"): ("ENABLES", 0.85, "LSP enables safe polymorphism"),
            ("liskov", "subclass"): ("GOVERNS", 0.85, "LSP governs subclass behavior"),
            
            ("single responsibility", "class"): ("GUIDES", 0.9, "SRP guides class design"),
            ("single responsibility", "method"): ("APPLIES_TO", 0.85, "SRP applies to method responsibility"),
            ("single responsibility", "module"): ("STRUCTURES", 0.8, "SRP structures module organization"),
            ("single responsibility", "component"): ("DEFINES", 0.8, "SRP defines component boundaries"),
            
            ("interface segregation", "interface"): ("SHAPES", 0.95, "ISP shapes interface design"),
            ("interface segregation", "client"): ("PROTECTS", 0.9, "ISP protects clients from unused dependencies"),
            ("interface segregation", "dependency"): ("MINIMIZES", 0.8, "ISP minimizes unnecessary dependencies"),
            
            ("dependency inversion", "abstraction"): ("PROMOTES", 0.95, "DIP promotes dependency on abstractions"),
            ("dependency inversion", "implementation"): ("DECOUPLES_FROM", 0.9, "DIP decouples from concrete implementations"),
            ("dependency inversion", "injection"): ("ENABLES", 0.85, "DIP enables dependency injection"),
            
            # Design Patterns -> Principles
            ("observer", "open/closed"): ("DEMONSTRATES", 0.95, "Observer pattern demonstrates OCP"),
            ("strategy", "open/closed"): ("EXEMPLIFIES", 0.95, "Strategy pattern exemplifies OCP"),
            ("factory", "dependency inversion"): ("SUPPORTS", 0.9, "Factory pattern supports DIP"),
            ("decorator", "single responsibility"): ("APPLIES", 0.85, "Decorator applies SRP"),
            ("adapter", "interface segregation"): ("IMPLEMENTS", 0.8, "Adapter implements ISP concepts"),
            
            # Architectural Patterns -> Quality Attributes
            ("microservices", "scalability"): ("MAXIMIZES", 0.95, "Microservices maximize scalability"),
            ("layered", "maintainability"): ("SUPPORTS", 0.85, "Layered architecture supports maintainability"),
            ("mvc", "testability"): ("ENHANCES", 0.8, "MVC enhances testability"),
            ("event-driven", "loose coupling"): ("ACHIEVES", 0.9, "Event-driven architecture achieves loose coupling"),
            
            # Code Structures -> Principles (reverse mappings)
            ("parser", "open/closed"): ("DEMONSTRATES", 0.9, "Parser demonstrates OCP implementation"),
            ("abstract", "open/closed"): ("ENABLES", 0.85, "Abstract classes enable OCP"),
            ("interface", "interface segregation"): ("IMPLEMENTS", 0.9, "Interface implements ISP"),
            ("class", "single responsibility"): ("FOLLOWS", 0.8, "Class follows SRP"),
            
            # Quality Attributes Interdependencies
            ("maintainability", "extensibility"): ("ENABLES", 0.8, "Maintainability enables extensibility"),
            ("testability", "reliability"): ("IMPROVES", 0.85, "Testability improves reliability"),
            ("performance", "scalability"): ("CONTRIBUTES_TO", 0.75, "Performance contributes to scalability"),
            ("security", "reliability"): ("SUPPORTS", 0.8, "Security supports reliability"),
            
            # Anti-patterns (negative relationships)
            ("god object", "single responsibility"): ("VIOLATES", 0.9, "God object violates SRP"),
            ("tight coupling", "maintainability"): ("REDUCES", 0.85, "Tight coupling reduces maintainability"),
            ("code duplication", "maintainability"): ("HINDERS", 0.8, "Code duplication hinders maintainability"),
        }

class EnhancedCypherRefiner:
    """Enhanced Cypher refiner that handles duplicates and preserves relevance scores"""
    
    def __init__(self, cypher_file_path: str):
        self.cypher_file_path = cypher_file_path
        self.mappings = ComprehensiveSemanticMappings()
        self.existing_nodes = {}  # name -> {label, properties, all_props}
        self.existing_relationships = {}  # (source, target, type) -> {properties, count}
        self.entity_classifications = {}  # name -> classification
        
        self.load_existing_graph()
    
    def load_existing_graph(self):
        """Parse existing Cypher file to understand current graph structure"""
        if not os.path.exists(self.cypher_file_path):
            print(f"Cypher file not found: {self.cypher_file_path}")
            return
        
        with open(self.cypher_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract nodes with enhanced pattern matching and property preservation
        node_pattern = r'MERGE \(:(\w+)\s*\{\s*name:\s*"([^"]+)"([^}]*)\}\);'
        node_matches = re.findall(node_pattern, content, re.IGNORECASE)
        
        for label, name, properties in node_matches:
            props_str = properties.strip()
            # Parse properties to preserve relevance_score and other important data
            parsed_props = self._parse_properties(props_str)
            
            if name not in self.existing_nodes:
                self.existing_nodes[name] = {
                    'label': label,
                    'properties': props_str,
                    'parsed_props': parsed_props,
                    'count': 1
                }
            else:
                # Handle duplicate nodes by merging properties
                self.existing_nodes[name]['count'] += 1
                # Merge properties, keeping the one with higher relevance_score if available
                existing_relevance = self.existing_nodes[name]['parsed_props'].get('relevance_score', 0)
                new_relevance = parsed_props.get('relevance_score', 0)
                if new_relevance > existing_relevance:
                    self.existing_nodes[name]['properties'] = props_str
                    self.existing_nodes[name]['parsed_props'] = parsed_props
            
            # Classify the entity
            self.entity_classifications[name] = self._classify_entity(name, label)
        
        # Extract existing relationships with duplicate handling
        rel_pattern = r'MATCH \(s \{name:\s*"([^"]+)"\}\),\s*\(t \{name:\s*"([^"]+)"\}\)\s*MERGE \(s\)-\[:(\w+)([^]]*)\]->\(t\);'
        rel_matches = re.findall(rel_pattern, content, re.IGNORECASE | re.DOTALL)
        
        for source, target, rel_type, properties in rel_matches:
            key = (source, target, rel_type)
            props_str = properties.strip()
            
            if key not in self.existing_relationships:
                self.existing_relationships[key] = {
                    'properties': props_str,
                    'parsed_props': self._parse_properties(props_str),
                    'count': 1
                }
            else:
                self.existing_relationships[key]['count'] += 1
        
        print(f"Loaded {len(self.existing_nodes)} unique nodes (with {sum(n['count'] for n in self.existing_nodes.values())} total occurrences)")
        print(f"Loaded {len(self.existing_relationships)} unique relationships (with {sum(r['count'] for r in self.existing_relationships.values())} total occurrences)")
    
    def _parse_properties(self, props_str: str) -> Dict:
        """Parse property string into dictionary"""
        if not props_str or not props_str.strip():
            return {}
        
        props = {}
        # Remove leading comma and whitespace
        props_str = props_str.lstrip(', ')
        
        # Simple property parsing (handles basic cases)
        prop_pattern = r'(\w+):\s*"([^"]*)"|\b(\w+):\s*([^,}]+)'
        matches = re.findall(prop_pattern, props_str)
        
        for match in matches:
            if match[0] and match[1]:  # String value
                key, value = match[0], match[1]
            elif match[2] and match[3]:  # Non-string value
                key, value = match[2], match[3].strip()
                # Try to convert to appropriate type
                try:
                    if '.' in value:
                        value = float(value)
                    else:
                        value = int(value)
                except ValueError:
                    pass
            else:
                continue
            props[key] = value
        
        return props
    
    def _classify_entity(self, name: str, label: str) -> str:
        """Classify entity based on name and label"""
        name_lower = name.lower()
        
        # Principle classifications
        if 'principle' in name_lower:
            if 'open' in name_lower and 'closed' in name_lower:
                return 'open/closed'
            elif 'liskov' in name_lower or 'substitution' in name_lower:
                return 'liskov'
            elif 'single' in name_lower and 'responsibility' in name_lower:
                return 'single responsibility'
            elif 'interface' in name_lower and 'segregation' in name_lower:
                return 'interface segregation'
            elif 'dependency' in name_lower and 'inversion' in name_lower:
                return 'dependency inversion'
        
        # Pattern classifications
        if 'pattern' in name_lower:
            if 'observer' in name_lower:
                return 'observer'
            elif 'strategy' in name_lower:
                return 'strategy'
            elif 'factory' in name_lower:
                return 'factory'
            elif 'decorator' in name_lower:
                return 'decorator'
            elif 'adapter' in name_lower:
                return 'adapter'
        
        # Architecture classifications
        if 'architecture' in name_lower or 'architectural' in name_lower:
            if 'microservice' in name_lower:
                return 'microservices'
            elif 'layer' in name_lower:
                return 'layered'
            elif 'mvc' in name_lower:
                return 'mvc'
            elif 'event' in name_lower:
                return 'event-driven'
        
        # Code structure classifications
        code_structures = {
            'parser': 'parser',
            'abstract': 'abstract',
            'interface': 'interface',
            'class': 'class',
            'method': 'method',
            'module': 'module',
            'component': 'component'
        }
        
        for keyword, classification in code_structures.items():
            if keyword in name_lower:
                return classification
        
        # Quality attributes
        quality_attrs = {
            'scalability': 'scalability',
            'maintainability': 'maintainability',
            'testability': 'testability',
            'performance': 'performance',
            'security': 'security',
            'reliability': 'reliability'
        }
        
        for keyword, classification in quality_attrs.items():
            if keyword in name_lower:
                return classification
        
        return 'unknown'
    
    def find_semantic_relationship(self, source_name: str, target_name: str) -> Dict:
        """Find appropriate semantic relationship between two entities"""
        source_class = self.entity_classifications.get(source_name, 'unknown')
        target_class = self.entity_classifications.get(target_name, 'unknown')
        
        # Direct lookup in semantic rules
        key = (source_class, target_class)
        if key in self.mappings.semantic_rules:
            rel_type, strength, description = self.mappings.semantic_rules[key]
            return {
                'type': rel_type,
                'strength': strength,
                'description': description,
                'confidence': 0.9
            }
        
        # Try reverse lookup
        reverse_key = (target_class, source_class)
        if reverse_key in self.mappings.semantic_rules:
            rel_type, strength, description = self.mappings.semantic_rules[reverse_key]
            # Create appropriate reverse relationship
            reverse_relations = {
                'EXEMPLIFIES': 'IS_EXEMPLIFIED_BY',
                'IMPLEMENTS': 'IS_IMPLEMENTED_BY',
                'ENABLES': 'IS_ENABLED_BY',
                'DEMONSTRATES': 'IS_DEMONSTRATED_BY',
                'SUPPORTS': 'IS_SUPPORTED_BY',
                'GUIDES': 'IS_GUIDED_BY'
            }
            reverse_type = reverse_relations.get(rel_type, f"INVERSE_OF_{rel_type}")
            return {
                'type': reverse_type,
                'strength': strength * 0.9,
                'description': f"Reverse: {description}",
                'confidence': 0.8
            }
        
        # Fallback to contextual relationships
        return self._generate_contextual_relationship(source_name, target_name, source_class, target_class)
    
    def _generate_contextual_relationship(self, source_name: str, target_name: str, 
                                        source_class: str, target_class: str) -> Dict:
        """Generate contextual relationship based on entity types"""
        
        # Context-based relationship patterns
        contextual_patterns = {
            ('principle', 'code'): ('GUIDES', 0.7, 'Principle guides code structure'),
            ('pattern', 'principle'): ('IMPLEMENTS', 0.75, 'Pattern implements principle'),
            ('architecture', 'quality'): ('AFFECTS', 0.7, 'Architecture affects quality attribute'),
            ('code', 'quality'): ('IMPACTS', 0.6, 'Code structure impacts quality'),
        }
        
        # Classify into broader categories
        broad_source = self._get_broad_category(source_class)
        broad_target = self._get_broad_category(target_class)
        
        key = (broad_source, broad_target)
        if key in contextual_patterns:
            rel_type, strength, description = contextual_patterns[key]
            return {
                'type': rel_type,
                'strength': strength,
                'description': f"{description}: {source_name} -> {target_name}",
                'confidence': 0.6
            }
        
        # Ultimate fallback
        return {
            'type': 'SEMANTICALLY_RELATED',
            'strength': 0.5,
            'description': f"Semantic relationship between {source_name} and {target_name}",
            'confidence': 0.4
        }
    
    def _get_broad_category(self, classification: str) -> str:
        """Get broad category for classification"""
        principle_types = ['open/closed', 'liskov', 'single responsibility', 'interface segregation', 'dependency inversion']
        pattern_types = ['observer', 'strategy', 'factory', 'decorator', 'adapter']
        architecture_types = ['microservices', 'layered', 'mvc', 'event-driven']
        code_types = ['parser', 'abstract', 'interface', 'class', 'method', 'module', 'component']
        quality_types = ['scalability', 'maintainability', 'testability', 'performance', 'security', 'reliability']
        
        if classification in principle_types:
            return 'principle'
        elif classification in pattern_types:
            return 'pattern'
        elif classification in architecture_types:
            return 'architecture'
        elif classification in code_types:
            return 'code'
        elif classification in quality_types:
            return 'quality'
        else:
            return 'unknown'
    
    def replace_weak_relationships(self) -> List[Dict]:
        """Identify and replace weak relationships with semantic ones"""
        replacements = []
        
        for (source, target, rel_type), rel_data in self.existing_relationships.items():
            # Check if this is a weak relationship
            if rel_type in self.mappings.weak_patterns:
                # Find semantic replacement
                new_relationship = self.find_semantic_relationship(source, target)
                
                # Only replace if we have reasonable confidence
                if new_relationship['confidence'] > 0.5:
                    replacements.append({
                        'source': source,
                        'target': target,
                        'old_type': rel_type,
                        'new_type': new_relationship['type'],
                        'strength': new_relationship['strength'],
                        'description': new_relationship['description'],
                        'confidence': new_relationship['confidence'],
                        'old_properties': rel_data['properties'],
                        'original_count': rel_data['count']
                    })
        
        return replacements
    
    def generate_additional_relationships(self) -> List[Dict]:
        """Generate additional semantic relationships between existing entities"""
        new_relationships = []
        existing_pairs = {(source, target) for source, target, _ in self.existing_relationships.keys()}
        
        # Get all node pairs that don't have relationships yet
        nodes = list(self.existing_nodes.keys())
        for i, source in enumerate(nodes):
            for target in nodes[i+1:]:
                if (source, target) not in existing_pairs and (target, source) not in existing_pairs:
                    # Check if these entities should have a semantic relationship
                    relationship = self.find_semantic_relationship(source, target)
                    
                    # Only add high-confidence relationships
                    if relationship['confidence'] > 0.7:
                        new_relationships.append({
                            'source': source,
                            'target': target,
                            'type': relationship['type'],
                            'strength': relationship['strength'],
                            'description': relationship['description'],
                            'confidence': relationship['confidence'],
                            'source_type': 'semantic_inference'
                        })
        
        return new_relationships
    
    def generate_enhanced_cypher(self, output_file: str = None) -> str:
        """Generate enhanced Cypher file with semantic relationships and no duplicates"""
        if output_file is None:
            base_name = os.path.splitext(self.cypher_file_path)[0]
            output_file = f"{base_name}_semantically_enhanced_deduped.cypher"
        
        # Get replacements and new relationships
        replacements = self.replace_weak_relationships()
        new_relationships = self.generate_additional_relationships()
        
        # Write enhanced file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("// === SEMANTICALLY ENHANCED KNOWLEDGE GRAPH (DEDUPLICATED) ===\n")
            f.write(f"// Enhanced by Comprehensive Semantic Refiner\n")
            f.write(f"// Removed duplicates and preserved relevance scores\n")
            f.write(f"// Replaced {len(replacements)} weak relationships\n")
            f.write(f"// Added {len(new_relationships)} new semantic relationships\n\n")
            
            # Write unique nodes with preserved properties
            f.write("// === UNIQUE NODES ===\n")
            for name, node_data in self.existing_nodes.items():
                props_str = node_data['properties']
                if props_str and not props_str.startswith(','):
                    props_str = ', ' + props_str
                
                query = f'MERGE (:{node_data["label"]} {{ name: "{name}"{props_str} }});'
                f.write(query + "\n")
            
            # Write relationships (original non-weak ones)
            f.write("\n// === ORIGINAL RELATIONSHIPS (NON-WEAK) ===\n")
            for (source, target, rel_type), rel_data in self.existing_relationships.items():
                if rel_type not in self.mappings.weak_patterns:
                    props_str = rel_data['properties']
                    if props_str and not props_str.startswith('{'):
                        props_str = ' {' + props_str + '}'
                    elif not props_str:
                        props_str = ''
                    
                    query = f'''MATCH (s {{name: "{source}"}}), (t {{name: "{target}"}})
MERGE (s)-[:{rel_type}{props_str}]->(t);'''
                    f.write(query + "\n")
            
            # Write replaced weak relationships
            f.write("\n// === ENHANCED SEMANTIC RELATIONSHIPS (REPLACED WEAK ONES) ===\n")
            for replacement in replacements:
                query = f'''MATCH (s {{name: "{replacement['source']}"}})
MATCH (t {{name: "{replacement['target']}"}})
MERGE (s)-[:{replacement['new_type']} {{
    strength: {replacement['strength']},
    description: "{replacement['description']}",
    confidence: {replacement['confidence']},
    semantic_type: "enhanced",
    replaced_from: "{replacement['old_type']}"
}}]->(t);'''
                f.write(query + "\n")
            
            # Add new semantic relationships
            if new_relationships:
                f.write("\n// === ADDITIONAL SEMANTIC RELATIONSHIPS ===\n")
                for rel in new_relationships:
                    query = f'''MATCH (s {{name: "{rel['source']}"}})
MATCH (t {{name: "{rel['target']}"}})
MERGE (s)-[:{rel['type']} {{
    strength: {rel['strength']},
    description: "{rel['description']}",
    confidence: {rel['confidence']},
    source_type: "{rel['source_type']}"
}}]->(t);'''
                    f.write(query + "\n")
            
            # Add summary
            f.write(f"\n\n// === ENHANCEMENT SUMMARY ===\n")
            f.write(f"// Unique Nodes: {len(self.existing_nodes)}\n")
            f.write(f"// Original Relationships: {len([r for r in self.existing_relationships.keys() if r[2] not in self.mappings.weak_patterns])}\n")
            f.write(f"// Weak Relationship Replacements: {len(replacements)}\n")
            f.write(f"// New Semantic Relationships: {len(new_relationships)}\n")
            
            f.write(f"// Weak Relationship Replacements:\n")
            for replacement in replacements:
                f.write(f"// - {replacement['source']} -> {replacement['target']}: {replacement['old_type']} -> {replacement['new_type']}\n")
            
            f.write(f"// New Semantic Relationships:\n")
            for rel in new_relationships:
                f.write(f"// - {rel['source']} -> {rel['target']}: {rel['type']} (confidence: {rel['confidence']})\n")
        
        print(f"Enhanced Cypher file created: {output_file}")
        print(f"Unique nodes: {len(self.existing_nodes)}")
        print(f"Replaced {len(replacements)} weak relationships")
        print(f"Added {len(new_relationships)} new semantic relationships")
        
        return output_file

def enhance_cypher_semantically(cypher_file_path: str, output_file: str = None) -> str:
    """Main function to enhance Cypher file with semantic relationships"""
    refiner = EnhancedCypherRefiner(cypher_file_path)
    return refiner.generate_enhanced_cypher(output_file)

if __name__ == "__main__":
    # Example usage
    input_file = "./knowledge_graph/graph_generation/versionKG/VER3knowledge_graph.cypher"
    output_file = enhance_cypher_semantically(input_file)
    print(f"Enhanced graph saved to: {output_file}")