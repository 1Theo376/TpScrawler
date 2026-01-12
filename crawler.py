from bs4 import BeautifulSoup
import urllib.robotparser
from urllib.request import urlopen
import time
import tldextract
import json
import jsonlines

class Crawler:
    def __init__(self, base_url, allowed_paths=[], priorized_paths=[]):
        self.base_url = base_url
        self.allowed_paths = allowed_paths
        self.priorized_paths = priorized_paths

    def get_page_content(self,url):
        response = urlopen(url) 
        return response.read()

    def be_polite(self, wait):
        time.sleep(wait)

    def parsing_allowed(self,url,robot_path):
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url("https://" + robot_path)
        rp.read()
        can_fetch = rp.can_fetch("*", url)
        return can_fetch
        
    
    def extract_links(self,content):
        soup = BeautifulSoup(content, 'html.parser')
        links = []
        for link in soup.find_all('a', href=True):
            if tldextract.extract(link['href']).domain == tldextract.extract(self.base_url).domain: #a voir les autres cas après...
                if "product" in link['href']:
                    self.priorized_paths.append(link['href'])
                else:
                    self.allowed_paths.append(link['href'])
                links.append(link['href'])
        return links
    
    def extract_first_paragraph(self,url):
        content = self.get_page_content(url)
        soup = BeautifulSoup(content, 'html.parser')
        if soup.find('p'):
            first_paragraph = soup.find('p').get_text()
        else:
            first_paragraph = 'No description found'
        return first_paragraph
    
    def extract_title(self,url):
        content = self.get_page_content(url)
        soup = BeautifulSoup(content, 'html.parser')
        if soup.title:
            title = soup.title.string 
        else:
            title = 'No title found'
        return title
    
    def crawl(self, max_nb_pages=50):
        ext = tldextract.extract(self.base_url)
        robot_path = f"{'https://' + ext.subdomain + '.' if ext.subdomain else ''}{ext.domain}.{ext.suffix}/robots.txt"
        self.allowed_paths.append(self.base_url)
        while self.allowed_paths and max_nb_pages > 0:
            if len(self.priorized_paths) > 0:
                current_url = self.priorized_paths.pop(0)
            else:
                current_url = self.allowed_paths.pop(0)
            self.be_polite(0.5)
            if self.parsing_allowed(current_url, robot_path):
                content = self.get_page_content(current_url)
                title, first_paragraph = self.extract_title(current_url), self.extract_first_paragraph(current_url)
                links = self.extract_links(content)
                max_nb_pages -= 1
                output = {
                    "url": current_url,
                    "title": title,
                    "description": first_paragraph,
                    "links": links
                }
                with jsonlines.open("/home/ensai/Documents/Indexation/TpScrawler/output/products.jsonl", mode='w') as writer:
                    writer.write(output)
    

crawler = Crawler("https://web-scraping.dev/")



crawler.crawl(10)