"""
Fixed CSV Generator for Neo4j Import
Properly extracts node names and relationship sources/targets from Cypher files
"""

import re
import csv
import os
import hashlib

def generate_csv_with_proper_extraction(cypher_file_path: str) -> dict:
    """Generate CSV files with proper node and relationship extraction"""
    print(f"\nGenerating CSV files from {cypher_file_path}...")
    
    base_name = os.path.splitext(cypher_file_path)[0]
    nodes_csv = f"{base_name}_nodes_fixed.csv"
    relationships_csv = f"{base_name}_relationships_fixed.csv"
    
    # Read Cypher file
    with open(cypher_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract nodes - improved pattern to handle your specific format
    nodes = set()
    
    # Pattern to match MERGE (:Label { name: "Name", ... })
    node_pattern = r'MERGE\s*\(\s*:\s*(\w+)\s*\{\s*name:\s*"([^"]+)"[^}]*\}\s*\)'
    node_matches = re.findall(node_pattern, content, re.IGNORECASE | re.DOTALL)
    
    print(f"Found {len(node_matches)} node matches")
    
    for label, name in node_matches:
        nodes.add((name.strip(), label.strip()))
        print(f"  Node: {name} ({label})")
    
    # If no nodes found with MERGE pattern, try CREATE pattern
    if not nodes:
        create_pattern = r'CREATE\s*\(\s*:\s*(\w+)\s*\{\s*name:\s*"([^"]+)"[^}]*\}\s*\)'
        create_matches = re.findall(create_pattern, content, re.IGNORECASE | re.DOTALL)
        for label, name in create_matches:
            nodes.add((name.strip(), label.strip()))
    
    # Write nodes CSV
    with open(nodes_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'name', 'label'])
        for i, (name, label) in enumerate(sorted(nodes), 1):
            node_id = f"node_{i:06d}"
            writer.writerow([node_id, name, label])
    
    # Extract relationships with properties - improved patterns
    relationships = set()
    
    # Pattern 1: MATCH (s {name: "SourceName"}), (t {name: "TargetName"}) MERGE (s)-[:REL_TYPE {properties}]->(t)
    pattern1 = r'MATCH\s*\(\s*s\s*\{\s*name:\s*"([^"]+)"\s*\}\s*\)\s*,?\s*\(\s*t\s*\{\s*name:\s*"([^"]+)"\s*\}\s*\)\s*MERGE\s*\(\s*s\s*\)\s*-\s*\[\s*:\s*(\w+)([^]]*)\]\s*->\s*\(\s*t\s*\)'
    matches1 = re.findall(pattern1, content, re.IGNORECASE | re.DOTALL)
    
    # Pattern 2: MATCH (s {name: "Source"}) MATCH (t {name: "Target"}) MERGE (s)-[:REL {props}]->(t)
    pattern2 = r'MATCH\s*\(\s*s\s*\{\s*name:\s*"([^"]+)"\s*\}\s*\)\s*MATCH\s*\(\s*t\s*\{\s*name:\s*"([^"]+)"\s*\}\s*\)\s*MERGE\s*\(\s*s\s*\)\s*-\s*\[\s*:\s*(\w+)([^]]*)\]\s*->\s*\(\s*t\s*\)'
    matches2 = re.findall(pattern2, content, re.IGNORECASE | re.DOTALL)
    
    # Pattern 3: Direct MERGE with node references
    pattern3 = r'MERGE\s*\(\s*\{\s*name:\s*"([^"]+)"\s*\}\s*\)\s*-\s*\[\s*:\s*(\w+)([^]]*)\]\s*->\s*\(\s*\{\s*name:\s*"([^"]+)"\s*\}\s*\)'
    matches3 = re.findall(pattern3, content, re.IGNORECASE | re.DOTALL)
    
    print(f"Relationship matches found:")
    print(f"  Pattern 1: {len(matches1)}")
    print(f"  Pattern 2: {len(matches2)}")
    print(f"  Pattern 3: {len(matches3)}")
    
    # Process all relationship matches
    for source, target, rel_type, properties in matches1 + matches2:
        # Clean up properties
        props = properties.strip()
        if props.startswith('{') and props.endswith('}'):
            props = props[1:-1].strip()
        relationships.add((source.strip(), target.strip(), rel_type.strip(), props))
        print(f"  Relationship: {source} -> {target} ({rel_type})")
    
    for source, rel_type, properties, target in matches3:
        # Clean up properties
        props = properties.strip()
        if props.startswith('{') and props.endswith('}'):
            props = props[1:-1].strip()
        relationships.add((source.strip(), target.strip(), rel_type.strip(), props))
        print(f"  Relationship: {source} -> {target} ({rel_type})")
    
    # Write relationships CSV with properties
    with open(relationships_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'source', 'target', 'relationship_type', 'properties'])
        
        for i, (source, target, rel_type, properties) in enumerate(sorted(relationships), 1):
            rel_id = f"rel_{i:06d}"
            writer.writerow([rel_id, source, target, rel_type, properties])
    
    print(f"\n=== CSV GENERATION COMPLETE ===")
    print(f"Generated files:")
    print(f"  Nodes: {nodes_csv} ({len(nodes)} nodes)")
    print(f"  Relationships: {relationships_csv} ({len(relationships)} relationships)")
    
    # Validation: Check if relationship sources/targets exist in nodes
    node_names = {name for name, label in nodes}
    orphaned_sources = set()
    orphaned_targets = set()
    valid_relationships = []
    
    for source, target, rel_type, properties in relationships:
        if source not in node_names:
            orphaned_sources.add(source)
        if target not in node_names:
            orphaned_targets.add(target)
        if source in node_names and target in node_names:
            valid_relationships.append((source, target, rel_type, properties))
    
    # Create a cleaned relationships CSV with only valid relationships
    if orphaned_sources or orphaned_targets:
        cleaned_csv = f"{base_name}_relationships_cleaned.csv"
        with open(cleaned_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'source', 'target', 'relationship_type', 'properties'])
            
            for i, (source, target, rel_type, properties) in enumerate(sorted(valid_relationships), 1):
                rel_id = f"rel_{i:06d}"
                writer.writerow([rel_id, source, target, rel_type, properties])
        
        print(f"  Cleaned: {cleaned_csv} ({len(valid_relationships)} valid relationships)")
    
    if orphaned_sources or orphaned_targets:
        print(f"\n=== VALIDATION WARNINGS ===")
        if orphaned_sources:
            print(f"Orphaned sources ({len(orphaned_sources)}): {list(orphaned_sources)[:5]}{'...' if len(orphaned_sources) > 5 else ''}")
        if orphaned_targets:
            print(f"Orphaned targets ({len(orphaned_targets)}): {list(orphaned_targets)[:5]}{'...' if len(orphaned_targets) > 5 else ''}")
        print(f"Valid relationships: {len(valid_relationships)}/{len(relationships)}")
    else:
        print(f"\n=== VALIDATION PASSED ===")
        print("All relationship sources and targets match existing nodes")
    
    return {
        'nodes_csv': nodes_csv,
        'relationships_csv': relationships_csv,
        'nodes_count': len(nodes),
        'relationships_count': len(relationships),
        'valid_relationships_count': len(valid_relationships) if 'valid_relationships' in locals() else len(relationships),
        'orphaned_sources': orphaned_sources,
        'orphaned_targets': orphaned_targets,
        'cleaned_csv': cleaned_csv if 'cleaned_csv' in locals() else None
    }

