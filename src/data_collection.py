import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

class JobScraper:
    def __init__(self, base_url, max_pages):
        """
        Initializes the JobScraper with the base URL and number of pages to scrape.
        :param base_url: URL template with a placeholder for the page number.
        :param max_pages: Number of pages to scrape.
        """
        self.base_url = base_url
        self.max_pages = max_pages
        self.failed_links_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'logs', 'failed_links.txt')
        self.output_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'jobs_data_with_details.csv')

        self.setup_logger()

    def setup_logger(self):
        """
        Sets up the logging configuration.
        """
        log_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'logs')
        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(log_dir, f"scraping_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def scrape_page(self, url, page_number):
        """
        Scrapes job data from a given URL.
        :param url: URL of the job listing page.
        :param page_number: Current page number being processed.
        :return: A dictionary containing job details.
        """
        logging.info(f"Processing page {page_number} from URL: {url}")

        data = {
            'Title': [],
            'Link': [],
            'Company Name': [],
            'Job Description': [],
            'Skills': [],
            'Location': [],
            'Experience': [],
            'Salary': []
        }

        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            job_lists = soup.find_all('ul', class_='joblist')

            for job_list in job_lists:
                jobs = job_list.find_all('li', class_='clearfix joblistli')
                for job in jobs:
                    data['Title'].append(job.find('a').text.strip() if job.find('a') else '')
                    data['Link'].append(job.find('a')['href'] if job.find('a') and job.find('a').has_attr('href') else '')
                    data['Company Name'].append(job.find('h3', class_='joblist-comp-name').text.strip() if job.find('h3', class_='joblist-comp-name') else '')
                    data['Job Description'].append(job.find('li', class_='job-description__').text.strip() if job.find('li', class_='job-description__') else '')

                    skills_tags = job.find('li', class_='key-skills__')
                    skills = ', '.join([tag.text.strip() for tag in skills_tags.find_all('a')]) if skills_tags else ''
                    data['Skills'].append(skills)

                    data['Location'].append(job.find('li', class_='srp-zindex location-tru').text.strip() if job.find('li', class_='srp-zindex location-tru') else '')

                    details = job.find('ul', class_='top-jd-dtl top-jd-dtl-seo clearfix')
                    if details:
                        detail_items = details.find_all('li')
                        data['Experience'].append(detail_items[1].text.strip() if len(detail_items) > 1 else '')
                        data['Salary'].append(detail_items[2].text.strip() if len(detail_items) > 2 else '')
                    else:
                        data['Experience'].append('')
                        data['Salary'].append('')

        except requests.exceptions.RequestException as e:
            logging.error(f"Request error on page {page_number}: {e}")
        except Exception as e:
            logging.error(f"Error processing page {page_number}: {e}")

        return data

    def scrape_job_details(self, link):
        """
        Scrapes detailed job data from a job link.
        :param link: URL of the job detail page.
        :return: A dictionary containing detailed job information.
        """
        logging.info(f"Processing job link: {link}")
        try:
            res = requests.get(link)
            res.raise_for_status()

            soup = BeautifulSoup(res.content, 'html.parser')
            key_details = {}

            job_id_div = soup.find('div', class_='jd-jobid')
            key_details['Job ID'] = job_id_div.text.strip() if job_id_div else None

            details_section = soup.find('ul', id='applyFlowHideDetails_1')
            if details_section:
                detail_items = details_section.find_all('li', class_='clearfix')
                for item in detail_items:
                    label = item.find('label').text.strip(':') if item.find('label') else None
                    value_span = item.find('span', class_='basic-info-dtl')

                    if value_span and value_span.find('ul'):
                        value = ', '.join([li.text.strip() for li in value_span.find_all('li')])
                    else:
                        value = value_span.text.strip() if value_span else None

                    if label and value:
                        key_details[label] = value

            employment_type = soup.find('span', class_='mt-4')
            if employment_type:
                key_details['Employment Type'] = employment_type.text.strip()

            return key_details

        except requests.exceptions.RequestException as e:
            logging.error(f"Request error for job link {link}: {e}")
            self.save_failed_link(link)
            return {}
        except Exception as e:
            logging.error(f"Error processing job link {link}: {e}")
            self.save_failed_link(link)
            return {}

    def save_failed_link(self, link):
        """
        Saves a failed link to a designated file.
        :param link: The link to save.
        """
        os.makedirs(os.path.dirname(self.failed_links_file), exist_ok=True)
        with open(self.failed_links_file, 'a') as f:
            f.write(f"{link}\n")

    def scrape_multiple_pages(self):
        """
        Scrapes job data from multiple pages and includes detailed data from job links.
        :return: A consolidated DataFrame containing job data from all pages.
        """
        all_job_data = []

        for page in range(1, self.max_pages + 1):
            url = self.base_url.format(page=page)
            page_data = self.scrape_page(url, page)
            if page_data and any(page_data['Link']):
                page_df = pd.DataFrame(page_data)

                with ThreadPoolExecutor(max_workers=10) as executor:
                    details_list = list(executor.map(self.scrape_job_details, page_data['Link']))

                details_df = pd.DataFrame(details_list)
                combined_df = pd.concat([page_df, details_df], axis=1)
                all_job_data.append(combined_df)

        if all_job_data:
            return pd.concat(all_job_data, ignore_index=True)
        return pd.DataFrame()

    def save_to_csv(self, dataframe):
        """
        Saves the scraped data to a CSV file.
        :param dataframe: The DataFrame containing the job data.
        """
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        dataframe.to_csv(self.output_file, index=False)
        logging.info(f"Scraping complete. Data saved to {self.output_file}.")

if __name__ == '__main__':
    BASE_URL = "https://www.timesjobs.com/jobfunction/it-software-jobs/&sequence={page}&startPage=1"
    MAX_PAGES = 100

    scraper = JobScraper(BASE_URL, MAX_PAGES)
    logging.info("Starting scraping process.")
    job_dataframe = scraper.scrape_multiple_pages()
    scraper.save_to_csv(job_dataframe)