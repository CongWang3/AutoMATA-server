"""
Test script to verify database connection and basic functionality
"""
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database import engine, init_db
from sqlalchemy import text


def test_database_connection():
    """
    Test database connection
    """
    try:
        # Test connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✅ Database connection successful!")
            
            # Check if tables exist (SQLite compatible)
            try:
                result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
                tables = [row[0] for row in result]
                print(f"📋 Existing tables: {tables}")
            except Exception as e:
                print(f"⚠️  Could not list tables: {str(e)}")
            
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False


def create_sample_data():
    """
    Create sample data for testing
    """
    try:
        from sqlalchemy.orm import Session
        from models.user import User
        from models.training_job import TrainingJob
        from services.training_job_service import create_training_task
        from services.user_service import create_user, get_user_by_email
        import json
        
        with Session(engine) as session:
            # Check if user already exists
            existing_user = get_user_by_email(session, "test@example.com")
            if existing_user:
                print(f"✅ User already exists with ID: {existing_user.id}")
                sample_user = existing_user
            else:
                # Create a sample user
                from schemas.user import UserCreate
                user_create = UserCreate(
                    username="testuser",
                    email="test@example.com",
                    password="testpassword",
                    is_active=True
                )
                sample_user = create_user(session, user_create)
                print(f"✅ Created sample user with ID: {sample_user.id}")
            
            # Check if training task already exists
            from models.training_job import TrainingJob
            existing_task = session.query(TrainingJob).filter(
                TrainingJob.task_name == "Sample Training Task"
            ).first()
            
            if existing_task:
                print(f"✅ Training task already exists with ID: {existing_task.id}")
            else:
                # Create a sample training task
                from schemas.training_job import TrainingJobCreate
                task_create = TrainingJobCreate(
                    task_name="Sample Training Task",
                    model_type="supervised",
                    language="python",
                    parameters=json.dumps({"epochs": 100, "batch_size": 32}),
                    dataset_path="/path/to/dataset",
                    created_by=sample_user.id
                )
                sample_task = create_training_task(session, task_create)
                print(f"✅ Created sample training task with ID: {sample_task.id}")
            
        return True
    except Exception as e:
        print(f"❌ Failed to create sample data: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🧪 Testing AutoMATA Training Task Management System")
    print("=" * 50)
    
    # Test database connection
    if test_database_connection():
        # Initialize database tables
        print("\n🔧 Initializing database tables...")
        init_db()
        print("✅ Database tables initialized!")
        
        # Create sample data
        print("\n📝 Creating sample data...")
        if create_sample_data():
            print("✅ Sample data created successfully!")
        else:
            print("⚠️  Failed to create sample data")
    else:
        print("❌ Cannot proceed without database connection")
        sys.exit(1)
    
    print("\n🎉 All tests completed!")