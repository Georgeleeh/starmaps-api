from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

app.config.from_object(Config)

db = SQLAlchemy(app)

from app import routes

@app.template_filter()
def format_datetime(value, format='full'):
    if value is None:
        return None
        
    if format == 'full':
        format="%Y-%m-%d %H:%M"
    elif format == 'date':
        format="%Y-%m-%d"
    elif format == 'time':
        format="%H:%M"
    return datetime.fromtimestamp(value).strftime(format)