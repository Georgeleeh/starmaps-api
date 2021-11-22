from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

app.config.from_object(Config)

db = SQLAlchemy(app)

from app import routes