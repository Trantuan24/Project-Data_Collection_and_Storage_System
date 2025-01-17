import unittest
import os
import tempfile
import pandas as pd
from unittest.mock import patch
from src.data_collection import JobScraper  

class TestJobScraper(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        Set up an instance of JobScraper and create temporary files for testing.
        """
        cls.base_url = "https://www.timesjobs.com/jobfunction/it-software-jobs/&sequence={page}&startPage=1"
        cls.max_pages = 2  # Use a small value for quick testing
        cls.scraper = JobScraper(cls.base_url, cls.max_pages)

        # Use temporary files for CSV and log output
        cls.output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv").name
        cls.failed_links_file = tempfile.NamedTemporaryFile(delete=False, suffix=".log").name

        # Update file paths in the scraper instance
        cls.scraper.output_file = cls.output_file
        cls.scraper.failed_links_file = cls.failed_links_file

    @classmethod
    def tearDownClass(cls):
        """
        Clean up temporary files after testing.
        """
        if os.path.exists(cls.output_file):
            os.remove(cls.output_file)
        if os.path.exists(cls.failed_links_file):
            os.remove(cls.failed_links_file)

    @patch('src.data_collection.requests.get')
    def test_scrape_page(self, mock_get):
        """
        Test the scrape_page method with mocked data.
        """
        # Mock HTML response
        mock_html = '''
        <html>
            <body>
                <ul class="joblist">
                    <li class="clearfix joblistli">
                        <a href="https://example.com/job1">Test Job 1</a>
                        <h3 class="joblist-comp-name">Test Company 1</h3>
                        <li class="job-description__">Job Description 1</li>
                        <li class="key-skills__"><a>Python</a>, <a>SQL</a></li>
                        <li class="srp-zindex location-tru">Remote</li>
                    </li>
                </ul>
            </body>
        </html>
        '''
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = mock_html

        url = self.base_url.format(page=1)
        data = self.scraper.scrape_page(url, 1)

        self.assertIsInstance(data, dict)
        self.assertIn('Title', data)
        self.assertIn('Link', data)
        self.assertEqual(data['Title'][0], "Test Job 1")
        self.assertEqual(data['Company Name'][0], "Test Company 1")
        self.assertEqual(data['Skills'][0], "Python, SQL")
        self.assertEqual(data['Location'][0], "Remote")

    @patch('src.data_collection.requests.get')
    def test_scrape_job_details(self, mock_get):
        """
        Test the scrape_job_details method with mocked data.
        """
        # Mock HTML response
        mock_html = '''
        <html>
            <body>
                <div class="jd-jobid">12345</div>
                <ul id="applyFlowHideDetails_1">
                    <li class="clearfix">
                        <label>Employment Type:</label>
                        <span class="basic-info-dtl">Full Time</span>
                    </li>
                    <li class="clearfix">
                        <label>Location:</label>
                        <span class="basic-info-dtl">Remote</span>
                    </li>
                </ul>
            </body>
        </html>
        '''
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = mock_html

        sample_link = "https://example.com/job1"
        details = self.scraper.scrape_job_details(sample_link)

        self.assertIsInstance(details, dict)
        self.assertIn('Job ID', details)
        self.assertEqual(details['Job ID'], "12345")
        self.assertEqual(details['Employment Type'], "Full Time")
        self.assertEqual(details['Location'], "Remote")

    def test_save_to_csv(self):
        """
        Test the save_to_csv method using a temporary file.
        """
        test_data = pd.DataFrame({
            'Title': ['Test Job'],
            'Link': ['https://example.com/job'],
            'Company Name': ['Test Company'],
            'Skills': ['Python, SQL'],
            'Location': ['Remote'],
        })

        self.scraper.save_to_csv(test_data)

        # Check if the file exists and contains the correct data
        self.assertTrue(os.path.exists(self.output_file))
        saved_data = pd.read_csv(self.output_file)
        self.assertEqual(len(saved_data), len(test_data), "Data saved to CSV does not match the input data.")

    def test_failed_links_logging(self):
        """
        Test logging of failed links using a temporary log file.
        """
        failed_link = "https://example.com/failed-link"
        self.scraper.save_failed_link(failed_link)

        # Check if the log file exists and contains the failed link
        self.assertTrue(os.path.exists(self.failed_links_file))
        with open(self.failed_links_file, 'r') as f:
            failed_links = f.read()
        self.assertIn(failed_link, failed_links)

if __name__ == '__main__':
    unittest.main()
