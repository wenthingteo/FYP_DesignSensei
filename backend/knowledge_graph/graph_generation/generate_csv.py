import re
import csv
import os
import hashlib
from typing import Dict, Set, List, Tuple
from collections import defaultdict

def generate_unique_id(content: str, prefix: str = "n") -> str:
    """Generate unique ID based on content hash"""
    hash_obj = hashlib.md5(content.encode('utf-8'))
    return f"{prefix}_{hash_obj.hexdigest()[:8]}"

def parse_properties(props_str: str) -> Dict:
    """Parse property string into dictionary"""
    if not props_str or not props_str.strip():
        return {}
    
    props = {}
    # Remove leading comma and whitespace
    props_str = props_str.lstrip(', ')
    
    # Handle both quoted and unquoted values
    prop_pattern = r'(\w+):\s*"([^"]*)"|(\w+):\s*([^,}]+)'
    matches = re.findall(prop_pattern, props_str)
    
    for match in matches:
        if match[0] and match[1] is not None:  # String value (quoted)
            key, value = match[0], match[1]
        elif match[2] and match[3]:  # Non-string value (unquoted)
            key, value = match[2], match[3].strip()
            # Try to convert to appropriate type
            try:
                if '.' in value:
                    value = float(value)
                elif value.isdigit():
                    value = int(value)
            except ValueError:
                pass
        else:
            continue
        props[key] = value
    
    return props

def extract_semantic_relationships(content: str, unique_nodes: Dict) -> List[Tuple]:
    """Extract semantic relationships between nodes from the Cypher content"""
    relationships = []
    
    print("Extracting relationships from content...")
    
    # Step 1: Find all MATCH statements that define source and target nodes
    match_pattern = r'MATCH\s*\(\s*s\s*\{\s*name:\s*"([^"]+)"\s*\}\s*\),\s*\(\s*t\s*\{\s*name:\s*"([^"]+)"\s*\}\s*\)'
    match_statements = re.findall(match_pattern, content, re.IGNORECASE)
    
    print(f"Found {len(match_statements)} MATCH statements")
    
    # Process MATCH statements
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        match_result = re.search(match_pattern, line, re.IGNORECASE)
        if match_result:
            source_name = match_result.group(1).strip()
            target_name = match_result.group(2).strip()
            
            # Look for the MERGE relationship in the next lines
            j = i + 1
            while j < len(lines) and j < i + 10:
                merge_line = lines[j].strip()
                full_merge = merge_line
                
                # Handle multi-line relationships
                if '->' in merge_line and not merge_line.endswith('(t)'):
                    k = j + 1
                    while k < len(lines) and k < j + 5:
                        next_line = lines[k].strip()
                        full_merge += ' ' + next_line
                        if '(t)' in next_line:
                            break
                        k += 1
                
                # Extract relationship type and properties
                rel_pattern = r'MERGE\s*\(\s*s\s*\)\s*-\s*\[\s*:\s*(\w+)\s*(\{[^}]*\})?\s*\]\s*->\s*\(\s*t\s*\)'
                rel_match = re.search(rel_pattern, full_merge, re.IGNORECASE)
                
                if rel_match:
                    rel_type = rel_match.group(1).strip()
                    properties = rel_match.group(2) if rel_match.group(2) else ""
                    
                    if properties:
                        properties = properties.strip('{}')
                    
                    if source_name in unique_nodes and target_name in unique_nodes:
                        relationships.append((source_name, target_name, rel_type, properties))
                        print(f"    ✓ Found relationship: {source_name} -[{rel_type}]-> {target_name}")
                    break
                j += 1
        i += 1
    
    print(f"Total relationships extracted: {len(relationships)}")
    return relationships

