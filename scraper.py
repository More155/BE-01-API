import time
import re
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from models import ScrapedPageRecord
from typing import Optional

class EthicalScraper:
    def __init__(self, base_url: str, bot_name: str, contact_email: str, delay: float = 2.0):
        self.base_url = base_url
        self.delay = delay
        self.headers = {"User-Agent": f"{bot_name}/1.0 (+mailto:{contact_email})"}
        
    def check_robots_txt(self) -> bool:
        parsed_url = urlparse(self.base_url)
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        try:
            response = httpx.get(robots_url, headers=self.headers, timeout=5.0)
            if response.status_code == 200:
                if "Disallow: /" in response.text and "User-agent: *" in response.text:
                    print(f"[⚠️ Warning]: robots.txt blocks global scrapers at {robots_url}")
                    return False
            return True
        except httpx.HTTPError:
            return True

    def fetch(self, url: str) -> str:
        print(f"[1/5 Fetching]: {url}")
        response = httpx.get(url, headers=self.headers, timeout=10.0)
        response.raise_for_status()
        return response.text

    def parse(self, raw_html: str) -> BeautifulSoup:
        print("[2/5 Parsing]")
        return BeautifulSoup(raw_html, "html.parser")

    def extract(self, soup: BeautifulSoup) -> dict:
        print("[3/5 Extracting]")
        for boilerplate in soup(["nav", "footer", "script", "style", "aside"]):
            boilerplate.decompose()
        title_element = soup.find("h1")
        content_element = soup.find("main") or soup.find("article") or soup.find("body")
        author_element = soup.select_one(".author-name, [itemprop='author']")
        return {
            "title": title_element.get_text() if title_element else "",
            "content": content_element.get_text() if content_element else "",
            "author": author_element.get_text() if author_element else "Unknown"
        }

    def clean(self, raw_data: dict) -> dict:
        print("[4/5 Cleaning]")
        cleaned_data = {}
        for key, value in raw_data.items():
            if isinstance(value, str):
                text = re.sub(r'\s+', ' ', value).strip()
                cleaned_data[key] = text
            else:
                cleaned_data[key] = value
        return cleaned_data

    def structure(self, cleaned_data: dict, url: str) -> ScrapedPageRecord:
        print("[5/5 Structuring]")
        full_record = {**cleaned_data, "url": url}
        return ScrapedPageRecord(**full_record)

    def run_pipeline(self, url: str) -> Optional[ScrapedPageRecord]:
        if not self.check_robots_txt():
            print("[❌ Error]: Aborting due to robots.txt restrictions.")
            return None
        try:
            raw_html = self.fetch(url)
            soup = self.parse(raw_html)
            raw_fields = self.extract(soup)
            cleaned_fields = self.clean(raw_fields)
            structured_record = self.structure(cleaned_fields, url)
            
            print(f"[💤 Politeness]: Sleeping for {self.delay}s...\n")
            time.sleep(self.delay)
            return structured_record
        except Exception as e:
            print(f"[❌ Pipeline Failure]: {url}. Error: {e}")
            return None