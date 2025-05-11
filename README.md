# PDF Intelligence

A powerful web application that enables users to upload PDF documents and ask questions about their content using advanced AI-powered document understanding.

## Features

- 📄 PDF Document Upload
- 🔍 Natural Language Question Answering
- 💾 Persistent Storage of Documents
- 🎯 Accurate Document Analysis
- 🌐 Web-based Interface

## Technologies Used

- Python 3.11+
- Flask (Web Framework)
- LlamaIndex (Document Processing & QA)
- SQLite (Database)
- HTML/CSS/JavaScript (Frontend)

## Installation

1. Clone the repository:
```bash
git clone <your-repository-url>
cd PdfIntelligence
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# Unix/MacOS
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory and add the following:
```
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your_secret_key_here
```

## Project Structure

```
├── app.py              # Main Flask application
├── models.py           # Database models
├── templates/          # HTML templates
│   ├── base.html      # Base template
│   ├── index.html     # Home page
│   ├── qa.html        # Q&A interface
│   └── upload.html    # Upload interface
├── static/            # Static assets
│   ├── css/          # Stylesheets
│   └── js/           # JavaScript files
├── utils/            # Utility functions
│   ├── llama_index_helper.py  # LlamaIndex integration
│   └── pdf_processor.py       # PDF processing
├── uploads/          # PDF storage
└── storage/          # Vector store storage
```

## Usage

1. Start the Flask application:
```bash
flask run
```

2. Open your web browser and navigate to `http://localhost:5000`

3. Upload a PDF document using the upload interface

4. Navigate to the Q&A interface to ask questions about your uploaded documents

## Development

### Prerequisites

- Python 3.11 or higher
- pip package manager
- Virtual environment (recommended)

### Setting up for Development

1. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

2. Set up pre-commit hooks:
```bash
pre-commit install
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- LlamaIndex for providing the document processing capabilities
- Flask framework for the web application structure
- All contributors who have helped to improve this project

## Support

If you encounter any issues or have questions, please file an issue on the GitHub repository.
