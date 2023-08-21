# shoutout Ch0c4p1kk for sharing the progress bar library <3 

import argparse
import json
import os
import re
import sys
import threading
import time
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from colorama import Fore, Style, init
from alive_progress import alive_bar

# Initialize colorama
init(autoreset=True)

class Result:
    def __init__(self, source, url, where):
        self.Source = source
        self.URL = url
        self.Where = where

headers = {}
sm = {}

def parse_headers(raw_headers):
    global headers
    if raw_headers:
        header_parts = raw_headers.split(";;")
        for header in header_parts:
            if ":" in header:
                key, value = map(str.strip, header.split(":", 1))
                headers[key] = value

def extract_hostname(url_string):
    try:
        parsed_url = urlparse(url_string)
        if parsed_url.scheme and parsed_url.netloc:
            return parsed_url.netloc
        else:
            raise ValueError("Input must be a valid absolute URL")
    except Exception as e:
        raise ValueError("Error parsing URL:", e)

def print_result(link, source_name, show_source, show_where, show_json, results, abs_link):
    result = abs_link
    if result:
        if show_json:
            where = result if show_where else ""
            result_obj = Result(source_name, result, where)
            result = json.dumps(result_obj.__dict__)
        elif show_source:
            result = f"[{source_name}] {Fore.LIGHTMAGENTA_EX}{result}{Style.RESET_ALL}"

        if show_where and not show_json:
            result = f"[{abs_link}] {result}"

        # Apply color codes for different source names
        if source_name == "href":
            result = f"{Fore.GREEN}{result}{Style.RESET_ALL}"
        elif source_name == "script":
            result = f"{Fore.BLUE}{result}{Style.RESET_ALL}"
        elif source_name == "form":
            result = f"{Fore.YELLOW}{result}{Style.RESET_ALL}"

        results.append(result)


def is_unique(url):
    global sm
    if url in sm:
        return False
    sm[url] = True
    return True

def main():
    parser = argparse.ArgumentParser(description="Web crawler tool")
    parser.add_argument("url", help="URL to crawl")
    parser.add_argument("-i", "--inside", action="store_true", help="Only crawl inside path")
    parser.add_argument("-t", "--threads", type=int, default=8, help="Number of threads to utilise.")
    parser.add_argument("-d", "--depth", type=int, default=2, help="Depth to crawl.")
    parser.add_argument("--size", type=int, default=-1, help="Page size limit, in KB.")
    parser.add_argument("--insecure", action="store_true", help="Disable TLS verification.")
    parser.add_argument("--subs", action="store_true", help="Include subdomains for crawling.")
    parser.add_argument("--json", action="store_true", help="Output as JSON.")
    parser.add_argument("-s", "--show-source", action="store_true", help="Show the source of URL based on where it was found.")
    parser.add_argument("-w", "--show-where", action="store_true", help="Show at which link the URL is found.")
    parser.add_argument("--headers", default="", help="Custom headers separated by two semi-colons.")
    parser.add_argument("--proxy", default="", help="Proxy URL.")
    parser.add_argument("--timeout", type=int, default=-1, help="Maximum time to crawl each URL, in seconds.")
    parser.add_argument("--dr", action="store_true", help="Disable following HTTP redirects.")
    parser.add_argument("-u", "--unique", action="store_true", help="Show only unique urls.")
    args = parser.parse_args()

    if args.proxy:
        os.environ["PROXY"] = args.proxy
    proxy_url = os.getenv("PROXY")

    parse_headers(args.headers)

    results = []
    lock = threading.Lock()

    def worker(url, pbar):
        try:
            hostname = extract_hostname(url)
            allowed_domains = [hostname]

            if "Host" in headers:
                allowed_domains.append(headers["Host"])

            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.content, "html.parser")

            # Process links
            for link in soup.find_all("a", href=True):
                link_url = link["href"]
                abs_link = link_url if link_url.startswith("http") else url + link_url
                if abs_link.startswith(url) or not args.inside:
                    print_result(link_url, "href", args.show_source, args.show_where, args.json, results, abs_link)

            # Process scripts
            for script in soup.find_all("script", src=True):
                print_result(script["src"], "script", args.show_source, args.show_where, args.json, results, script)

            # Process forms
            for form in soup.find_all("form", action=True):
                print_result(form["action"], "form", args.show_source, args.show_where, args.json, results, form)

            pbar()

        except Exception as e:
            with lock:
                print(Fore.RED + "Error while processing:", e)

    with alive_bar(len(args.url), bar="blocks") as pbar:
        threads = []
        thread = threading.Thread(target=worker, args=(args.url, pbar))
        threads.append(thread)
        thread.start()

        for thread in threads:
            thread.join()

    output_file = sys.stdout if args.unique else sys.stderr
    with output_file as f:
        for result in results:
            if args.unique:
                if is_unique(result):
                    f.write(result + "\n")
            else:
                f.write(result + "\n")

