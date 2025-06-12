from typing import Dict, List

class CitationHandler:
    """Handles proper citation of sources from GraphRAG results"""
    
    def __init__(self):
        self.citation_formats = {
            'inline': '[Source: {source}, page {page}]',
            'footnote': '[{index}]',
            'academic': '({author}, {year}, p. {page})'
        }
        
    def format_citations(self, 
                        graphrag_results: Dict, 
                        format_type: str = 'inline') -> Dict:
        """
        Format citations from GraphRAG results
        
        Args:
            graphrag_results: Results from GraphRAG search
            format_type: Type of citation format ('inline', 'footnote', 'academic')
            
        Returns:
            Dict with formatted citations and reference list
        """
        
        if not graphrag_results.get('results'):
            return {'citations': {}, 'references': []}
        
        citations = {}
        references = []
        
        for i, result in enumerate(graphrag_results['results'], 1):
            source = result.get('source', 'Unknown')
            page = result.get('page', 'N/A')
            
            # Create citation key
            citation_key = f"{result['node_id']}"
            
            # Format citation based on type
            if format_type == 'inline':
                citation_text = self.citation_formats['inline'].format(
                    source=source, page=page
                )
            elif format_type == 'footnote':
                citation_text = self.citation_formats['footnote'].format(index=i)
            else:  # academic
                citation_text = self.citation_formats['academic'].format(
                    author=source.split('.')[0],  # Use filename as author
                    year='2024',  # Default year
                    page=page
                )
            
            citations[citation_key] = citation_text
            
            # Add to references
            references.append({
                'index': i,
                'source': source,
                'page': page,
                'title': result.get('name', 'Unknown'),
                'relevance_score': result.get('relevance_score', 0.0)
            })
        
        return {
            'citations': citations,
            'references': references,
            'citation_instructions': self._get_citation_instructions(format_type)
        }
    
    def _get_citation_instructions(self, format_type: str) -> str:
        """Get instructions for using citations in the response"""
        
        instructions = {
                        'inline': """
                        CITATION INSTRUCTIONS:
                        - Use inline citations immediately after statements that reference the knowledge base
                        - Format: [Source: filename, page X]
                        - Example: "The Single Responsibility Principle states that a class should have only one reason to change [Source: solid-principles.pdf, page 5]."
                        """,
                        'footnote': """
                            CITATION INSTRUCTIONS:
                            - Use numbered footnotes [1], [2], etc.
                            - Include full reference list at the end
                            - Example: "The Observer pattern is used for event handling.[1]"
                        """,
                        'academic': """
                            CITATION INSTRUCTIONS:
                            - Use academic citation format (Author, Year, p. Page)
                            - Include reference list at the end
                            - Example: "Design patterns provide reusable solutions (Gang of Four, 1994, p. 23)."
                        """
        }
        
        return instructions.get(format_type, instructions['inline'])
    
    def validate_sources(self, graphrag_results: Dict) -> List[Dict]:
        """Validate and score the quality of sources"""
        
        if not graphrag_results.get('results'):
            return []
        
        validated_sources = []
        
        for result in graphrag_results['results']:
            source_score = self._calculate_source_score(result)
            
            validated_sources.append({
                'node_id': result['node_id'],
                'name': result['name'],
                'source': result.get('source', 'Unknown'),
                'relevance_score': result.get('relevance_score', 0.0),
                'source_quality_score': source_score,
                'recommended': source_score > 0.7
            })
        
        # Sort by combined score
        validated_sources.sort(
            key=lambda x: (x['relevance_score'] + x['source_quality_score']) / 2,
            reverse=True
        )
        
        return validated_sources
    
    def _calculate_source_score(self, result: Dict) -> float:
        """Calculate quality score for a source"""
        score = 0.0
        
        # Check if source is provided
        if result.get('source'):
            score += 0.3
        
        # Check if page number is provided
        if result.get('page') and result['page'] != 'N/A':
            score += 0.2
        
        # Check description quality (length and completeness)
        description = result.get('description', '')
        if len(description) > 50:
            score += 0.3
        
        # Check if relationships are provided
        if result.get('relationships'):
            score += 0.2
        
        return min(score, 1.0)
