import os
import uuid
import logging
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Get Google API Key from environment variable
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)

# Create storage directory if it doesn't exist
STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'storage')
os.makedirs(STORAGE_DIR, exist_ok=True)

def process_document_direct(text, filename):
    """
    Process document using direct Gemini API approach
    """
    try:
        logger.debug(f"Processing document directly: {filename}")
        
        # Create a unique ID for this document
        index_id = str(uuid.uuid4())
        persist_dir = os.path.join(STORAGE_DIR, index_id)
        os.makedirs(persist_dir, exist_ok=True)
        
        # Store document content directly
        document_data = {
            "index_id": index_id,
            "filename": filename,
            "text": text,
            "word_count": len(text.split()),
            "char_count": len(text),
            "processed_at": "2025-11-07T16:26:00Z"
        }
        
        with open(os.path.join(persist_dir, "document_data.json"), "w") as f:
            json.dump(document_data, f, indent=2)
        
        logger.debug(f"Successfully processed document. Word count: {document_data['word_count']}")
        return index_id
        
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise Exception(f"Failed to process document: {str(e)}")

def query_document_direct(index_id, question):
    """
    Query document using direct Gemini API with full document context
    """
    try:
        logger.debug(f"Querying document with index_id: {index_id}")
        logger.debug(f"Question: {question}")
        
        # Load document data
        persist_dir = os.path.join(STORAGE_DIR, index_id)
        document_file = os.path.join(persist_dir, "document_data.json")
        
        if not os.path.exists(document_file):
            raise Exception("Document not found. Please re-upload the document.")
        
        with open(document_file, "r") as f:
            document_data = json.load(f)
        
        document_text = document_data["text"]
        filename = document_data["filename"]
        
        logger.debug(f"Loaded document: {filename} with {len(document_text)} characters")
        
        # Create a concise prompt with the document context
        prompt = f"""You are an AI assistant analyzing a document. Answer the following question based ONLY on the information in this document.

Document: {filename}
Word Count: {document_data['word_count']}

Document Content:
{document_text}

Question: {question}

Instructions:
- Answer concisely and directly
- Only include information found in the document
- If information is not in document, state "Not found in document"
- Keep response brief and focused
- Do not include unrelated details

Answer:"""

        # Use Gemini to generate the response
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        answer = response.text
        
        logger.debug(f"Successfully generated response. Answer length: {len(answer)}")
        logger.debug(f"Answer preview: {answer[:200]}...")
        
        return answer
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error querying document: {error_msg}")
        
        # Provide more user-friendly error messages
        if "429" in error_msg or "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
            raise Exception("API quota exceeded. Please try again later or check your API usage limits.")
        elif "401" in error_msg or "unauthorized" in error_msg.lower():
            raise Exception("API authentication failed. Please check your Google API key.")
        elif "403" in error_msg or "forbidden" in error_msg.lower():
            raise Exception("API access forbidden. Please verify your API key permissions.")
        else:
            raise Exception(f"Failed to process question: {error_msg}")

# Create aliases to match the expected function names
process_document = process_document_direct
query_document = query_document_direct