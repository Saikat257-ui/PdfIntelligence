import os
from dotenv import load_dotenv
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session
from werkzeug.utils import secure_filename
import uuid
from models import db, Document
from utils.pdf_processor import extract_text_from_pdf
from utils.llama_index_helper import process_document, query_document

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET",
                                "pdf_qa_application_secret_key")

# Configure session to ensure it works correctly
app.config['SESSION_COOKIE_NAME'] = 'pdf_qa_session'
app.config[
    'SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
app.config['SESSION_PERMANENT'] = True

# Configure SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///pdf_qa.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             'uploads')
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Ensure instance folder has correct permissions
os.makedirs('instance', exist_ok=True)
os.chmod('instance', 0o777)

# Create database tables
with app.app_context():
    db.create_all()
    # Ensure database file has correct permissions
    os.chmod('instance/pdf_qa.db', 0o666)


# Before request handler to ensure session works correctly
@app.before_request
def before_request():
    # Make sure session is initialized for all requests
    if session.get('initialized') != True:
        session['initialized'] = True
        session.modified = True
        logger.debug("Session initialized")


def allowed_file(filename):
    return '.' in filename and filename.rsplit(
        '.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)

        file = request.files['file']

        # If user does not select file, browser submits an empty file
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            try:
                # Generate a unique filename
                original_filename = secure_filename(file.filename)
                file_extension = original_filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'],
                                        unique_filename)

                # Save the file
                file.save(filepath)

                # Extract text from PDF
                extracted_text = extract_text_from_pdf(filepath)

                # Process document with LlamaIndex
                index_id = process_document(extracted_text, unique_filename)

                # Save document metadata to database
                new_document = Document(filename=original_filename,
                                        filepath=filepath,
                                        index_id=index_id,
                                        upload_date=datetime.utcnow())
                db.session.add(new_document)
                db.session.commit()

                # Store document ID in session
                session['current_document_id'] = new_document.id

                flash('File uploaded successfully!', 'success')
                return redirect(url_for('qa', document_id=new_document.id))

            except Exception as e:
                logger.error(f"Error during file upload: {str(e)}")
                flash(f'Error processing file: {str(e)}', 'error')
                return redirect(request.url)
        else:
            flash('File type not allowed. Please upload a PDF file.', 'error')
            return redirect(request.url)

    # GET request - show upload form
    return render_template('upload.html')


@app.route('/qa', methods=['GET'])
@app.route('/qa/<int:document_id>', methods=['GET'])
def qa(document_id=None):
    logger.debug(
        f"Accessing QA route, document_id: {document_id}, session: {session}")

    # Try to get document ID from URL parameter first, then session
    if document_id is None and 'current_document_id' in session:
        document_id = session.get('current_document_id')
        logger.debug(f"Document ID from session: {document_id}")

    # If still no document ID, redirect to upload
    if document_id is None:
        logger.warning("No document ID in URL or session")
        flash('Please upload or select a document first', 'warning')
        return redirect(url_for('upload'))

    # Look up the document
    document = Document.query.get(document_id)

    if not document:
        logger.error(f"Document not found in database: {document_id}")
        flash('Document not found. Please upload a new document.', 'error')
        return redirect(url_for('upload'))

    # Always update session with current document ID
    session['current_document_id'] = document_id
    session.modified = True

    logger.debug(f"Rendering QA page with document: {document.filename}")
    return render_template('qa.html', document=document)


@app.route('/api/ask', methods=['POST'])
@app.route('/api/ask/<int:document_id>', methods=['POST'])
def ask_question(document_id=None):
    # Get document_id from multiple sources (URL param, request data, session)
    if document_id is None:
        # Try to get from request data
        data = request.json or {}
        document_id = data.get('document_id')

        # If still not found, try session
        if document_id is None and 'current_document_id' in session:
            document_id = session.get('current_document_id')

    if document_id is None:
        return jsonify(
            {'error':
             'No document selected. Please select a document first.'}), 400

    # Get question from request data
    data = request.json or {}
    question = data.get('question')

    if not question:
        return jsonify({'error': 'No question provided'}), 400

    # Look up document
    document = Document.query.get(document_id)

    if not document:
        return jsonify({'error':
                        f'Document with ID {document_id} not found'}), 404

    # Always update session with current document
    session['current_document_id'] = document_id
    session.modified = True

    try:
        # Query the document using LlamaIndex
        answer = query_document(document.index_id, question)
        return jsonify({
            'answer': answer,
            'document_id': document_id,
            'document_name': document.filename
        })
    except Exception as e:
        logger.error(f"Error querying document: {str(e)}")
        return jsonify({'error': f'Error processing question: {str(e)}'}), 500


@app.route('/api/documents', methods=['GET'])
def get_documents():
    documents = Document.query.order_by(Document.upload_date.desc()).all()
    docs_list = [{
        'id': doc.id,
        'filename': doc.filename,
        'upload_date': doc.upload_date.strftime('%Y-%m-%d %H:%M:%S')
    } for doc in documents]
    return jsonify({'documents': docs_list})


@app.route('/api/select-document/<int:document_id>', methods=['POST'])
def select_document(document_id):
    logger.debug(
        f"Selecting document with ID: {document_id}, session before: {session}"
    )
    document = Document.query.get(document_id)

    if not document:
        logger.error(f"Document not found with ID: {document_id}")
        if request.content_type and 'application/json' in request.content_type:
            return jsonify({'error': 'Document not found'}), 404
        else:
            flash('Document not found', 'error')
            return redirect(url_for('upload'))

    # Store document ID in session
    session.clear()  # Clear any existing session data
    session['current_document_id'] = document_id
    session['initialized'] = True
    # Force the session to be saved
    session.modified = True

    logger.debug(
        f"Document selected successfully: {document.filename}, session after: {session}"
    )

    # Check if this is a form submission (not AJAX)
    if request.form.get('selected') == 'true':
        flash(f'Selected document: {document.filename}', 'success')
        # Use direct URL parameter approach
        return redirect(url_for('qa', document_id=document_id))
    else:
        # API response for AJAX calls with redirect URL that includes document ID
        return jsonify({
            'success': True,
            'document': document.filename,
            'redirect_url': url_for('qa', document_id=document_id)
        })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
