import fitz  # PyMuPDF
import logging

logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file using PyMuPDF (fitz)
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text from the PDF
    """
    try:
        logger.debug(f"Extracting text from PDF: {pdf_path}")
        text = ""
        
        # Open the PDF file
        with fitz.open(pdf_path) as pdf_document:
            # Get the number of pages
            num_pages = len(pdf_document)
            logger.debug(f"PDF has {num_pages} pages")
            
            # Extract text from each page
            for page_num in range(num_pages):
                page = pdf_document.load_page(page_num)
                page_text = page.get_text()
                text += page_text + "\n\n"  # Add double newline between pages
        
        logger.debug(f"Successfully extracted {len(text)} characters from PDF")
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise Exception(f"Failed to extract text from PDF: {str(e)}")
