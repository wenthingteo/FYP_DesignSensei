import csv
import os
import re
import ast
from collections import defaultdict

cypher_file = './knowledge_graph/knowledge_graph.cypher'
output_dir = './knowledge_graph/CSV'
os.makedirs(output_dir, exist_ok=True)

# Separate storage for domains and topics
domains = set()
topics = {}
rels = []
domain_topic_rels = []  # To track which topics belong to which domains

def parse_properties(prop_str):
    try:
        # Handle empty properties
        if not prop_str.strip():
            return {}
        
        # Replace property syntax for Python dict
        py_dict = re.sub(r'(\w+)\s*:', r'"\1":', prop_str)
        return ast.literal_eval("{" + py_dict + "}")
    except Exception as e:
        print(f"[!] Property parse error: {e} => {prop_str}")
        return {}

# Enhanced node line parser
def parse_node_line(line):
    # Match various node creation patterns
    patterns = [
        r'(CREATE|MERGE)\s*\(\s*:?(\w*)?\s*:\s*(\w+)\s*\{(.+?)\}\s*\)\s*;',
        r'(CREATE|MERGE)\s*\(\s*(\w+)?\s*:\s*(\w+)\s*\{(.+?)\}\s*\)\s*;',
        r'(CREATE|MERGE)\s*\(\s*:\s*(\w+)\s*\{(.+?)\}\s*\)\s*;',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, line)
        if match:
            groups = match.groups()
            if len(groups) == 4:
                _, _, label, prop_str = groups
            elif len(groups) == 3:
                _, label, prop_str = groups
            else:
                continue
            
            props = parse_properties(prop_str)
            return label, props
    
    return None

# Enhanced relationship line parser
def parse_rel_line(line):
    # More flexible regex to match any relationship type
    # Pattern: MATCH (node1), (node2) MERGE (node1)-[:REL_TYPE {properties}]->(node2);
    
    # With description/properties
    match = re.match(
        r'MATCH\s*\([^{]*\{\s*name\s*:\s*"([^"]+)"\s*\}[^,]*\),\s*\([^{]*\{\s*name\s*:\s*"([^"]+)"\s*\}[^)]*\)\s*MERGE\s*\([^)]*\)-\[:\s*(\w+)\s*\{([^}]+)\}\]->\([^)]*\);',
        line
    )
    if match:
        source, target, rel_type, props_str = match.groups()
        props = parse_properties(props_str)
        description = props.get('description', '')
        return source, target, rel_type, description

    # Without properties
    match = re.match(
        r'MATCH\s*\([^{]*\{\s*name\s*:\s*"([^"]+)"\s*\}[^,]*\),\s*\([^{]*\{\s*name\s*:\s*"([^"]+)"\s*\}[^)]*\)\s*MERGE\s*\([^)]*\)-\[:\s*(\w+)\s*\]->\([^)]*\);',
        line
    )
    if match:
        source, target, rel_type = match.groups()
        return source, target, rel_type, ""

    return None

# Process the file
print("Processing Cypher file...")
with open(cypher_file, 'r', encoding='utf-8') as f:
    raw_lines = f.readlines()

lines = []
i = 0
matched_relationships = 0
unmatched_relationships = 0

while i < len(raw_lines):
    line = raw_lines[i].strip()
    
    # Skip empty or comment lines
    if not line or line.startswith('//'):
        i += 1
        continue

    # Handle multi-line relationships (MATCH + MERGE)
    if line.startswith("MATCH") and (i + 1 < len(raw_lines)):
        next_line = raw_lines[i + 1].strip()
        if next_line.startswith("MERGE"):
            combined = f"{line} {next_line}"
            rel_result = parse_rel_line(combined)
            if rel_result:
                source, target, rel_type, desc = rel_result
                rels.append({
                    'source': source,
                    'target': target,
                    'relationship_type': rel_type,
                    'description': desc.strip(),
                })
                matched_relationships += 1
                i += 2
                continue
            else:
                print(f"[Line {i+1}-{i+2}] RELATIONSHIP not matched:")
                print(f"  {combined}")
                unmatched_relationships += 1
                i += 2
                continue

    # Single line relationship (less common)
    if line.startswith("MATCH") and "MERGE" in line:
        rel_result = parse_rel_line(line)
        if rel_result:
            source, target, rel_type, desc = rel_result
            rels.append({
                'source': source,
                'target': target,
                'relationship_type': rel_type,
                'description': desc.strip(),
            })
            matched_relationships += 1
            i += 1
            continue

    # Try parsing as node
    result = parse_node_line(line)
    if result:
        label, props = result
        
        # Add domain to domains set
        domains.add(label)
        
        # Create topic entry
        topic_name = props.get('name', '')
        if topic_name:
            key = (label, topic_name, props.get("source"), props.get("page"))
            if key not in topics:
                topics[key] = {
                    'name': topic_name,
                    'description_list': [],
                    'source': props.get('source', ''),
                    'page': props.get('page', ''),
                    'relevance_score': float(props.get('relevance_score', 0)),
                    'domain': label  # Track which domain this topic belongs to
                }
                
                # Create domain-topic relationship
                domain_topic_rels.append({
                    'source': label,
                    'target': topic_name,
                    'relationship_type': 'CONTAINS',
                    'description': f'{label} contains {topic_name}'
                })

            desc = props.get('description', '').strip()
            if desc and desc not in topics[key]['description_list']:
                topics[key]['description_list'].append(desc)
        i += 1
        continue

    # If we get here, the line wasn't matched
    if line.strip():  # Only report non-empty lines
        print(f"[Line {i+1}] Not matched: {line[:100]}...")
    i += 1

