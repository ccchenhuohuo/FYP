"""
Database initialization and update script

This script provides two main functions:
1. Initialize database:
   - Delete existing database (if exists)
   - Create a new empty database
   - Create all tables corresponding to models
   - Add default admin account
2. Update stock data:
   - Download latest stock data from yfinance
   - Update stock data in the database
"""
import pymysql
import os
import sys

# Adjust Python path to include project root for sibling imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from flask import Flask
from config import DB_CONFIG, SECRET_KEY, SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS, TECH_TICKERS
import time
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize database"""
    # Connect to MySQL server (without specifying database)
    print("Connecting to MySQL server...")
    conn = pymysql.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        charset='utf8mb4'
    )
    
    # Create cursor object
    cursor = conn.cursor()
    
    try:
        # Delete database (if exists)
        print(f"Deleting database {DB_CONFIG['database']} (if exists)...")
        cursor.execute(f"DROP DATABASE IF EXISTS {DB_CONFIG['database']}")
        
        # Create database
        print(f"Creating new database {DB_CONFIG['database']}...")
        cursor.execute(f"CREATE DATABASE {DB_CONFIG['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        
        print("Database created successfully!")
        return True
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False
    finally:
        # Close cursor and connection
        cursor.close()
        conn.close()

def create_tables():
    """Create tables and add default data"""
    print("Creating Flask application...")
    app = Flask(__name__)
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
    
    # Import models and initialize database
    from models import init_db, db
    
    print("Initializing database connection...")
    init_db(app)
    
    with app.app_context():
        # Create all tables
        print("Creating all tables...")
        db.create_all()
        
        print("Tables created successfully!")
        print("Database initialized successfully!")
    
    return app

def update_stock_data(recreate_app=False):
    """
    Download stock data from yfinance and update database
    
    Parameters:
        recreate_app (bool): whether to recreate Flask application
                            if called from initialize database process, no need to recreate
    """
    try:
        # If need to recreate application (independent update data)
        if recreate_app:
            app = Flask(__name__)
            app.config['SECRET_KEY'] = SECRET_KEY
            app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
            app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
            
            # Import models and initialize database
            from models import init_db
            init_db(app)
        
        # Import stock_data module from utils
        from utils.stock_data import run_stock_data_collection
        
        print("Starting to download stock data from yfinance...")
        # Run stock data collection and storage process
        run_stock_data_collection()
        
        print("All stock data downloaded and updated!")
        return True
    except ImportError as e:
        print(f"Error: cannot import stock_data module: {e}")
        print("Please ensure stock_data.py file exists in utils directory")
        return False
    except Exception as e:
        print(f"Error downloading stock data: {e}")
        return False

def main():
    print("=" * 60)
    print("Database initialization and update tool")
    print("=" * 60)
    
    # Ask if initialize database
    init_db_choice = input("Do you need to initialize database? This will delete all existing data! (y/n): ").strip().lower()
    
    if init_db_choice == 'y':
        print("\nStarting to initialize database...")
        
        # Initialize database
        if init_database():
            # Create tables
            app = create_tables()
            
            # Ask if download stock data
            download_data = input("\nDo you need to download stock data from yfinance? (y/n): ").strip().lower()
            
            if download_data == 'y':
                update_stock_data(recreate_app=False)
            else:
                print("Skipping download stock data.")
                
            print("\nDatabase initialized successfully!")
            print("Now you can run the application.")
        else:
            print("Database initialization failed, exiting program.")
            sys.exit(1)
    else:
        # Ask if update stock data
        update_data = input("\nDo you need to update stock data in local database? (y/n): ").strip().lower()
        
        if update_data == 'y':
            print("\nStarting to update stock data...")
            if update_stock_data(recreate_app=True):
                print("\nStock data updated successfully!")
            else:
                print("\nStock data update failed!")
        else:
            print("\nOperation cancelled. No changes made.")

if __name__ == "__main__":
    main() 