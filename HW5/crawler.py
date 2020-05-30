#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import argparse
import re
import os
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


DEFAULT_OUTPUT = 'results'
DEFAULT_INTERVAL = 5.0  # interval between requests (seconds)
DEFAULT_ARTICLES_LIMIT = 1  # total number articles to be extrated
DEFAULT_RESET = False
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'

visited_urls = set()  # all urls already visited, to not visit twice
pending_urls_info = []  # queue, element is lists of structure [pending_url, [anchor texts]]
link_graph = [] # graph to describe the linking between urls

def load_urls(session_file):
    """Resume previous session if any, load visited URLs"""

    try:
        with open(session_file) as fin:
            for line in fin:
                visited_urls.add(line.strip())
    except FileNotFoundError:
        pass


def scrap(base_url, article, anchor_texts, output_file, session_file, articles_limit):
    """Represents one request per article"""

    full_url = base_url + article
    try:
        r = requests.get(full_url, headers={'User-Agent': USER_AGENT})
    except requests.exceptions.ConnectionError:
        print("Check your Internet connection")
        input("Press [ENTER] to continue to the next request.")
        return
    if r.status_code not in (200, 404):
        print("Failed to request page (code {})".format(r.status_code))
        input("Press [ENTER] to continue to the next request.")
        return

    soup = BeautifulSoup(r.text, 'html.parser')
    title = soup.find('h1', {'id':'firstHeading'}).get_text().lower()
    content = soup.find('div', {'id':'mw-content-text'})

    # skip if already added text from this article, as continuing session
    if full_url in visited_urls:
        return
    visited_urls.add(full_url)

    # add new related articles to queue
    # check if are actual articles URL
    for a in content.find_all('a'):
        href = a.get('href')
        href_anchor_text = a.get_text().lower()
        if not href:
            continue
        if href[0:6] != '/wiki/':  # allow only article pages
            continue
        elif ':' in href:  # ignore special articles e.g. 'Special:'
            continue
        elif href[-4:] in ".png .jpg .jpeg .svg":  # ignore image files inside articles
            continue
        elif base_url + href in visited_urls:  # already visited
            continue
        pending_urls = [pending_url[0] for pending_url in pending_urls_info]
        if href in pending_urls:  # already added to queue
            url_index = pending_urls.index(href)
            if href_anchor_text not in pending_urls_info[url_index][1]:
                pending_urls_info[url_index][1].append(href_anchor_text)
            continue
        url_index = len(pending_urls_info)
        pending_urls_info.append([href, [href_anchor_text]])
        if url_index >= articles_limit:
            break
        link_graph[len(visited_urls)-1].append(url_index)  # build the linking graph

    parenthesis_regex = re.compile('\(.+?\)')  # to remove parenthesis content
    citations_regex = re.compile('\[.+?\]')  # to remove citations, e.g. [1]

    # remove math expressions 
    math_expressions = content.find_all('span', {'class':'mwe-math-element'})
    for math_expression in math_expressions:
        math_expression.decompose()
    
    # get plain text from each <p>
    p_list = content.find_all('p')
    with open(output_file, 'w', encoding = 'utf-8') as fout:
        # write title
        fout.write("$T: " + title + '\n\n')
        # write anchor text
        fout.write("$AT: ") # use $AT: to represent anchor text
        for i in range(len(anchor_texts)):
            if i == len(anchor_texts)-1:
                fout.write(anchor_texts[i] + '\n\n')
                break
            fout.write(anchor_texts[i] + ", ")

        # write plain text
        for p in p_list:
            text = p.get_text().strip()
            text = parenthesis_regex.sub('', text)
            text = citations_regex.sub('', text)
            if text:
                fout.write(text + '\n\n')  # extra line between paragraphs

    with open(session_file, 'a', encoding = 'utf-8') as fout:
        fout.write(full_url + '\n')  # log URL to session file

def main(initial_url, articles_limit, interval, output_folder, reset):
    """ Main loop, single thread """

    minutes_estimate = interval * articles_limit / 60
    print("This session will take {:.1f} minute(s) to download {} article(s):".format(minutes_estimate, articles_limit))
    print("\t(Press CTRL+C to pause)\n")

    link_graph.extend([[] for _ in range(articles_limit)])

    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    session_file = "visited_websites.txt"
    if reset:
        print("Reset")
        with open(session_file, 'w', encoding = 'utf-8') as f:
            f.seek(0)
            f.truncate()
    load_urls(session_file)  # load previous session (if any)

    base_url = '{uri.scheme}://{uri.netloc}'.format(uri=urlparse(initial_url))
    initial_url = initial_url[len(base_url):]
    pending_urls_info.append([initial_url, ['']])

    counter = 0
    while len(pending_urls_info) > 0:
        try:
            counter += 1
            if counter > articles_limit:
                break
            try:
                anchor_texts = []
                next_url, anchor_texts = pending_urls_info[counter-1]
            except IndexError:
                break

            time.sleep(interval)
            article_format = next_url.replace('/wiki/', '')[:35]
            output_file = output_folder + "/" + str(counter).zfill(4) + ".txt"
            print("{:<7} {}".format(counter, article_format))
            scrap(base_url, next_url, anchor_texts, output_file, session_file, articles_limit)
        except KeyboardInterrupt:
            input("\n> PAUSED. Press [ENTER] to continue...\n")
            counter -= 1

    graph_file = "linking_graph.txt"
    with open(graph_file, 'w') as f:
        for file_links in link_graph:
            file_links.sort()
            for file_link in file_links:
                f.write(str(file_link) + " ")
            f.write("\n")

    print("Finished!")
    sys.exit(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "initial_url", help="Initial Wikipedia article, e.g. https://en.wikipedia.org/wiki/Computer_science")
    parser.add_argument("-a", "--articles", nargs='?', default=DEFAULT_ARTICLES_LIMIT, type=int, help="Total number of articles")
    parser.add_argument("-i", "--interval", nargs='?', default=DEFAULT_INTERVAL, type=float, help="Interval between requests")
    parser.add_argument("-o", "--output", nargs='?', default=DEFAULT_OUTPUT, type=str, help="Output folder")
    parser.add_argument("-r", "--reset", action="store_true")
    args = parser.parse_args()
    main(args.initial_url, args.articles, args.interval, args.output, args.reset)
