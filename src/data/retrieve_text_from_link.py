# -*- coding: utf-8 -*-
import click

import logging
import requests
from os.path import exists
from bs4 import BeautifulSoup
from pathlib import Path
# from dotenv import find_dotenv, load_dotenv
from src.data.get_gmails import GMailGetter
from src.data.extract_hyperlinks import InboxDelta
from joblib import dump, load
from string import punctuation


class LinkParser:
    def __init__(self, hyperlink_list, run_pipeline=True):
        self.link_list = hyperlink_list
        if run_pipeline:
            self.corpus = self.retrieve_text(hyperlink_list)

    def retrieve_text(self, hyperlinks):
        corpus = {}
        for link in hyperlinks:
            response = requests.get(link)
            print(response.status_code)
            print(response.headers['content-type'])
            if response.encoding == 'utf-8':
                corpus[link] = (response.headers['content-type'], response.text)
        return corpus

    def parse_text(self, corpus):
        for link, text_tpl in corpus.items():
            if 'html' in text_tpl[0]:
                tmp_soup = BeautifulSoup(text_tpl[1], "html5lib")
                tmp_output = ''
                counter = 0
                for line in tmp_soup.prettify().split("\n"):
                    #if len(line) > 200: # TODO: Check is this setting is appropriate, make data-driven
                    punctset = [f for f in line if f in punctuation]
                    punctuation_counts = len(punctset)
                    if punctuation_counts / (len(line)+.0000000000000000001) < .1: # TODO: Check if this setting is appropriate, make data-driven
                        tmp_output = tmp_output + line
                    counter +=1
                if counter == 0:
                    print(link)
                    print('\n\n')
                    print(tmp_soup)
                    print('\n\n')
                    print("Nothing mined... :(")
                    print('\n\n\n\n\n\n')
                corpus[link] = tmp_output
        return corpus


def main():
    if not exists ("./parser.jbl"):
        mails = GMailGetter()
        messages = InboxDelta(mails.unread_messages)
        parser = LinkParser(messages.hyperlinks)
        dump(parser, "parser.jbl")
    else:
        parser = load("./parser.jbl")
    crp = parser.parse_text(parser.corpus)

    for key, val in crp.items():
        print(key)
        print('\n')
        print(val)
        print('\n\n')
    # TODO: Parse message content into usable text :)

if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    # load_dotenv(find_dotenv())

    main()

