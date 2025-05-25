# text_extraction.py    
import os
import fitz  # PyMuPDF for PDF
from pptx import Presentation
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_path):
    """Extract text from PDF file."""
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF {file_path}: {e}")
        return ""

def extract_text_from_pptx(file_path):
    """Extract text from PowerPoint file."""
    try:
        prs = Presentation(file_path)
        text = ""
        for slide_num, slide in enumerate(prs.slides, 1):
            slide_text = f"\n--- Slide {slide_num} ---\n"
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    slide_text += shape.text + "\n"
            text += slide_text
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PPTX {file_path}: {e}")
        return ""

def extract_texts_from_folder(folder_path):
    """Extract text from all supported files in a folder."""
    if not os.path.exists(folder_path):
        logger.error(f"Folder does not exist: {folder_path}")
        return {}
    
    extracted_texts = {}
    supported_extensions = {'.pdf', '.pptx'}
    
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        
        # Skip directories
        if os.path.isdir(file_path):
            continue
            
        file_ext = os.path.splitext(filename)[1].lower()
        
        if file_ext == '.pdf':
            logger.info(f"Extracting text from PDF: {filename}")
            text = extract_text_from_pdf(file_path)
            if text.strip():  # Only add if text is not empty
                extracted_texts[filename] = text
                
        elif file_ext == '.pptx':
            logger.info(f"Extracting text from PPTX: {filename}")
            text = extract_text_from_pptx(file_path)
            if text.strip():
                extracted_texts[filename] = text
                
        elif file_ext not in supported_extensions:
            logger.info(f"Skipped unsupported file: {filename}")

    return extracted_texts

def save_extracted_texts(extracted_texts, output_dir="./knowledge_graph/extracted_texts"):
    """Save extracted texts to individual files for inspection."""
    os.makedirs(output_dir, exist_ok=True)
    
    for filename, text in extracted_texts.items():
        output_filename = os.path.splitext(filename)[0] + "_extracted.txt"
        output_path = os.path.join(output_dir, output_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        logger.info(f"Saved extracted text to: {output_path}")

if __name__ == "__main__":
    folder_path = "./knowledge_graph/resource"
    all_extracted = extract_texts_from_folder(folder_path)
    
    if all_extracted:
        logger.info(f"Successfully extracted text from {len(all_extracted)} files")
        
        # Preview extracted texts
        for filename, text in all_extracted.items():
            print(f"\n{'='*50}")
            print(f"FILE: {filename}")
            print(f"{'='*50}")
            print(f"Length: {len(text)} characters")
            print(f"Preview:\n{text[:500]}...")
        
        # Optionally save to files
        save_extracted_texts(all_extracted)
    else:
        logger.warning("No texts were extracted")