def generate_neo4j_csv_files(cypher_file_path: str) -> dict:
    """Generate Neo4j-compatible CSV files with proper domain hierarchy"""
    print(f"\nGenerating Neo4j CSV files from {cypher_file_path}...")
    
    base_name = os.path.splitext(cypher_file_path)[0]
    nodes_csv = f"{base_name}_nodes_neo4j.csv"
    relationships_csv = f"{base_name}_relationships_neo4j.csv"
    
    with open(cypher_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Track nodes by domain
    nodes_by_domain = defaultdict(list)  # domain_label -> [node_data]
    all_nodes = []  # All nodes including domains
    all_relationships = []  # All relationships
    
    # Extract nodes with property preservation
    node_pattern = r'MERGE\s*\(\s*:\s*(\w+)\s*\{\s*name:\s*"([^"]+)"([^}]*)\}\s*\)'
    node_matches = re.findall(node_pattern, content, re.IGNORECASE | re.DOTALL)
    
    print(f"Found {len(node_matches)} node declarations")
    
    # Process individual nodes first
    seen_names = set()
    for label, name, properties in node_matches:
        name = name.strip()
        label = label.strip()
        props_str = properties.strip()
        
        if name not in seen_names:
            parsed_props = parse_properties(props_str)
            node_id = generate_unique_id(name, "n")
            
            node_data = {
                'id': node_id,
                'name': name,
                'label': label,
                'description': parsed_props.get('description', ''),
                'source': parsed_props.get('source', ''),
                'page': parsed_props.get('page', ''),
                'relevance_score': parsed_props.get('relevance_score', ''),
                'semantic_type': parsed_props.get('semantic_type', 'concept')
            }
            
            nodes_by_domain[label].append(node_data)
            all_nodes.append(node_data)
            seen_names.add(name)
            print(f"  Node: {name} ({label}) -> {node_id}")
    
    # Create domain nodes
    print(f"\nCreating domain nodes...")
    domain_nodes = {}
    for domain_label, child_nodes in nodes_by_domain.items():
        if child_nodes:
            domain_name = f"{domain_label} Domain"
            domain_id = generate_unique_id(domain_name, "d")
            
            # Create a comprehensive description
            child_names = [node['name'] for node in child_nodes[:5]]  # First 5 for description
            domain_description = f"Domain containing {len(child_nodes)} {domain_label.lower()} concepts including: {', '.join(child_names)}"
            if len(child_nodes) > 5:
                domain_description += "..."
            
            domain_data = {
                'id': domain_id,
                'name': domain_name,
                'label': 'Domain',
                'description': domain_description,
                'source': 'system_generated',
                'page': '',
                'relevance_score': 1.0,
                'semantic_type': 'domain'
            }
            
            all_nodes.append(domain_data)
            domain_nodes[domain_label] = domain_data
            print(f"  Domain: {domain_name} -> {domain_id} (contains {len(child_nodes)} nodes)")
    
    # Create CONTAINS relationships (Domain -> Child)
    print(f"\nBuilding CONTAINS relationships...")
    for domain_label, child_nodes in nodes_by_domain.items():
        if domain_label in domain_nodes:
            domain_data = domain_nodes[domain_label]
            
            for child_node in child_nodes:
                rel_id = generate_unique_id(f"{domain_data['id']}_{child_node['id']}_CONTAINS", "r")
                
                relationship = {
                    'id': rel_id,
                    'source': domain_data['id'],
                    'target': child_node['id'],
                    'type': 'CONTAINS',
                    'description': f"The {domain_label} domain contains the concept '{child_node['name']}'",
                    'relationship_type': 'hierarchical',
                    'strength': 'strong'
                }
                
                all_relationships.append(relationship)
                print(f"  CONTAINS: {domain_data['name']} -> {child_node['name']}")
    
    # Extract semantic relationships between child nodes
    print(f"\nExtracting semantic relationships...")
    name_to_node = {node['name']: node for node in all_nodes}
    semantic_relationships = extract_semantic_relationships(content, name_to_node)
    
    for source_name, target_name, rel_type, properties in semantic_relationships:
        source_node = name_to_node[source_name]
        target_node = name_to_node[target_name]
        
        parsed_props = parse_properties(properties)
        rel_id = generate_unique_id(f"{source_node['id']}_{target_node['id']}_{rel_type}", "r")
        
        relationship = {
            'id': rel_id,
            'source': source_node['id'],
            'target': target_node['id'],
            'type': rel_type,
            'description': parsed_props.get('description', f"{source_name} {rel_type.lower().replace('_', ' ')} {target_name}"),
            'relationship_type': 'semantic',
            'strength': parsed_props.get('strength', 'medium'),
            'confidence': parsed_props.get('confidence', '')
        }
        
        all_relationships.append(relationship)
        print(f"  {rel_type}: {source_name} -> {target_name}")
    
    # Write nodes CSV with Neo4j format
    print(f"\nWriting nodes CSV...")
    with open(nodes_csv, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['id:ID', 'name', 'label:LABEL', 'description', 'source', 'page:int', 'relevance_score:float', 'semantic_type']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for node in all_nodes:
            # Convert to Neo4j format
            row = {
                'id:ID': node['id'],
                'name': node['name'],
                'label:LABEL': node['label'],
                'description': node['description'],
                'source': node['source'],
                'page:int': node['page'] if node['page'] else '',
                'relevance_score:float': node['relevance_score'] if node['relevance_score'] else '',
                'semantic_type': node['semantic_type']
            }
            writer.writerow(row)
    
    # Write relationships CSV with Neo4j format
    print(f"Writing relationships CSV...")
    with open(relationships_csv, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['id:ID', ':START_ID', ':END_ID', ':TYPE', 'description', 'relationship_type', 'strength', 'confidence']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for rel in all_relationships:
            row = {
                'id:ID': rel['id'],
                ':START_ID': rel['source'],
                ':END_ID': rel['target'],
                ':TYPE': rel['type'],
                'description': rel['description'],
                'relationship_type': rel['relationship_type'],
                'strength': rel.get('strength', ''),
                'confidence': rel.get('confidence', '')
            }
            writer.writerow(row)
    
    # Generate summary
    summary = {
        'nodes_file': nodes_csv,
        'relationships_file': relationships_csv,
        'total_nodes': len(all_nodes),
        'domain_nodes': len(domain_nodes),
        'concept_nodes': len(all_nodes) - len(domain_nodes),
        'total_relationships': len(all_relationships),
        'hierarchical_relationships': sum(1 for r in all_relationships if r['type'] == 'CONTAINS'),
        'semantic_relationships': sum(1 for r in all_relationships if r['type'] != 'CONTAINS'),
        'domains': list(domain_nodes.keys())
    }
    
    print(f"\nNeo4j CSV Generation Summary:")
    print(f"  Nodes CSV: {nodes_csv}")
    print(f"  Relationships CSV: {relationships_csv}")
    print(f"  Total nodes: {summary['total_nodes']} ({summary['domain_nodes']} domains + {summary['concept_nodes']} concepts)")
    print(f"  Total relationships: {summary['total_relationships']}")
    print(f"  Hierarchical (CONTAINS): {summary['hierarchical_relationships']}")
    print(f"  Semantic relationships: {summary['semantic_relationships']}")
    print(f"  Domains: {', '.join(summary['domains'])}")
    
    return summary

def validate_neo4j_csv_output(nodes_file: str, relationships_file: str):
    """Validate the generated Neo4j CSV files"""
    print("\nValidating Neo4j CSV files...")
    
    # Validate nodes file
    node_ids = set()
    domains = 0
    concepts = 0
    
    with open(nodes_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            node_ids.add(row['id:ID'])
            if row['label:LABEL'] == 'Domain':
                domains += 1
            else:
                concepts += 1
    
    print(f"  Nodes: {len(node_ids)} total ({domains} domains, {concepts} concepts)")
    
    # Validate relationships file
    with open(relationships_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rel_count = 0
        contains_rels = 0
        semantic_rels = 0
        invalid_refs = 0
        rel_types = set()
        
        for row in reader:
            rel_count += 1
            rel_types.add(row[':TYPE'])
            
            if row[':TYPE'] == 'CONTAINS':
                contains_rels += 1
            else:
                semantic_rels += 1
            
            # Check references
            if row[':START_ID'] not in node_ids:
                invalid_refs += 1
                print(f"    Warning: Invalid START_ID: {row[':START_ID']}")
            if row[':END_ID'] not in node_ids:
                invalid_refs += 1
                print(f"    Warning: Invalid END_ID: {row[':END_ID']}")
    
    print(f"  Relationships: {rel_count} total")
    print(f"  CONTAINS: {contains_rels}")
    print(f"  Semantic: {semantic_rels}")
    print(f"  Types: {sorted(rel_types)}")
    print(f"  Invalid references: {invalid_refs}")
    
    if invalid_refs == 0:
        print("  ✅ All references are valid")
    else:
        print(f"  ❌ Found {invalid_refs} invalid references")

if __name__ == "__main__":
    input_file = "./knowledge_graph/graph_generation/new_1005_knowledge_graph.cypher"
    
    if os.path.exists(input_file):
        summary = generate_neo4j_csv_files(input_file)
        validate_neo4j_csv_output(summary['nodes_file'], summary['relationships_file'])
    else:
        print(f"File not found: {input_file}")
        print("Please provide the correct path to your Cypher file.")