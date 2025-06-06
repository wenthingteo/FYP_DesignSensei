MIN_DOCUMENTS_PER_TOPIC = 3
MIN_CHUNKS_PER_TOPIC = 50

def validate_coverage(chunked_content: Dict[str, List[Dict]]):
    """Check if all domains have sufficient coverage"""
    domain_counts = {topic: 0 for topic in DOMAIN_FOCUS["topics"]}
    
    for chunks in chunked_content.values():
        for chunk in chunks:
            for domain in chunk.get("domains", []):
                if domain in domain_counts:
                    domain_counts[domain] += 1
    
    # Generate report
    coverage_report = []
    for topic, count in domain_counts.items():
        status = "✅" if count >= MIN_CHUNKS_PER_TOPIC else "⚠️"
        coverage_report.append(f"{status} {topic}: {count} chunks")
    
    logger.info("\nDOMAIN COVERAGE REPORT:\n" + "\n".join(coverage_report))
    
    # Check if any topic is under-represented
    under_represented = [t for t, c in domain_counts.items() if c < MIN_CHUNKS_PER_TOPIC]
    if under_represented:
        logger.warning(f"Add resources for: {', '.join(under_represented)}")