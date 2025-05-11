from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(255), nullable=False)
    index_id = db.Column(db.String(255), nullable=False)  # ID for LlamaIndex
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Document {self.filename}>"
