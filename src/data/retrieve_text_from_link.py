# -*- coding: utf-8 -*-
import click
import logging
import requests
import re
from pathlib import Path
# from dotenv import find_dotenv, load_dotenv
import pickle
import os.path
from src.data.get_gmails import connector_gmail
from src.data.extract_hyperlinks import InboxDelta


class LinkParser:
    def __init__(self, hyperlink_list):
        self.link_list = hyperlink_list
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
                txt = text_tpl[1]
                txt = re.sub('<.*>', '', txt)
                txt = re.sub('\n', ' ', txt)
                print(txt)
                tmp_tpl = (text_tpl[0], txt)
                corpus[link] = tmp_tpl
        return corpus


def main():
    mails = connector_gmail()
    messages = InboxDelta(mails.retrieved_delta)
    parser = LinkParser(messages.hyperlinks)
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

