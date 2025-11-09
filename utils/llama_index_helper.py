import os
import uuid
import logging
from dotenv import load_dotenv
from llama_index.core import Document as LlamaDocument
from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Get Google API Key from environment variable
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

# Create storage directory if it doesn't exist
STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'storage')
os.makedirs(STORAGE_DIR, exist_ok=True)

def get_llm():
    """Get configured Gemini LLM instance."""
    return Gemini(api_key=GOOGLE_API_KEY)

def get_embedding_model():
    """Get configured Gemini embedding model."""
    try:
        return GeminiEmbedding(api_key=GOOGLE_API_KEY, model_name="models/text-embedding-004", dimension=768)
    except Exception as e:
        logger.warning(f"Failed to use text-embedding-004, falling back to embedding-001: {e}")
        return GeminiEmbedding(api_key=GOOGLE_API_KEY, model_name="models/embedding-001", dimension=768)

def process_document(text, filename):
    """
    Process a document with enhanced analysis and LlamaIndex storage
    
    Args:
        text (str): Extracted text from the document
        filename (str): Original filename
        
    Returns:
        str: Index ID for future reference
    """
    try:
        logger.debug(f"Processing document: {filename}")
        
        # Create a unique ID for this index
        index_id = str(uuid.uuid4())
        persist_dir = os.path.join(STORAGE_DIR, index_id)
        os.makedirs(persist_dir, exist_ok=True)
        
        # Initialize LLM and embedding model
        llm = get_llm()
        embed_model = get_embedding_model()
        
        # Create service context with Gemini configuration
        from llama_index.core.settings import Settings
        Settings.llm = llm
        Settings.embed_model = embed_model
        
        # Create enhanced LlamaIndex document with better metadata
        enhanced_metadata = {
            "filename": filename,
            "content_preview": text[:500] + "..." if len(text) > 500 else text,
            "word_count": len(text.split()),
            "char_count": len(text),
            "document_type": detect_document_type_simple(text, filename)
        }
        
        document = LlamaDocument(text=text, metadata=enhanced_metadata)
        
        # Parse document into nodes with better chunking
        parser = SimpleNodeParser.from_defaults(
            chunk_size=1024,
            chunk_overlap=200
        )
        nodes = parser.get_nodes_from_documents([document])
        
        # Create and save index
        index = VectorStoreIndex(nodes)
        
        # Save index to disk with additional metadata
        index.storage_context.persist(persist_dir)
        
        # Also save enhanced document analysis for backup
        enhanced_analysis = {
            "index_id": index_id,
            "filename": filename,
            "metadata": enhanced_metadata,
            "text": text,
            "nodes": len(nodes)
        }
        
        import json
        with open(os.path.join(persist_dir, "enhanced_analysis.json"), "w") as f:
            json.dump(enhanced_analysis, f, indent=2)
        
        logger.debug(f"Successfully processed document and saved index to {persist_dir}")
        logger.debug(f"Document has {len(nodes)} nodes and {enhanced_metadata['word_count']} words")
        
        return index_id
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise Exception(f"Failed to process document: {str(e)}")

def detect_document_type_simple(text, filename):
    """Simple document type detection"""
    text_lower = text.lower()
    filename_lower = filename.lower()
    
    resume_indicators = ['resume', 'curriculum vitae', 'cv', 'experience', 'education', 'skills', 'objective']
    if any(indicator in text_lower for indicator in resume_indicators):
        return "Resume/CV"
    
    paper_indicators = ['abstract', 'introduction', 'methodology', 'results', 'conclusion', 'references']
    if any(indicator in text_lower for indicator in paper_indicators):
        return "Academic Paper"
    
    return "General Document"

def query_document(index_id, question):
    """
    Query a document using LlamaIndex with enhanced error handling
    
    Args:
        index_id (str): Index ID from process_document
        question (str): User's question
        
    Returns:
        str: Answer to the question
    """
    try:
        logger.debug(f"Querying document with index_id: {index_id}")
        logger.debug(f"Question: {question}")
        
        # Load index from disk
        persist_dir = os.path.join(STORAGE_DIR, index_id)
        
        # Check if storage directory exists
        if not os.path.exists(persist_dir):
            raise Exception("Document index not found. Please re-upload the document.")
        
        # Initialize LLM and embedding model
        llm = get_llm()
        embed_model = get_embedding_model()
        
        # Update settings for Gemini
        from llama_index.core.settings import Settings
        Settings.llm = llm
        Settings.embed_model = embed_model
        
        # Load storage context
        storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
        
        # Load index
        index = load_index_from_storage(storage_context)
        
        # First, try to get enhanced analysis if available
        enhanced_analysis_file = os.path.join(persist_dir, "enhanced_analysis.json")
        if os.path.exists(enhanced_analysis_file):
            import json
            with open(enhanced_analysis_file, "r") as f:
                enhanced_data = json.load(f)
                logger.debug(f"Using enhanced analysis: {enhanced_data['metadata']['word_count']} words, {enhanced_data['nodes']} nodes")
        
        # Create query engine with enhanced configuration
        from llama_index.core.prompts import PromptTemplate
        
        # Enhanced prompt template for better context understanding
        prompt_template = PromptTemplate(
            "You are an AI assistant analyzing a specific document. You have access to the exact content of this document. "
            "Please provide a detailed, accurate answer based ONLY on the information present in the document content provided below. "
            "If the information asked for is not in the document, clearly state 'I cannot find this information in the document.' "
            "Be specific and use exact details from the document when available.\n\n"
            "=== DOCUMENT CONTENT ===\n{context}\n"
            "=== END DOCUMENT CONTENT ===\n\n"
            "Question: {query}\n\n"
            "Instructions: Answer based solely on the document content above. If the information is not present, say so clearly."
        )
        
        # Create query engine with better configuration
        query_engine = index.as_query_engine(
            text_qa_template=prompt_template,
            similarity_top_k=5,  # Retrieve more relevant chunks
            response_mode="compact"  # More detailed responses
        )
        
        # Query the index
        response = query_engine.query(question)
        answer = str(response)
        
        # Log the actual response for debugging
        logger.debug(f"Raw response from query engine: {answer[:200]}...")
        
        logger.debug(f"Successfully queried document. Answer length: {len(answer)}")
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
