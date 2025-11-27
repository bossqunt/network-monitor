"""
Database setup utility
Run this script to create the database and tables
"""
import mysql.connector
from mysql.connector import Error
import sys

def setup_database():
    """Create database and tables"""
    print("=" * 60)
    print("Network Monitor - Database Setup")
    print("=" * 60)
    
    # Read schema file
    try:
        with open('schema.sql', 'r') as f:
            schema = f.read()
    except FileNotFoundError:
        print("Error: schema.sql not found")
        return False
    
    # Connect to MySQL (without database selected)
    try:
        connection = mysql.connector.connect(
            host='127.0.0.1',
            user='root',
            password='unknown'
        )
        
        if connection.is_connected():
            print("✓ Connected to MySQL server")
            
            cursor = connection.cursor()
            
            # Execute each SQL statement
            for statement in schema.split(';'):
                statement = statement.strip()
                if statement:
                    try:
                        cursor.execute(statement)
                        print(f"✓ Executed: {statement[:50]}...")
                    except Error as e:
                        print(f"Warning: {e}")
            
            connection.commit()
            cursor.close()
            connection.close()
            
            print("=" * 60)
            print("✓ Database setup completed successfully!")
            print("=" * 60)
            return True
            
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        print("\nPlease ensure:")
        print("  1. MySQL is running on 127.0.0.1")
        print("  2. Username is 'root' with password 'unknown'")
        print("  3. Or update credentials in config.yaml")
        return False

if __name__ == '__main__':
    success = setup_database()
    sys.exit(0 if success else 1)
