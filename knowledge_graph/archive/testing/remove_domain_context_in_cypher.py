import re

filename = 'knowledge_graph.cypher'

pattern = re.compile(r'(,?\s*domain_context\s*:\s*"[^"]*"\s*,?)')

with open(filename, 'r', encoding='utf-8') as f:
    lines = f.readlines()

with open(filename, 'w', encoding='utf-8') as f:
    for line in lines:
        # Remove domain_context property with comma fix
        line_cleaned = pattern.sub(lambda m: ',' if (m.group(0).startswith(',') and m.group(0).endswith(',')) else '', line)
        # Fix double commas
        line_cleaned = line_cleaned.replace(',,', ',')
        # Remove trailing commas before }
        line_cleaned = re.sub(r',\s*}', '}', line_cleaned)
        f.write(line_cleaned)

print(f"domain_context removed in-place from {filename}")