print(f"\nRelationship parsing summary:")
print(f"  Topic-to-Topic relationships: {matched_relationships}")
print(f"  Domain-to-Topic relationships: {len(domain_topic_rels)}")
print(f"  Unmatched: {unmatched_relationships}")

# Post-process topic descriptions
print("Post-processing topics...")
for topic in topics.values():
    topic['description'] = ';'.join(topic.pop('description_list')[:5])

# Ensure output directory exists
print(f"Creating output directory: {output_dir}")
os.makedirs(output_dir, exist_ok=True)

# Create combined nodes CSV with both domains and topics
nodes_file = os.path.join(output_dir, 'nodes.csv')
print(f"Writing nodes to: {nodes_file}")
try:
    with open(nodes_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['node_type', 'name', 'description', 'source', 'page', 'relevance_score', 'domain'])
        writer.writeheader()
        
        # Write domain nodes
        for domain in sorted(domains):
            writer.writerow({
                'node_type': 'Domain',
                'name': domain,
                'description': f'Domain category: {domain}',
                'source': '',
                'page': '',
                'relevance_score': 1.0,
                'domain': domain
            })
        
        # Write topic nodes
        for topic in topics.values():
            writer.writerow({
                'node_type': 'Topic',
                'name': topic['name'],
                'description': topic['description'],
                'source': topic['source'],
                'page': topic['page'],
                'relevance_score': topic['relevance_score'],
                'domain': topic['domain']
            })
    
    total_nodes = len(domains) + len(topics)
    print(f"✓ Nodes written successfully: {len(domains)} domains + {len(topics)} topics = {total_nodes} total")
except Exception as e:
    print(f"✗ Error writing nodes: {e}")

# Create combined relationships CSV
rels_file = os.path.join(output_dir, 'relationships.csv')
print(f"Writing relationships to: {rels_file}")
try:
    with open(rels_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['source', 'target', 'relationship_type', 'description'])
        writer.writeheader()
        
        # Write domain-topic relationships
        for rel in domain_topic_rels:
            writer.writerow(rel)
        
        # Write topic-topic relationships
        for rel in rels:
            writer.writerow(rel)
    
    total_rels = len(domain_topic_rels) + len(rels)
    print(f"✓ Relationships written successfully: {len(domain_topic_rels)} domain-topic + {len(rels)} topic-topic = {total_rels} total")
except Exception as e:
    print(f"✗ Error writing relationships: {e}")

print(f"\n=== SUMMARY ===")
print(f"Total domains found: {len(domains)}")
print(f"Total topics processed: {len(topics)}")
print(f"Total nodes in CSV: {len(domains) + len(topics)}")
print(f"Total relationships: {len(domain_topic_rels) + len(rels)}")
print(f"Files written to: {output_dir}")

# Show domain breakdown
print(f"\n=== DOMAIN BREAKDOWN ===")
domain_counts = defaultdict(int)
for topic in topics.values():
    domain_counts[topic['domain']] += 1

for domain in sorted(domains):
    print(f"{domain}: {domain_counts[domain]} topics")

# Verify files exist
nodes_exists = os.path.exists(nodes_file)
rels_exists = os.path.exists(rels_file)
print(f"\nNodes CSV exists: {nodes_exists}")
print(f"Relationships CSV exists: {rels_exists}")

if nodes_exists:
    print(f"Nodes file size: {os.path.getsize(nodes_file)} bytes")
if rels_exists:
    print(f"Relationships file size: {os.path.getsize(rels_file)} bytes")