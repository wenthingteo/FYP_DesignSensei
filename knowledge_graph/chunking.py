# chunking.py
import re
import os
import json
import logging
from typing import Dict, List, Tuple
import nltk
from nltk.tokenize import sent_tokenize
from multiprocessing import Pool, cpu_count
from domain_config import DOMAIN_FOCUS

# Download required NLTK data
nltk.download('punkt', quiet=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChunkingStrategy:
    @staticmethod
    def sentence_based(text: str, max_tokens: int = 500, overlap: int = 2) -> List[Dict]:
        """Chunk text preserving sentence boundaries with overlap"""
        sentences = sent_tokenize(text)
        chunks = []
        current_chunk = []
        current_length = 0
        
        for i, sentence in enumerate(sentences):
            sent_length = len(sentence.split())
            
            if current_length + sent_length > max_tokens and current_chunk:
                # Save current chunk
                chunks.append(" ".join(current_chunk))
                
                # Start new chunk with overlap
                overlap_start = max(0, len(current_chunk) - overlap)
                current_chunk = current_chunk[overlap_start:]
                current_length = sum(len(s.split()) for s in current_chunk)
            
            current_chunk.append(sentence)
            current_length += sent_length
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        return chunks

    @staticmethod
    def semantic_based(text: str, max_tokens: int = 500) -> List[Dict]:
        """
        Enhanced semantic chunking that:
        1. Preserves section headers
        2. Keeps related concepts together
        3. Maintains contextual relationships
        """
        # Split by headings (markdown-style or capitalized lines)
        sections = re.split(r'\n#{1,3} ', text)  # Markdown headers
        if len(sections) == 1:
            sections = re.split(r'\n[A-Z][A-Z0-9\s]+\n', text)  # ALL CAPS headers
        
        chunks = []
        current_chunk = ""
        current_header = ""
        
        for section in sections:
            if not section.strip():
                continue
                
            # Extract header from first line
            header_match = re.match(r'^(.*?)\n', section)
            header = header_match.group(1).strip() if header_match else "Section"
            content = section[len(header):].strip() if header_match else section
            
            # Process section content
            section_chunks = ChunkingStrategy.sentence_based(content, max_tokens)
            
            for chunk in section_chunks:
                # Prepend header for context
                chunk_with_header = f"{header}: {chunk}" if header else chunk
                chunks.append(chunk_with_header)
                
        return chunks

def is_relevant_chunk(text: str) -> bool:
    """Balanced relevance check with domain weighting"""
    text_lower = text.lower()
    domain_score = 0
    
    for domain, keywords in DOMAIN_FOCUS["keywords"].items():
        for kw in keywords:
            if kw in text_lower:
                domain_score += 1
                # Return early if we have strong signal
                if domain_score >= 2:
                    return True
    
    # Also allow longer chunks with at least one keyword
    if domain_score >= 1 and len(text.split()) > 100:
        return True
        
    return False

def process_content(args):
    """Wrapper for parallel processing"""
    content, strategy, max_tokens = args
    return _process_content(content, strategy, max_tokens)

def _process_content(content: Dict, strategy: str = "semantic", max_tokens: int = 400) -> List[Dict]:
    text = ""
    if content['type'] == 'text':
        text = content['text']
    elif content['type'] == 'slide':
        text = f"{content['title']}\n{content['content']}"
    
    if strategy == "semantic":
        chunks = ChunkingStrategy.semantic_based(text, max_tokens)
    else:
        chunks = ChunkingStrategy.sentence_based(text, max_tokens)
    
    processed_chunks = []
    for chunk_text in chunks:
        if not is_relevant_chunk(chunk_text):
            continue
            
        # Determine domains for this chunk
        chunk_topics = []
        for topic, keywords in DOMAIN_FOCUS["keywords"].items():
            if any(kw in chunk_text.lower() for kw in keywords):
                chunk_topics.append(topic)
                
        processed_chunks.append({
            "text": chunk_text,
            "domains": chunk_topics,
            "source": content['source_file'],
            "section": content.get('section', ''),
            "position": content.get('page') or content.get('slide'),
            "chunk_type": strategy,
            "token_estimate": len(chunk_text.split())
        })
    
    return processed_chunks

def chunk_extracted_content(extracted_content: Dict, strategy: str = "semantic", max_workers: int = None) -> Dict[str, List[Dict]]:
    """Parallel chunking for large datasets"""
    if max_workers is None:
        max_workers = max(1, cpu_count() - 1)
        
    chunked_content = {}
    tasks = []
    
    for filename, sections in extracted_content.items():
        for section in sections:
            section['source_file'] = filename
            tasks.append((section, strategy, 400))  # max_tokens=400
    
    with Pool(processes=max_workers) as pool:
        results = pool.map(process_content, tasks)
        
    # Group results by filename
    for result in results:
        for chunk in result:
            filename = chunk['source']
            if filename not in chunked_content:
                chunked_content[filename] = []
            chunked_content[filename].append(chunk)
    
    for filename, chunks in chunked_content.items():
        logger.info(f"Created {len(chunks)} chunks from {filename}")
    
    return chunked_content

def save_chunked_content(chunked_content: Dict, output_dir: str):
    """Save chunked content with metadata"""
    os.makedirs(output_dir, exist_ok=True)
    for filename, chunks in chunked_content.items():
        base_name = os.path.splitext(filename)[0]
        output_path = os.path.join(output_dir, f"{base_name}_chunks.jsonl")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for chunk in chunks:
                f.write(json.dumps(chunk) + '\n')
        logger.info(f"Saved {len(chunks)} chunks to {output_path}")
