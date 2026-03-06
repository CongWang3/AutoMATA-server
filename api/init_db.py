"""
Database initialization script
Creates all tables based on the defined models
"""
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database import engine, init_db
from models.training_job import TrainingJob
from models.dataset import Dataset
from models.ml_model import MLModel


def create_tables():
    """
    Create all tables in the database
    """
    print("Creating database tables...")
    
    # Create all tables
    init_db()
    
    print("Database tables created successfully!")


if __name__ == "__main__":
    create_tables()