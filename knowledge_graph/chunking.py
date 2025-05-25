# chunking.py
import re
import logging
from typing import List, Dict, Tuple
from nltk.tokenize import sent_tokenize
import nltk

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_text(text: str) -> str:
    """Clean and normalize text."""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,!?;:()\-]', '', text)
    # Remove multiple consecutive punctuation
    text = re.sub(r'([.,!?;:]){2,}', r'\1', text)
    return text.strip()

def estimate_tokens(text: str) -> int:
    """Rough estimation of token count (1 token ≈ 4 characters)."""
    return len(text) // 4

def chunk_by_sentences(text: str, max_tokens: int = 500, overlap_sentences: int = 1) -> List[Dict]:
    """
    Chunk text by sentences with overlap to maintain context.
    
    Args:
        text: Input text
        max_tokens: Maximum tokens per chunk
        overlap_sentences: Number of sentences to overlap between chunks
    
    Returns:
        List of chunk dictionaries with metadata
    """
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = ""
    current_sentences = []
    
    for i, sentence in enumerate(sentences):
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # Check if adding this sentence would exceed the limit
        test_chunk = current_chunk + " " + sentence if current_chunk else sentence
        
        if estimate_tokens(test_chunk) <= max_tokens:
            current_chunk = test_chunk
            current_sentences.append(sentence)
        else:
            # Save current chunk if it's not empty
            if current_chunk:
                chunks.append({
                    'text': current_chunk.strip(),
                    'chunk_id': len(chunks),
                    'sentence_count': len(current_sentences),
                    'token_estimate': estimate_tokens(current_chunk),
                    'sentence_range': (i - len(current_sentences), i - 1)
                })
            
            # Start new chunk with overlap
            if overlap_sentences > 0 and len(current_sentences) > overlap_sentences:
                overlap_text = " ".join(current_sentences[-overlap_sentences:])
                current_chunk = overlap_text + " " + sentence
                current_sentences = current_sentences[-overlap_sentences:] + [sentence]
            else:
                current_chunk = sentence
                current_sentences = [sentence]
    
    # Add the last chunk
    if current_chunk:
        chunks.append({
            'text': current_chunk.strip(),
            'chunk_id': len(chunks),
            'sentence_count': len(current_sentences),
            'token_estimate': estimate_tokens(current_chunk),
            'sentence_range': (len(sentences) - len(current_sentences), len(sentences) - 1)
        })
    
    return chunks

def chunk_by_paragraphs(text: str, max_tokens: int = 500) -> List[Dict]:
    """
    Chunk text by paragraphs, splitting large paragraphs if needed.
    """
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    chunks = []
    
    for para in paragraphs:
        if estimate_tokens(para) <= max_tokens:
            # Paragraph fits within limit
            chunks.append({
                'text': para,
                'chunk_id': len(chunks),
                'token_estimate': estimate_tokens(para),
                'type': 'paragraph'
            })
        else:
            # Split large paragraph into sentences
            sentence_chunks = chunk_by_sentences(para, max_tokens)
            for chunk in sentence_chunks:
                chunk['chunk_id'] = len(chunks)
                chunk['type'] = 'split_paragraph'
                chunks.append(chunk)
    
    return chunks

def process_document_chunks(extracted_texts: Dict[str, str], 
                          max_tokens: int = 500, 
                          method: str = 'sentences') -> Dict[str, List[Dict]]:
    """
    Process all extracted texts and create chunks.
    
    Args:
        extracted_texts: Dictionary of filename -> text
        max_tokens: Maximum tokens per chunk
        method: 'sentences' or 'paragraphs'
    
    Returns:
        Dictionary of filename -> list of chunks
    """
    all_chunks = {}
    
    for filename, text in extracted_texts.items():
        logger.info(f"Chunking text from: {filename}")
        
        # Clean the text
        cleaned_text = clean_text(text)
        
        # Choose chunking method
        if method == 'sentences':
            chunks = chunk_by_sentences(cleaned_text, max_tokens)
        elif method == 'paragraphs':
            chunks = chunk_by_paragraphs(cleaned_text, max_tokens)
        else:
            raise ValueError("Method must be 'sentences' or 'paragraphs'")
        
        # Add source metadata to each chunk
        for chunk in chunks:
            chunk['source_file'] = filename
            chunk['source_type'] = filename.split('.')[-1].lower()
        
        all_chunks[filename] = chunks
        logger.info(f"Created {len(chunks)} chunks from {filename}")
    
    return all_chunks

def save_chunks_to_file(all_chunks: Dict[str, List[Dict]], output_file: str = "./knowledge_graph/chunks_output.txt"):
    """Save chunks to a text file for inspection."""
    with open(output_file, 'w', encoding='utf-8') as f:
        for filename, chunks in all_chunks.items():
            f.write(f"\n{'='*80}\n")
            f.write(f"SOURCE: {filename}\n")
            f.write(f"TOTAL CHUNKS: {len(chunks)}\n")
            f.write(f"{'='*80}\n")
            
            for chunk in chunks:
                f.write(f"\n--- Chunk {chunk['chunk_id']} ---\n")
                f.write(f"Tokens: {chunk['token_estimate']}\n")
                f.write(f"Type: {chunk.get('type', 'sentence-based')}\n")
                f.write(f"Text:\n{chunk['text']}\n")
    
    logger.info(f"Chunks saved to: {output_file}")

if __name__ == "__main__":
    # Example usage - you would import this from text_extraction.py
    from text_extraction import extract_texts_from_folder
    
    folder_path = "./knowledge_graph/resource"
    extracted_texts = extract_texts_from_folder(folder_path)
    
    if extracted_texts:
        # Process chunks
        all_chunks = process_document_chunks(
            extracted_texts, 
            max_tokens=400,  # Slightly smaller to leave room for context
            method='sentences'
        )
        
        # Display summary
        total_chunks = sum(len(chunks) for chunks in all_chunks.values())
        print(f"\nCHUNKING SUMMARY:")
        print(f"Total files processed: {len(all_chunks)}")
        print(f"Total chunks created: {total_chunks}")
        
        for filename, chunks in all_chunks.items():
            avg_tokens = sum(c['token_estimate'] for c in chunks) / len(chunks)
            print(f"  {filename}: {len(chunks)} chunks (avg {avg_tokens:.0f} tokens)")
        
        # Save for inspection
        save_chunks_to_file(all_chunks)
    else:
        logger.error("No extracted texts found to chunk")