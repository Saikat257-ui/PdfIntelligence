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
    return GeminiEmbedding(api_key=GOOGLE_API_KEY, model_name="models/embedding-001", dimension=768)

def process_document(text, filename):
    """
    Process a document with LlamaIndex and store the index
    
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
        
        # Create LlamaIndex document
        document = LlamaDocument(text=text, metadata={"filename": filename})
        
        # Parse document into nodes
        parser = SimpleNodeParser.from_defaults()
        nodes = parser.get_nodes_from_documents([document])
        
        # Create and save index
        index = VectorStoreIndex(nodes)
        
        # Save index to disk
        index.storage_context.persist(persist_dir)
        logger.debug(f"Successfully processed document and saved index to {persist_dir}")
        
        return index_id
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise Exception(f"Failed to process document: {str(e)}")

def query_document(index_id, question):
    """
    Query a document using LlamaIndex
    
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
        
        # Create query engine
        query_engine = index.as_query_engine()
        
        # Query the index
        response = query_engine.query(question)
        answer = str(response)
        
        logger.debug(f"Successfully queried document. Answer length: {len(answer)}")
        return answer
    except Exception as e:
        logger.error(f"Error querying document: {str(e)}")
        raise Exception(f"Failed to query document: {str(e)}")
