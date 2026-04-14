import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24).hex())
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///catering.db')

    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql+psycopg2://", 1)

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300
    }

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    STOCK_WARNING_THRESHOLD = 10