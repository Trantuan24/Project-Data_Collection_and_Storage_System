import unittest
import pandas as pd
import logging
from src.data_cleaning import *

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TestDataCleaning(unittest.TestCase):
    """
    Unit tests for data cleaning functions.
    """

    def setUp(self):
        """
        Set up sample data for testing.
        """
        logging.info("Setting up sample data for tests.")
        self.sample_data = pd.DataFrame({
            'Job ID': ['123', '456', None, '789'],
            'Title': ['Software Engineer', 'Data Scientist', None, 'Project Manager'],
            'Qualification': ['B.Tech, M.Tech', None, 'B.Sc', 'B.Tech, B.Tech'],
            'Company Name': ['Company A', 'Company B', None, 'Company D'],
            'Salary': [None, '10 LPA', None, '15 LPA'],
            'Hiring Location': ['Location A', 'Location B', 'Location C', 'Location D'],
            'Experience': ['2 - 4 years', None, '1 year', '5 - 7 years'],
            'Role': [None, None, None, None],
            'Specialization': ['Software Engineering', 'Data Science', None, 'Management'],
            'Job Function': ['Development', 'Analysis', None, 'Project Management']
        })

    def test_drop_nan_job_id(self):
        """
        Test removing rows with NaN values in the 'Job ID' column.
        """
        logging.info("Testing drop_nan_job_id function.")
        cleaned_data = drop_nan_job_id(self.sample_data)
        self.assertEqual(len(cleaned_data), 3)  # Only 3 rows remain
        self.assertNotIn(None, cleaned_data['Job ID'].values)

    def test_fill_column_nan(self):
        """
        Test filling NaN values in a column with a default value.
        """
        logging.info("Testing fill_column_nan function.")
        filled_data = fill_column_nan(self.sample_data, 'Salary', 'Not Disclosed')
        self.assertNotIn(None, filled_data['Salary'].values)
        self.assertIn('Not Disclosed', filled_data['Salary'].values)

    def test_drop_column_hiring_location(self):
        """
        Test dropping the 'Hiring Location' column.
        """
        logging.info("Testing drop_column_hiring_location function.")
        cleaned_data = drop_column_hiring_location(self.sample_data)
        self.assertNotIn('Hiring Location', cleaned_data.columns)

    def test_clean_column(self):
        """
        Test cleaning a specific column using a cleaning function.
        """
        logging.info("Testing clean_column function.")
        self.sample_data['Qualification'] = self.sample_data['Qualification'].fillna("")
        cleaned_data = clean_column(self.sample_data, 'Qualification', clean_qualification)
        self.assertIn('B.Sc', cleaned_data['Qualification'].values)
        self.assertNotIn('\r\n', cleaned_data['Qualification'].values)

    def test_clean_qualification(self):
        """
        Test cleaning values in the 'Qualification' column.
        """
        logging.info("Testing clean_qualification function.")
        result = clean_qualification('')  # Replace None with an empty string
        self.assertEqual(result, '')
        result = clean_qualification('B.Tech, M.Tech, B.Tech')
        self.assertEqual(result, 'B.Tech, M.Tech')

    def test_clean_title(self):
        """
        Test cleaning values in the 'Title' column.
        """
        logging.info("Testing clean_title function.")
        result = clean_title('software engineer | developer')
        self.assertEqual(result, 'Software Engineer Developer')

    def test_clean_company_name(self):
        """
        Test cleaning values in the 'Company Name' column.
        """
        logging.info("Testing clean_company_name function.")
        result = clean_company_name('')  # Replace None with an empty string
        self.assertEqual(result, '')
        result = clean_company_name('Company@Name#Inc!')
        self.assertEqual(result, 'Companynameinc')

    def test_clean_job_id_column(self):
        """
        Test cleaning the 'Job ID' column to ensure numeric values.
        """
        logging.info("Testing clean_job_id_column function.")
        cleaned_data = clean_job_id_column(self.sample_data)
        self.assertTrue(cleaned_data['Job ID'].str.isnumeric().all())

    def test_clean_experience_column(self):
        """
        Test cleaning the 'Experience' column.
        """
        logging.info("Testing clean_experience_column function.")
        cleaned_data = clean_experience_column(self.sample_data)
        self.assertNotIn('\n', cleaned_data['Experience'].values)
        self.assertNotIn('\t', cleaned_data['Experience'].values)

    def test_infer_roles(self):
        """
        Test inferring roles based on existing data.
        """
        logging.info("Testing infer_roles function.")
        inferred_data = infer_roles(self.sample_data)
        self.assertIn('Software Developer/ Programmer', inferred_data['Role'].values)
        self.assertIn('Data Scientist', inferred_data['Role'].values)

    def tearDown(self):
        """
        Clean up after running tests.
        """
        logging.info("Tearing down after tests.")

if __name__ == '__main__':
    logging.info("Starting unit tests.")
    unittest.main()