def analyze_cypher_structure(cypher_file_path: str):
    """Analyze the structure of the Cypher file to understand patterns"""
    print(f"\n=== ANALYZING CYPHER STRUCTURE ===")
    
    with open(cypher_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Look for different patterns
    patterns = {
        'MERGE nodes': r'MERGE\s*\(\s*:\s*\w+\s*\{[^}]+\}\s*\)',
        'CREATE nodes': r'CREATE\s*\(\s*:\s*\w+\s*\{[^}]+\}\s*\)',
        'MATCH-MERGE relationships': r'MATCH.*MERGE.*-\[.*\]->',
        'Direct MERGE relationships': r'MERGE.*-\[.*\]->',
        'Node references with name': r'\{\s*name:\s*"[^"]+"\s*\}'
    }
    
    for pattern_name, pattern in patterns.items():
        matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
        print(f"{pattern_name}: {len(matches)} matches")
        if matches and len(matches) <= 3:  # Show first few examples
            for match in matches[:3]:
                print(f"  Example: {match[:100]}...")
    
    # Show actual content sample
    lines = content.split('\n')
    print(f"\nFirst 10 lines of file:")
    for i, line in enumerate(lines[:10]):
        if line.strip():
            print(f"  {i+1}: {line.strip()}")

def main():
    """Main function to generate corrected CSV files"""
    input_file = "./knowledge_graph/graph_generation/versionKG/VER3knowledge_graph_semantically_enhanced.cypher"
    
    if not os.path.exists(input_file):
        print(f"File not found: {input_file}")
        # Try original file
        input_file = "./knowledge_graph/graph_generation/versionKG/VER3knowledge_graph.cypher"
        if not os.path.exists(input_file):
            print("No input files found!")
            return
    
    try:
        # First analyze the structure
        analyze_cypher_structure(input_file)
        
        # Then generate corrected CSVs
        results = generate_csv_with_proper_extraction(input_file)
        
        print(f"\n=== SUMMARY ===")
        print(f"Input file: {input_file}")
        print(f"Generated files:")
        print(f"  - {results['nodes_csv']}")
        print(f"  - {results['relationships_csv']}")
        print(f"Extracted {results['nodes_count']} nodes and {results['relationships_count']} relationships")
        
        if results['orphaned_sources'] or results['orphaned_targets']:
            print(f"\nNote: Some relationships reference nodes that weren't found.")
            print(f"This might indicate missing nodes or different naming patterns.")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()