if __name__ == "__main__":
    print(Fore.MAGENTA + r"""
  ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⠀⢰⠛⠉⠳⡀⠀⠀⠀⠀⢀⣠⠤⠴⠒⠒⠒⠒⠤⣄⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⡾⠉⠙⠻⣧⠀⠀⢳⡀⠀⣠⠞⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⢳⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡤⠶⢻⢷⣤⡀⠀⠈⢧⡀⠀⣷⠞⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⢣⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣰⠋⠀⠀⢸⠀⠙⢿⡄⠀⠀⢱⣴⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣇⣠⠴⡶⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡞⠁⣀⣀⣴⡛⠳⣄⠀⠙⣦⣄⣠⣇⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⢁⣴⢧⡈⠳⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡤⠞⠁⠀⣨⠏⠀⣠⡼⠲⡶⣶⠋⢹⡗⣦⣀⣀⡀⣀⣀⣤⠀⠈⢳⡀⠀⢀⣀⣀⠀⢀⡞⠉⢳⣤⠞⠁⢠⠏⠙⠦⡀⠙⢧⠚⢳⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⣠⡴⠚⠁⠀⣀⣴⠞⠁⣠⠞⡿⠀⢀⡇⠸⣤⣸⡶⠿⣇⣶⡇⠻⠿⠀⠀⠀⠀⢹⠀⡏⠀⢹⡄⢸⣧⠀⠘⡏⠀⢠⠏⠀⠀⠀⠈⠳⣄⠱⢬⣧⡀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⣠⠞⠁⣠⣶⣶⠟⠋⠁⢀⡴⠃⣰⠁⢀⣾⠀⣠⠟⠋⢳⡶⠛⢥⡀⠀⠀⠀⡤⢶⣶⡋⠸⡇⠀⠈⣿⡟⢹⠀⠀⣿⡶⠋⠀⠀⠀⠀⠀⠀⠈⠳⣾⣿⣏⠓⠤⣄⠀⠀
⠀⠀⠀⡠⠞⢁⣠⠞⠁⠀⠀⠀⠀⠀⠀⠈⠉⠁⠀⠀⠘⠷⠤⢼⣀⠀⠀⣼⠇⠀⢀⡞⠀⣸⠃⠀⠀⠀⠀⡇⠀⢸⠀⠀⢸⡖⠒⢻⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢣⡘⢦⡀⠀⠀
⣤⠖⠋⣀⠴⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠉⠉⠀⠀⡞⠀⢠⠇⠀⠀⠀⠀⠀⡷⠒⠺⡇⠀⠀⣇⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠑⠒⠒
⠉⠉⠉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢺⣀⣀⡾⠀⠀⠀⠀⠀⠀⢸⠀⠀⡇⠀⠀⢿⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀SICARI0-WEBSPIDER | 23⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⣇⠀⢹⠀⠀⢸⡄⣸⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡀⢸⠀⠀⢸⡏⠉⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⣧⠾⡇⠀⠘⡇⣀⢳⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀Crawlinggg..........⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⠀⢸⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢐⣇⣀⣸⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    """ + Style.RESET_ALL)
    main()
