import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# ======= Logging Configuration =======
log_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'logs')
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, f"cleaning_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def log_process(message):
    """Log the data processing steps."""
    logging.info(message)

# ======= 1. Load Data =======
def load_data(file_path):
    """Load data from a CSV file.

    Args:
        file_path (str): Path to the CSV file.

    Returns:
        pd.DataFrame: DataFrame containing the data.
    """
    try:
        log_process(f"Loading data from {file_path}")
        return pd.read_csv(file_path)
    except FileNotFoundError:
        log_process(f"File not found: {file_path}")
        return pd.DataFrame()
    except Exception as e:
        log_process(f"Error loading file {file_path}: {e}")
        return pd.DataFrame()

# ======= 2. Handle Missing Data =======
def drop_nan_job_id(df):
    """Remove rows with missing 'Job ID'."""
    log_process("Dropping rows with missing 'Job ID'")
    return df.dropna(subset=["Job ID"])

def fill_column_nan(df, column_name, default_value):
    """Fill missing values in a specific column with a default value.

    Args:
        df (pd.DataFrame): Input DataFrame.
        column_name (str): Column to process.
        default_value: Default value to fill in.

    Returns:
        pd.DataFrame: Processed DataFrame.
    """
    if column_name in df.columns:
        log_process(f"Filling missing values in column '{column_name}' with '{default_value}'")
        df[column_name] = df[column_name].fillna(default_value)
    return df

def drop_column_hiring_location(df):
    """Remove the 'Hiring Location' column if it exists."""
    log_process("Dropping column 'Hiring Location' if it exists")
    return df.drop(columns=['Hiring Location'], errors='ignore')

# ======= 3. Clean Data =======
def clean_column(df, column_name, clean_func):
    """Clean a specific column using a cleaning function.

    Args:
        df (pd.DataFrame): Input DataFrame.
        column_name (str): Column to clean.
        clean_func (function): Cleaning function to apply.

    Returns:
        pd.DataFrame: Processed DataFrame.
    """
    if column_name in df.columns:
        log_process(f"Cleaning column '{column_name}'")
        df[column_name] = df[column_name].apply(clean_func)
    return df

def clean_qualification(qual):
    """Clean the 'Qualification' column."""
    qual = qual.replace('\r\n', ' ').replace('\n', ' ').strip()
    qual = ' '.join(qual.split())
    qualifications = [q.strip() for q in qual.split(',')]
    unique_qualifications = sorted(set(qualifications))
    return ', '.join(unique_qualifications)

def clean_title(title):
    """Clean the 'Title' column."""
    title = title.replace('"', '').replace('|', '').strip()
    title = re.sub(r'\s+', ' ', title).strip()
    title = title.title()
    return title

def clean_company_name(name):
    """Clean the 'Company Name' column."""
    name = re.sub(r'[^\w\s&/-]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    name = name.title()
    return name

def clean_job_id_column(df):
    """Clean the 'Job ID' column."""
    log_process("Cleaning 'Job ID' column")
    df['Job ID'] = df['Job ID'].str.extract(r'(\d+)')
    return df

def clean_experience_column(df):
    """Clean the 'Experience' column."""
    log_process("Cleaning 'Experience' column")
    df['Experience'] = (
        df['Experience']
        .str.replace(r'[\n\t]+', '', regex=True)
        .str.replace(r'\s+-\s+', '-', regex=True)
        .str.strip()
    )
    return df

# ======= 4. Fetch Data from Links =======
def fetch_from_links(df, column_name, element_class, target_column):
    """Fetch data from links and populate the target column.

    Args:
        df (pd.DataFrame): Input DataFrame.
        column_name (str): Column containing links.
        element_class (str): HTML class of the element to fetch.
        target_column (str): Column to populate with fetched data.

    Returns:
        pd.DataFrame: Processed DataFrame.
    """
    def fetch_data(index, link):
        try:
            log_process(f"Fetching data from link: {link}")
            response = requests.get(link)
            if response.status_code != 200:
                log_process(f"Failed to fetch {link}: Status code {response.status_code}")
                return None

            soup = BeautifulSoup(response.content, 'html.parser')
            element = soup.find('div', class_=element_class)
            if element:
                fetched_data = element.find('span').text.strip()
                log_process(f"Data fetched from {link}: {fetched_data}")
                return fetched_data

            log_process(f"No relevant data found for {link}")
            return None
        except Exception as e:
            log_process(f"Error fetching data from {link}: {e}")
            return None

    links_with_nan = df[df[target_column].isnull()][column_name]
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(lambda args: fetch_data(*args), links_with_nan.items()))

    for idx, result in zip(links_with_nan.index, results):
        if result:
            df.at[idx, target_column] = result

    return df

