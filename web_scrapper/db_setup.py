import psycopg2
import os

# PostgreSQL configuration (loaded from environment variables)
pg_config = {
    'dbname': os.getenv('DB_NAME', 'default_dbname'),
    'user': os.getenv('DB_USER', 'default_user'),
    'password': os.getenv('DB_PASSWORD', 'default_password'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432')
}

def setup_database():
    connection = None
    try:
        # Connect to the PostgreSQL database
        connection = psycopg2.connect(**pg_config)
        cursor = connection.cursor()

        # Create table with SSH identifier and URL
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ScrapedData (
                id SERIAL PRIMARY KEY,
                ssh_identifier VARCHAR(255),
                url VARCHAR(500),
                type VARCHAR(255),
                text TEXT
            );
        """)

        # Commit the changes to the database
        connection.commit()
        print("Database setup completed successfully.")

    except psycopg2.DatabaseError as e:
        print(f"An error occurred while setting up the database: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("Database connection closed.")

if __name__ == "__main__":
    setup_database()
