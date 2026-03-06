"""
Script to run database migrations
"""
import subprocess
import sys
import os

def run_migrations():
    """
    Run database migrations using Alembic
    """
    try:
        # Generate a new migration
        print("Generating new migration...")
        result = subprocess.run([
            sys.executable, "-m", "alembic", "revision", "--autogenerate", "-m", "Initial migration"
        ], cwd=os.path.dirname(os.path.abspath(__file__)), capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error generating migration: {result.stderr}")
            return False
        
        print("Migration generated successfully.")
        
        # Run the migration
        print("Running migration...")
        result = subprocess.run([
            sys.executable, "-m", "alembic", "upgrade", "head"
        ], cwd=os.path.dirname(os.path.abspath(__file__)), capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error running migration: {result.stderr}")
            return False
        
        print("Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error running migrations: {str(e)}")
        return False


if __name__ == "__main__":
    success = run_migrations()
    if not success:
        sys.exit(1)