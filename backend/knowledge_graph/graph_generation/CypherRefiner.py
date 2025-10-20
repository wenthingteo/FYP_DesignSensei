import re

# Input and output file paths
input_file = "cypher_output/new_1005_knowledge_graph.cypher"      # your original Cypher file
output_file = "cleaned.cypher"      # the cleaned file output

# Label normalization map
label_corrections = {
    "design_principles": "DesignPrinciple",
    "design_patterns": "DesignPattern",
    "architecture": "Architecture",
    "archpattern": "ArchPattern",
    "dddconcept": "DDDConcept",
    "codestructure": "CodeStructure",
    "qualityattribute": "QualityAttribute",
    "designprinciple": "DesignPrinciple",
    "designpattern": "DesignPattern",
}

def normalize_label(label):
    """Normalize labels to PascalCase and fix known variations"""
    clean = label.strip(":() ")
    normalized = label_corrections.get(clean.lower(), clean)
    return normalized[0].upper() + normalized[1:] if normalized else clean

def fix_cypher_line(line):
    """Fix a single line of Cypher code"""
    original_line = line

    # --- Replace single quotes with double quotes safely ---
    line = re.sub(r"'([^']*)'", lambda m: f'"{m.group(1)}"', line)

    # --- Normalize labels in MERGE/MATCH statements ---
    line = re.sub(r":([a-zA-Z_]+)", lambda m: f":{normalize_label(m.group(1))}", line)

    # --- Add missing labels if only property is matched (heuristic) ---
    if re.search(r'MATCH\s*\(a\s*{', line) and "name:" in line:
        line = re.sub(r'MATCH\s*\(a\s*{', "MATCH (a:Concept {", line)
    if re.search(r'MATCH\s*\(b\s*{', line) and "name:" in line:
        line = re.sub(r'MATCH\s*\(b\s*{', "MATCH (b:Concept {", line)

    # --- Detect and remove self-referencing relationships ---
    if re.search(r'MATCH.*\(a.*name:\s*"([^"]+)"\).*\(b.*name:\s*"\1"\)', line):
        print(f"⚠️  Skipped self-referencing relationship: {line.strip()}")
        return None

    return line

def process_cypher_file(input_path, output_path):
    cleaned_lines = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            fixed = fix_cypher_line(stripped)
            if fixed:
                cleaned_lines.append(fixed)

    # Write cleaned output
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(cleaned_lines))

    print(f"\n✅ Cleaning completed! Output saved to: {output_path}")
    print(f"Total lines written: {len(cleaned_lines)}")

# Run the script
if __name__ == "__main__":
    process_cypher_file(input_file, output_file)