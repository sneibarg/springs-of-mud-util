#!/usr/bin/python3
from bs4 import BeautifulSoup, NavigableString
import requests
import multiprocessing as mp
import urllib.robotparser
import logging
import re
import os
import pickle

from requests import ReadTimeout

logger = None


def create_livejournal_session(username, password):
    LOGIN_ROUTE = 'https://www.livejournal.com/login.bml'
    payload = {
        'user': username,
        'password': password,
    }
    s = requests.Session()
    p = s.post(LOGIN_ROUTE, data=payload)
    return s  # return the session object


def append_to_file(filename, string):
    javascript_enabled_message = "JavaScript must be enabled in order to use this site. Please enable JavaScript in your browser and refresh the page."
    string = string.replace(javascript_enabled_message, '')
    pattern = r"[\s\(\)]"
    filename = re.sub(pattern, "_", filename)
    with open(filename, 'a') as f:
        f.write(string)


def configure_logger(log_file_name, log_directory, log_to_console=True):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    c_handler = logging.StreamHandler() if log_to_console else None
    f_handler = logging.FileHandler(os.path.join(log_directory, log_file_name))

    if c_handler:
        c_handler.setLevel(logging.INFO)
    f_handler.setLevel(logging.INFO)

    format_str = '%(asctime)s - PID: %(process)d - %(processName)s - %(funcName)s - %(levelname)s - %(message)s'
    c_format = logging.Formatter(format_str)
    f_format = logging.Formatter(format_str)

    if c_handler:
        c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    if c_handler:
        logger.addHandler(c_handler)
    logger.addHandler(f_handler)
    return logger


def get_page(session, url, retries=3, timeout=10):
    for _ in range(retries):
        try:
            response = session.get(url, timeout=timeout)
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup
        except ReadTimeout:
            logger.warning(f"Request timeout for url: {url}. Retrying...")
    logger.error(f"Failed to get page after {retries} attempts for url: {url}.")
    return None


def save_progress(to_visit, visited, to_visit_file='to_visit.p', visited_file='visited.p'):
    with open(to_visit_file, 'wb') as tvf, open(visited_file, 'wb') as vf:
        pickle.dump(to_visit, tvf)
        pickle.dump(list(visited), vf)


def load_progress(to_visit_file='to_visit.p', visited_file='visited.p'):
    to_visit = []
    visited = []

    if os.path.exists(to_visit_file) and os.path.getsize(to_visit_file) > 0:
        with open(to_visit_file, 'rb') as tvf:
            to_visit = pickle.load(tvf)

    if os.path.exists(visited_file) and os.path.getsize(visited_file) > 0:
        with open(visited_file, 'rb') as vf:
            visited = pickle.load(vf)

    return to_visit, visited


def extract_content_from_elements(soup):
    possible_elements = ['p', 'div', 'span', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'samp']
    for elem in possible_elements:
        content = soup.find_all(elem)
        if content:
            return ' '.join([item.get_text() for item in content if
                             isinstance(item, NavigableString) or item.get_text().strip() != ''])

    return None


def extract_content_from_selectors(soup):
    possible_selectors = [
        'div#topic-content',
        'div#content',
        'main#main-content',
    ]

    for selector in possible_selectors:
        content = soup.select_one(selector)
        title = extract_title(soup)

        if title is not None and content is not None:
            return content.text
    return None


def extract_title(soup):
    title_tag = soup.title
    if title_tag is not None:
        title_text = title_tag.string
        if title_text and not title_text.strip().startswith('javascript') and not re.search(r'\w+\(.*\)',
                                                                                            title_text.strip()):
            return title_text
    return None


def extract_links(soup, base_url):
    links = [a['href'] for a in soup.find_all('a', href=True)]
    full_links = [base_url + link if 'http' not in link else link for link in links]
    return full_links


def crawl_page(session, url, base_url, visited, rp, domain_filter, retries=3, timeout=2000):
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(base_url + "/robots.txt")
    rp.read()
    if url not in visited and rp.can_fetch("*", url):
        from urllib.parse import urlparse
        visited.append(url)
        logger.info(f"Crawling: {url}")
        soup = get_page(session, url, retries, timeout)
        if soup is None:
            logger.error("Error getting content from page - " + str(page))
            return []
        content = extract_content_from_elements(soup)
        if content is None:
            content = extract_content_from_selectors(soup)
        title = extract_title(soup)
        links = extract_links(soup, base_url)
        logger.info("TITLE=" + str(title))
        logger.info("LINKS=" + str(links))
        if content is not None and title is not None:
            topic_file = os.path.join(os.getcwd(), "content", str(title))
            soup_file = os.path.join(os.getcwd(), "soup", str(title))
            append_to_file(topic_file, str(content))
            append_to_file(soup_file, str(soup))
        filtered_links = [link for link in links if domain_filter in urlparse(link).netloc]
        return filtered_links
    return []


if __name__ == "__main__":
    domain_filter = "livejournal.com"
    base_url = "https://yahvah.livejournal.com"
    start_url = base_url + "/calendar/2003"
    logger = configure_logger("web_crawler.log", "/home/neibarge/Python/livejournal")
    visited = mp.Manager().list()
    session = create_livejournal_session("yahvah", "")
    pool = mp.Pool(mp.cpu_count())
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(base_url + "/robots.txt")
    rp.read()

    to_visit, to_visited = load_progress()
    if not to_visit:
        to_visit.append(start_url)

    try:
        while to_visit:
            current_url = to_visit.pop()
            new_links = pool.apply_async(crawl_page, args=(session, current_url, base_url, visited, rp, domain_filter))
            to_visit.extend(new_links.get())
    except Exception:
        print("Caught exception - saving progress...")
    finally:
        save_progress(to_visit, visited)