# ======= 5. Infer Job Roles =======
def infer_role(title, specialization, job_function):
    """Infer the job role based on title, specialization, and job function."""
    title = (title or "").lower()
    specialization = (specialization or "").lower()
    job_function = (job_function or "").lower()

    if "qa qc engineer" in title or "quality assurance" in title or "testing" in title:
        return "Software Quality Assurance Engineer"
    if "software engineer" in title or "software developer" in title:
        return "Software Developer/ Programmer"
    if "data engineer" in title or "data science" in title or "data scientist" in title:
        return "Data Scientist"
    if "project manager" in title or "delivery manager" in title or "it project manager" in title:
        return "Project Manager"
    if "consultant" in title or "sap" in title:
        return "Consultant"
    if "internship" in title or "intern" in title or "fresher" in title:
        return "Intern"
    if "web designer" in title or "graphic designer" in title or "visualiser" in title:
        return "Web Designer"
    if "architect" in title:
        return "Technical Architect"
    if "administrator" in title or "system admin" in title:
        return "System Administrator"
    if "marketing" in title:
        return "Marketing Executive"
    if "hr" in title:
        return "HR Executive"

    if "quality assurance/testing" in specialization:
        return "Software Quality Assurance Engineer"
    if "application programming" in specialization:
        return "Software Developer/ Programmer"
    if "graphic designing" in specialization or "web designing" in specialization:
        return "Web Designer"
    if "database administration" in specialization:
        return "Database Administrator (DBA)"
    if "internet/e-commerce" in specialization:
        return "Frontend Developer"
    if "erp/crm" in specialization:
        return "ERP/CRM Analyst"

    if "project leader" in job_function or "project manager" in job_function:
        return "Project Manager"
    if "business/systems analysis" in job_function:
        return "Business Analyst"
    if "client server" in job_function:
        return "System Analyst"
    if "network planning" in job_function:
        return "Network Engineer"
    if "administration" in job_function:
        return "Administration Manager"

    return "Other IT Role"

def infer_roles(df):
    """Infer job roles for rows with missing values in the 'Role' column.

    Args:
        df (pd.DataFrame): Input DataFrame.

    Returns:
        pd.DataFrame: Processed DataFrame.
    """
    log_process("Inferring roles for missing values in 'Role' column")
    df.loc[df['Role'].isna(), 'Role'] = df.loc[df['Role'].isna()].apply(
        lambda row: infer_role(row['Title'], row['Specialization'], row['Job Function']),
        axis=1
    )
    return df

# ======= 6. Save Data =======
def save_data(df, output_path):
    """Save the DataFrame to a CSV file.

    Args:
        df (pd.DataFrame): DataFrame to save.
        output_path (str): Path to the output CSV file.

    Returns:
        None
    """
    try:
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        log_process(f"Data successfully saved to {output_path}")
    except Exception as e:
        log_process(f"Error saving data to {output_path}: {e}")

# ======= 7. Execute Cleaning Process =======
def clean_data(file_path, output_path):
    """Perform the entire data cleaning process.

    Args:
        file_path (str): Path to the input data file.
        output_path (str): Path to the output data file.

    Returns:
        None
    """
    log_process("Starting data cleaning process")

    # 1. Load data
    log_process(f"Loading data from file: {file_path}")
    df = load_data(file_path)
    if df.empty:
        log_process("No data to clean. Exiting.")
        return

    # 2. Handle missing data
    log_process("Handling missing data")
    df = drop_nan_job_id(df)
    log_process(f"Dropped rows with missing 'Job ID': {len(df)} rows remaining")
    df = drop_column_hiring_location(df)
    log_process("'Hiring Location' column dropped (if present)")
    df = fill_column_nan(df, 'Salary', "Not Disclosed")
    log_process("Missing 'Salary' values filled with 'Not Disclosed'")
    df = fill_column_nan(df, 'Qualification', "Any Graduate")
    log_process("Missing 'Qualification' values filled with 'Any Graduate'")
    df = fill_column_nan(df, 'Vacancies', 1)
    log_process("Missing 'Vacancies' values filled with 1")

    # 3. Clean and normalize data
    log_process("Cleaning and normalizing data")
    df = clean_column(df, 'Qualification', clean_qualification)
    log_process("'Qualification' column cleaned and normalized")
    df = clean_column(df, 'Title', clean_title)
    log_process("'Title' column cleaned and normalized")
    df = clean_column(df, 'Company Name', clean_company_name)
    log_process("'Company Name' column cleaned and normalized")
    df = clean_job_id_column(df)
    log_process("'Job ID' column cleaned")
    df = clean_experience_column(df)
    log_process("'Experience' column cleaned")

    # 4. Fetch data from links
    log_process("Fetching additional data from job links")
    df = fetch_from_links(df, 'Link', 'job-skills', 'Skills')
    log_process("Fetched missing 'Skills' data from job links")
    df = fetch_from_links(df, 'Link', 'location-text__ mt-8', 'Location')
    log_process("Fetched missing 'Location' data from job links")

    # 5. Infer job roles
    log_process("Inferring job roles for missing values")
    df = infer_roles(df)
    log_process("Job roles inferred successfully")

    # 6. Save cleaned data
    log_process(f"Saving cleaned data to file: {output_path}")
    save_data(df, output_path)
    log_process("Data cleaning process completed successfully")


# ======= 7. Chạy chương trình =======
if __name__ == "__main__":
    input_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'jobs_data_with_details.csv')
    output_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed', 'cleaned_jobs_data.csv')
    clean_data(input_file, output_file)
