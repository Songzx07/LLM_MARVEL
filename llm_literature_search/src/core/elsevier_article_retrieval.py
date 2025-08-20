import os
import re
import time
import requests
from typing import List


class DOIFetcher:
    def __init__(self, api_key: str, base_url: str, rate_limit: int = 10):
        """
        Initialize the DOIFetcher with API key and base URL.

        Args:
            api_key: Elsevier API key
            base_url: Base URL for Elsevier API
            rate_limit: Number of requests per second (default is 10)
        """
        self.api_key = api_key
        self.base_url = base_url
        self.rate_limit = rate_limit
        self.delay = 1.0 / rate_limit
        self.last_request_time = 0

    def sanitize_filename(self, doi: str) -> str:
        """
        Clean the DOI string to create a valid filename.

        Args:
            doi: DOI string

        Returns:
            A sanitized filename based on the DOI
        """

        if doi.startswith('doi:'):
            doi = doi[4:]
        if doi.startswith('https://doi.org/'):
            doi = doi[16:]
        if doi.startswith('http://doi.org/'):
            doi = doi[15:]

        filename = re.sub(r'[<>:"/\\|?*]', '_', doi)
        filename = filename.replace('/', '_')

        return filename

    def rate_limit_wait(self):
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.delay:
            sleep_time = self.delay - time_since_last
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def fetch_paper(self, doi: str, output_dir: str = "./article_xmls") -> bool:
        """
        Fetch a paper by its DOI and save it as an XML file.

        Args:
            doi: DOI of the paper to fetch
            output_dir: Output directory to save the XML file

        Returns:
            True if the paper was fetched successfully, False otherwise
        """
        os.makedirs(output_dir, exist_ok=True)

        self.rate_limit_wait()

        try:
            url = f"{self.base_url}/{doi}?view=FULL"
            headers = {
                "X-ELS-APIKey": self.api_key
            }

            print(f"Fetching: {doi}")

            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 200:
                filename = self.sanitize_filename(doi) + ".xml"
                filepath = os.path.join(output_dir, filename)

                with open(filepath, 'wb') as f:
                    f.write(response.content)

                print(f"  Successfully fetched: {filename}")
                return True
            else:
                print(f"   Wrong fetching {doi}: HTTP {response.status_code}")
                return False

        except Exception as e:
            print(f"   Wrong fetching {doi}: {str(e)}")
            print("This paper is not published by Elsevier")
            return False

    def fetch_papers_batch(self, doi_list: List[str], output_dir: str = "./article_xmls") -> dict:
        """
        Fetch a batch of papers by their DOIs.

        Args:
            doi_list: DOI list
            output_dir: Output directory

        Returns:
            A dictionary with total, successful, failed counts and list of failed DOIs
        """
        total = len(doi_list)
        successful = 0
        failed = 0
        failed_dois = []

        print(f"Start to fetch xml file of {total} papers...")
        print("-" * 50)

        for i, doi in enumerate(doi_list, 1):
            print(f"[{i}/{total}] ", end="")

            if self.fetch_paper(doi, output_dir):
                successful += 1
            else:
                failed += 1
                failed_dois.append(doi)

            if i > 0:
                print(
                    f"    Progress: {i/total*100:.1f}%")

        print("-" * 50)
        print(f"\n Completed paper fetching.")
        print(f"In total: {total} papers")
        print(f"Success: {successful} papers")
        print(f"Failed: {failed} papers")

        if failed_dois:
            print(f"\nFailed DOI:")
            for doi in failed_dois:
                print(f"  - {doi}")

        return {
            'total': total,
            'successful': successful,
            'failed': failed,
            'failed_dois': failed_dois,
        }
