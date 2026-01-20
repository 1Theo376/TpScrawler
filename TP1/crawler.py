from bs4 import BeautifulSoup
import urllib.robotparser
from urllib.request import urlopen
import time
import urllib.request
import jsonlines
from urllib.parse import urljoin, urlparse

class Crawler:
    def __init__(self, base_url):
        self.base_url = base_url 
        self.already_visited = [] #We don't want to keep same results
        self.robot_parser = None #Permissions in robots.txt
        self.queue = [] #Normal queue
        self.priority_queue = [] #Priority queue for product pages

    def init_robot_parser(self, robot_url):
        """
        Initialize and configure the robots.txt parser for the target website.

        Parameters:
        ----------
        robot_urlo :str
            The URL of the robots.txt file.

        Returns:

        """
        self.robot_parser = urllib.robotparser.RobotFileParser()
        self.robot_parser.set_url(robot_url)
        self.robot_parser.read()
        return self.robot_parser
    
    def is_parsing_allowed(self, url):
        """
        Check whether the given URL is allowed to be crawled according to robots.txt.

        Parameters:
        ----------
        url : str
            The URL to check for crawling permission.
        
        Returns:
        -------
        bool
            True if crawling is allowed, False otherwise.
        """
        return self.robot_parser.can_fetch("*", url)
    
    def be_polite(self):
        """
        Enforce politeness by respecting the crawl delay specified in robots.txt.

        If no craw delay is specified, a default delay of 1 second is applied.
        """
        delay = self.robot_parser.crawl_delay("*")
        if delay is None:
            time.sleep(1)
        else:
            time.sleep(delay)

    def get_html(self, url):
        """
    Retrieve the raw HTML content of a web page.

    Parameters
    ----------
    url : str
        URL of the web page to fetch.

    Returns
    -------
    bytes
        Raw HTML content of the page.
    """
        req = urllib.request.Request(
            url=url,
            method="GET")
        response = urllib.request.urlopen(req)
        data=response.read()
        return(data)
    
    def get_page_content(self, url):
        """
    Fetch and parse the HTML content of a web page if crawling is allowed.

    Parameters
    ----------
    url : str
        URL of the web page to fetch and parse.

    Returns
    -------
    bs4.BeautifulSoup or None
        Parsed HTML content as a BeautifulSoup object if allowed,
        None otherwise.
    """
        if not self.is_parsing_allowed(url):
            return None

        html = self.get_html(url)
        return BeautifulSoup(html, "html.parser")

           
    def extract_links(self,soup, current_url):
        """
    Extract and normalize internal links from a parsed HTML page.

    Parameters
    ----------
    soup : bs4.BeautifulSoup
        Parsed HTML content of the current page.
    current_url : str
        URL of the page from which links are extracted.

    Returns
    -------
    list of str
        List of unique internal absolute URLs extracted from the page.
    """
        links = []
        base_netloc = urlparse(self.base_url).netloc

        for a in soup.find_all("a", href=True):
            href = a["href"]

            if href.startswith("#"):
                continue
            absolute = urljoin(current_url, href)
            absolute = absolute.split("#", 1)[0].rstrip("/")
            if urlparse(absolute).netloc != base_netloc:
                continue

            links.append(absolute)
        return list(dict.fromkeys(links))

    def extract_first_paragraph(self, soup):
        """
    Extract the text of the first paragraph from a parsed HTML page.

    Parameters
    ----------
    soup : bs4.BeautifulSoup
        Parsed HTML content of the page.

    Returns
    -------
    str
        Text content of the first paragraph, or a default message if none exists.
    """
        first_paragraph = soup.find("p")
        return first_paragraph.get_text(strip=True) if first_paragraph else "No description found"

    def extract_title(self, soup):
        """
    Extract the title of a web page from its HTML content.

    Parameters
    ----------
    soup : bs4.BeautifulSoup
        Parsed HTML content of the page.

    Returns
    -------
    str
        Page title, or a default message if the title tag is missing.
    """
        if soup.title and soup.title.string:
            title = soup.title.string.strip() 
        else:
            title = 'No title found'
        return title
    
    def add_to_queue(self, url, visited_set):
        """
    Add a URL to the appropriate crawl queue if it has not been visited yet.

    Parameters
    ----------
    url : str
        URL to be added to the crawl queue.
    visited_set : set
        Set of URLs that have already been visited.
    """
        if url in visited_set:
            return
        if url in self.queue or url in self.priority_queue:
            return

        if "product" in url:
            self.priority_queue.append(url)
        else:
            self.queue.append(url)

    def pop_next_url(self):
        """
    Retrieve and remove the next URL to crawl from the queues.

    Returns
    -------
    str or None
        Next URL to crawl, or None if no URL remains in the queues.
    """
        if self.priority_queue:
            return self.priority_queue.pop(0)
        if self.queue:
            return self.queue.pop(0)
        return None

    def crawl(self, start_url=None, max_pages=50):
        """
    Crawl the website starting from a given URL and collect page information.

    Parameters
    ----------
    start_url : str, optional
        URL from which the crawl starts. If None, the base URL is used.
    max_pages : int, optional
        Maximum number of pages to crawl (default is 50).

    Returns
    -------
    list of dict
        List of dictionaries containing the extracted information for each
        visited page.
    """
        parsed = urlparse(self.base_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        self.init_robot_parser(robots_url)
        if start_url is None:
            start_url = self.base_url

        outputs = []
        visited = set(self.already_visited)

        # init queue
        self.add_to_queue(start_url, visited)

        while len(outputs) < max_pages:
            current_url = self.pop_next_url()
            if current_url is None:
                break  # nothing to visit

            if current_url in visited:
                continue
            visited.add(current_url)

            self.be_polite()

            soup = self.get_page_content(current_url)
            if soup is None:
                continue

            title = self.extract_title(soup)
            desc = self.extract_first_paragraph(soup)
            links = self.extract_links(soup, current_url)

            for link in links:
                self.add_to_queue(link, visited)

            outputs.append({
                "url": current_url,
                "title": title,
                "description": desc,
                "links": links
            })

        self.already_visited = list(visited)
        return outputs
    
    def save_to_jsonl(self, data, output_path):
        """
        Save crawl results to a JSONL file.

        Parameters
        ----------
        data : list of dict
            Crawl results to be saved.
        output_path : str
            Path to the output JSONL file.
        """
        with jsonlines.open(output_path, mode="w") as writer:
            for item in data:
                writer.write(item)


if __name__ == "__main__":
    crawler = Crawler("https://web-scraping.dev/products")
    data = crawler.crawl(
        max_pages=50
    )
    crawler.save_to_jsonl(
        data,
        "/home/ensai/Documents/Indexation/TpScrawler/TP1/output/products.jsonl"
    )
