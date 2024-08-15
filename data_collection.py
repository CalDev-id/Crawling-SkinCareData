import threading
import time
import json

from selenium import webdriver
from bs4 import BeautifulSoup
import trafilatura
from tqdm import tqdm

class DataCollection():
    def __init__(self, lang, num_pages, num_item_per_page):
        self.thread_local = threading.local()
        self.lang = lang
        self.num_pages = num_pages
        self.num_item_per_page = num_item_per_page
        self.current_id = 1  # Initialize ID counter
    
    def get_driver(self):
        driver = getattr(self.thread_local, 'driver', None)
        if driver is None:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('user-data-dir=C:/Users/haica/AppData/Local/Google/Chrome/User Data')
            driver = webdriver.Chrome(options=chrome_options)
            setattr(self.thread_local, 'driver', driver)
        return driver
    
    def visit_content(self, target_url):
        try:
            driver_visit = self.get_driver()
            driver_visit.implicitly_wait(10)
            driver_visit.set_page_load_timeout(30)
            driver_visit.get(target_url)
            time.sleep(10)
            
            page_content = trafilatura.bare_extraction(driver_visit.page_source)
            
            title = page_content.get("title")
            author = page_content.get("author")
            date = page_content.get("date")
            url = page_content.get("url")
            article = page_content.get("text") or page_content.get("raw_text", "")
            
            search_content = {
                "id": self.current_id,  # Set current ID
                "title": title,
                "date": date,
                "author": author,
                "url": url,
                "article": article,
            }
            
            self.current_id += 1  # Increment ID for the next entry
            
            return search_content
        except Exception as e:
            print(f"Error visiting {target_url}: {e}")
            return False
            
    def fetch_search_result(self, url, page, query="no_name"):
        driver = self.get_driver()
        driver.implicitly_wait(5)
        driver.get(url)
        
        page_content = BeautifulSoup(driver.page_source, "html.parser")
        search_lists = page_content.find_all("div", attrs={"class": 'MjjYud'})
        search_lists = search_lists[:self.num_item_per_page]
        
        all_datasets = []
        for cnt in tqdm(search_lists):
            title = cnt.find_all("h3", attrs={"class":  'DKV0Md'})
            
            if len(title) > 0:
                source_url = cnt.find_all("a", attrs={"jsname": "UWckNb"})[0]["href"]
                print(source_url)
                if source_url.endswith(".pdf"):
                    continue
                
                search_content_result = self.visit_content(source_url)
                if not search_content_result:
                    continue
                
                all_datasets.append(search_content_result)
                   
        return all_datasets
    
    def search(self, query):
        all_datasets = []
        for i_p in range(self.num_pages):
            start_index = i_p * 10
            url = "https://www.google.com/search?"\
                  f"q={query}&"\
                  f"hl={self.lang}&"\
                  f"lr={self.lang}&"\
                  f"start={start_index}"
            page_data = self.fetch_search_result(url, i_p, query)
            all_datasets.extend(page_data)
        
        # Simpan semua hasil ke dalam satu file JSON dengan ID increment
        with open(f"data/{query}_all.json", "w") as json_w:
            json.dump(all_datasets, json_w, indent=4)

if __name__ == "__main__":
    data_collect = DataCollection(lang="id", num_pages=10, num_item_per_page=10)
    data_collect.search("kandungan skincare yang cocok untuk black head")
