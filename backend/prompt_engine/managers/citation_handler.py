from typing import Dict, List

class CitationHandler:
    """Handles proper citation of sources from GraphRAG results"""
    
    def __init__(self):
        # We can keep these formats for internal use or if we change our mind later
        self.citation_formats = {
            'inline': '[Source: {source}, page {page}]',
            'footnote': '[{index}]',
            'academic': '({author}, {year}, p. {page})'
        }
        
    def format_citations(self, 
                        graphrag_results: Dict, 
                        format_type: str = 'inline', # Keep type for flexibility, but it won't be used in output
                        for_llm_prompt: bool = True) -> Dict: 
        """
        Format citations from GraphRAG results.
        
        Args:
            graphrag_results: Results from GraphRAG search
            format_type: Type of citation format (unused if for_llm_prompt is False)
            for_llm_prompt: If True, returns minimal info suitable for LLM grounding.
                            If False, returns structured citation info (e.g., for frontend display).
            
        Returns:
            Dict with structured citation info, potentially simplified for LLM prompt.
        """
        
        if not graphrag_results.get('results'):
            return {'citations': {}, 'references': []}
        
        citations = {}
        references = []
        
        # We'll still extract sources and pages for internal tracking or metadata
        for i, result in enumerate(graphrag_results['results'], 1):
            source = result.get('source', 'Unknown')
            page = result.get('page', 'N/A')
            node_id = result.get('node_id', f'unknown_node_{i}')
            
            # For internal tracking or more detailed metadata for frontend
            references.append({
                'index': i,
                'source': source,
                'page': page,
                'title': result.get('name', 'Unknown'),
                'relevance_score': result.get('relevance_score', 0.0),
                'node_id': node_id
            })
            
            # If we don't want LLM to explicitly cite, we don't format text for it.
            # We can still create a simple key-value for 'citations' for metadata if needed.
            citations[node_id] = {'source': source, 'page': page}
        
        # If not for LLM prompt, return the full structure for potential frontend use.
        if not for_llm_prompt:
             return {
                'citations': citations, # Simplified for prompt, but full for external
                'references': references,
                'citation_instructions': self._get_citation_instructions(format_type) # Can remove this if never used
            }

        # If for LLM prompt, we don't need explicit instructions or formatted text.
        # The prompt will guide the LLM to just *use* the context, not explicitly cite it.
        return {
            'citations': citations, # Still include this for metadata
            'references': references, # Still include this for metadata
            'citation_prompt_hint': "" # Empty string, no explicit citation instruction for LLM
        }
    
    def _get_citation_instructions(self, format_type: str) -> str:
        """Get instructions for using citations in the response (can be simplified/removed for LLM)"""
        # If you truly want to remove all citation instructions, this method could return ""
        # or be entirely removed if `citation_prompt_hint` is always empty.
        return "" # Return empty string for now, as LLM won't be explicitly citing
    
    def validate_sources(self, graphrag_results: Dict) -> List[Dict]:
        """Validate and score the quality of sources"""
        
        if not graphrag_results.get('results'):
            return []
        
        validated_sources = []
        
        for result in graphrag_results['results']:
            source_score = self._calculate_source_score(result)
            
            validated_sources.append({
                'node_id': result.get('node_id', 'N/A'),
                'name': result.get('name', 'Unknown'),
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
        if result.get('source') and result['source'] != 'N/A': # Ensure it's not default N/A
            score += 0.3
        
        # Check if page number is provided
        if result.get('page') and result['page'] != 'N/A':
            score += 0.2
        
        # Check description quality (length and completeness)
        description = result.get('description', '')
        if len(description) > 50:
            score += 0.3
        
        # Check if relationships are provided (indicating richness/connectedness)
        if result.get('relationships') and isinstance(result['relationships'], list) and len(result['relationships']) > 0:
            score += 0.2
        
        return min(score, 1.0)