import psycopg2
from sql_queries import create_table_queries, drop_table_queries
import logging
import configparser
import pandas as pd


config = configparser.ConfigParser()
config.read("config/config.ini")
HOST=config['postgres']['host']
DB=config['postgres']['database']
USER=config['postgres']['user']
PWD=config['postgres']['password']

# Configure logging
logging.basicConfig(
    filename='data/logs/create_tables.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def create_database():
    """
    Create job_db database.

    Returns:
        cur (obj): Cursor object for the connection to the job_db database.
        conn (obj): Connection object to the job_db database.
    """
    try:
        # Kết nối tới database mặc định
        conn = psycopg2.connect(
            host=HOST, 
            dbname='postgres',  
            user=USER,  
            password=PWD 
        )
        conn.set_session(autocommit=True)
        cur = conn.cursor()

        # Tạo database job_db
        cur.execute("DROP DATABASE IF EXISTS job_db")
        cur.execute("CREATE DATABASE job_db WITH ENCODING 'utf8' TEMPLATE template0")
        logging.info("Database 'job_db' created successfully.")

        # Đóng kết nối tới database mặc định
        conn.close()

        # Kết nối tới database job_db
        conn = psycopg2.connect(
            host=HOST,  
            dbname='job_db',
            user=USER,  
            password=PWD  
        )
        cur = conn.cursor()

        return cur, conn

    except Exception as e:
        logging.error(f"Error while creating the database: {e}")
        raise


def drop_tables(cur, conn):
    """
    Drop all tables in the retail_orders database.
    """
    try:
        for query in drop_table_queries:
            cur.execute(query)
            conn.commit()
        logging.info("All tables dropped successfully.")
    except Exception as e:
        logging.error(f"Error while dropping tables: {e}")
        raise


def create_tables(cur, conn):
    """
    Create all tables in the retail_orders database.
    """
    try:
        for query in create_table_queries:
            cur.execute(query)
            conn.commit()
        logging.info("All tables created successfully.")
    except Exception as e:
        logging.error(f"Error while creating tables: {e}")
        raise

def insert_cleaned_jobs_data(cur, conn, csv_file):
    """
    Insert data from a CSV file into the cleaned_jobs_data table.

    Args:
        cur (obj): Cursor object for the database connection.
        conn (obj): Connection object to the database.
        csv_file (str): Path to the CSV file containing the data.
    """
    try:
        # Đọc file CSV bằng pandas
        df = pd.read_csv(csv_file)

        # Chèn dữ liệu vào bảng cleaned_jobs_data
        for index, row in df.iterrows():
            cur.execute("""
                INSERT INTO cleaned_jobs_data (
                    title, link, company_name, job_description, skills, location,
                    experience, salary, job_id, job_function, industry, specialization,
                    role, qualification, employment_type, vacancies
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (job_id) DO NOTHING
            """, (
                row['Title'], row['Link'], row['Company Name'], row['Job Description'],
                row['Skills'], row['Location'], row['Experience'], row['Salary'],
                row['Job ID'], row['Job Function'], row['Industry'], row['Specialization'],
                row['Role'], row['Qualification'], row['Employment Type'], row['Vacancies']
            ))
        conn.commit()
        logging.info(f"Data from {csv_file} loaded successfully into 'cleaned_jobs_data'.")
    except Exception as e:
        logging.error(f"Error while inserting data into 'cleaned_jobs_data': {e}")
        raise


def main():
    """
    Main function to set up the database, create tables, and load data.
    """
    try:
        # Tạo database và kết nối
        cur, conn = create_database()

        # Xóa bảng nếu tồn tại và tạo lại bảng
        drop_tables(cur, conn)
        create_tables(cur, conn)

        # Đường dẫn tới file CSV
        csv_file = "data/processed/cleaned_jobs_data.csv"

        # Chèn dữ liệu từ file CSV vào bảng cleaned_jobs_data
        insert_cleaned_jobs_data(cur, conn, csv_file)

        # Đóng kết nối
        conn.close()
        logging.info("Database setup and data insertion completed successfully.")
    except Exception as e:
        logging.error(f"Error in main execution: {e}")


if __name__ == "__main__":
    main()