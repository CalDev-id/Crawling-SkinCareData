import threading
import time
import sys
import csv
import json

from selenium import webdriver
from bs4 import BeautifulSoup
import trafilatura
from tqdm import tqdm

class DataCollection():
    def __init__(self,
                 lang,
                 num_pages,
                 num_item_per_page):
        self.thread_local = threading.local()
        self.lang = lang
        
        self.num_pages = num_pages
        self.num_item_per_page = num_item_per_page
    
    def get_driver(self):
        driver = getattr(self.thread_local, 'driver', None)
        if driver is None:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('user-data-dir=C:/Users/haica/AppData/Local/Google/Chrome/User Data')
            chrome_options.add_argument('--headless')  # Menjalankan Chrome dalam mode headless
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            driver = webdriver.Chrome(options = chrome_options)
            setattr(self.thread_local, 'driver', driver)
        return driver
    
    def visit_content(self, target_url):
        try:
            driver_visit = self.get_driver()
            driver_visit.implicitly_wait(10)
            driver_visit.set_page_load_timeout(30)
            driver_visit.get(target_url)
            time.sleep(5)  # Kurangi waktu tunggu agar lebih efisien
            
            page_content = trafilatura.bare_extraction(driver_visit.page_source)
            
            if page_content:
                title = page_content.get("title", "No Title")
                author = page_content.get("author", "Unknown")
                date = page_content.get("date", "Unknown")
                url = target_url
                article = page_content.get("text") or page_content.get("raw_text", "No Content")
                
                search_content = {
                    "title": title,
                    "date": date,
                    "author": author,
                    "url": url,
                    "article": article,
                }
                return search_content
            else:
                return False
        except Exception as e:
            print(f"Error visiting {target_url}: {e}")
            return False
            
    def fetch_search_result(self, url, page, query="no_name"):
        driver = self.get_driver()
        driver.implicitly_wait(5)
        driver.get(url)
        
        all_datasets = []
        
        page_content = BeautifulSoup(driver.page_source, "html.parser")
        search_lists = page_content.find_all("div", attrs={"class": 'MjjYud'})
        search_lists = search_lists[:self.num_item_per_page]
        
        for cnt in tqdm(search_lists, desc=f"Processing page {page+1}"):
            title = cnt.find_all("h3", attrs={"class": 'DKV0Md'})
            
            if title:
                title = title[0].text
                source_url = cnt.find("a", href=True)["href"]
                
                if source_url.endswith(".pdf"):
                    continue
                
                search_content_result = self.visit_content(source_url)
                if search_content_result:
                    all_datasets.append(search_content_result)

        return all_datasets
    
    def search(self, query):
        datasets = []
        csv_file = f"data/{query}_all.csv"
        
        with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=["title", "date", "author", "url", "article"])
            writer.writeheader()
            
            for i_p in range(self.num_pages):
                start_index = i_p * 10
                url = "https://www.google.com/search?"\
                      f"q={query}&"\
                      f"hl={self.lang}&"\
                      f"lr={self.lang}&"\
                      f"start={start_index}"
                page_data = self.fetch_search_result(url, i_p, query)
                datasets += page_data
                
                for data in page_data:
                    writer.writerow(data)
            

if __name__ == "__main__":
    data_collect = DataCollection(lang="id", num_pages=1, num_item_per_page=10)
    data_collect.search("kandungan skincare yang cocok untuk jerawat pustula")
