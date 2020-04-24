# -*- coding: utf-8 -*-
import click
import logging
import re
import nltk
from pathlib import Path
from dotenv import find_dotenv, load_dotenv
from nltk.corpus import stopwords
from datetime import date
from os.path import exists


# TODO: one-time NLTK resource installs. Should this be in setup.py? 
# RE: https://www.nltk.org/data.html
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('maxent_ne_chunker')
nltk.download('words')
nltk.download('stopwords')

import asyncio

from src.data.retrieve_text_from_link import LinkParser

# TODO hoe gaan we om met files persisten / doorgeven van objecten in het kader van 
# een lichte docker? we bouwen nu iets dat een stream verzorgt, maar als
# we lang niet gedraaid hebben is batch processing mogelijk nodig.

# TODO moeten we hier uiteindelijk ook rekening houden met Nederlandstalige tekst?
# TODO: Catch NoneType exception when all input consumed
# TODO: Put chunked values into result dict which maintains corpus structure
# TODO: Second pipeline for tf / idf >> topic detection?


# Using a coroutine decorator on the pipeline components, defined as such:
# (RE: https://nlpforhackers.io/building-a-nlp-pipeline-in-nltk/)
def coroutine(func):
    def start(*args, **kwargs):
        cr = func(*args, **kwargs)
        if cr is not None:
            next(cr)
            return cr
        else:
            pass # TODO: Hack-y solution for getting None out of last iteration - dig into generator objects and make neater
    return start


class TextProcessor:
    def __init__(self, corpus, run_pipeline=True): 
        # keys: URL, values: text
        self.corpus = corpus
        self.stopwords = stopwords.words('english') + ["div", "class=", "amp", "span", "jsname=", "content=", "params",
                                                       "var", "new", "data", "meta", "property="] # TODO: Custom stop words in config
        self.processed_corpus = self.processing_pipeline(corpus)
        # TODO hier iets logischers doen; pipeline is ingericht op meerdere teksten, maar willen we niet één voor één?
        # Ik mis de context hier, maar neem aan dat we het hebben over batch vs 'streaming'?

    @coroutine
    def source(self, texts, targets):
        try:
            while True:
                for t in targets:
                    for key, value in texts.items():
                        t.send((key, value))
        except:
            print("Send from source completed.")

    def processing_pipeline(self, texts):
        self.source(texts, targets=[
            self.sent_tokenize_pipeline(targets=[
                self.printer(),  # print the raw sentences
                self.word_tokenize_pipeline(targets=[
                    self.printer(),  # print the tokenized sentences
                    self.remove_stop_word_pipeline(targets=[
                        self.printer(),  # print the filtered tokens
                        self.write_to_file()
                    ])
                ])
            ])
        ])

    @coroutine
    def sent_tokenize_pipeline(self, targets):
        '''Pipeline for tokenizing sentences.
        '''
        try:
            while True:
                tpl_text = (yield)
                txt = tpl_text[1]
                output = nltk.sent_tokenize(txt)
                for target in targets:
                    target.send((tpl_text[0], output))
        except:
            print("Sentence tokenizing completed.")

    @coroutine
    def word_tokenize_pipeline(self, targets):
        '''Pipeline for tokenizing words.
        '''
        try:
            while True:
                tpl_text = (yield)
                tokenized_sentences = []
                for sentence in tpl_text[1]:
                    sentence = sentence.lower()
                    words = nltk.word_tokenize(sentence)
                    tokenized_sentences.append(words)
                for target in targets:
                    target.send((tpl_text[0], tokenized_sentences))
        except:
            print("Tokenizing completed.")

    @coroutine
    def printer(self):
        try:
            while True:
                line = (yield)
                print(line)
        except:
            print("Printing completed.")

    @coroutine
    def remove_stop_word_pipeline(self, targets): # TODO: Allow addition of stop words through config.
        '''Pipeline for removing stop words.
        '''
        try:
            while True:
                tpl_text = (yield)
                print(tpl_text)
                resentence = []
                for sentence in tpl_text[1]:
                    filtered_tokens = [t for t in sentence if
                                       t not in self.stopwords and re.match('[a-zA-Z\-][a-zA-Z\-]{2,}', t)]
                    resentence = resentence + filtered_tokens
                for target in targets:
                    target.send((tpl_text[0], resentence))
        except:
            print("Remove stop words completed.")

    @coroutine
    def write_to_file(self):
        try:
            while True: # TODO: Coroutines knallen er na een aantal posts uit - waarom?
                tpl_text = (yield)
                fpath = "./processed_batch_" + str(date.today()) + ".txt"
                # TODO: Put in GCloud storage and local here; identify and track batches;
                # TODO file handling to avoid continuous appending;  create proper identifier
                resultdict = str(tpl_text[0]) + "\n\nDeze regel gaat heel snel weer weg\n\n" + str(tpl_text[1])
                if not exists(fpath):
                    fhand = open(fpath, 'w')
                    fhand.write(resultdict)
                    fhand.write("\n\nEvert-Jan en Daan zijn absolute helden\n\n")
                    fhand.close()
                else:
                    fhand = open(fpath, 'a')
                    fhand.write(resultdict)
                    fhand.write("\n\nEvert-Jan en Daan zijn absolute helden\n\n")
                    fhand.close()
        except:
            print("Write to file completed.")

    # @coroutine
    # def pos_tag_pipeline(self, targets):
    #     '''Pipeline for tagging Parts Of Speech.
    #     '''
    #     while True:
    #         words = (yield)
    #         tagged_words = nltk.pos_tag(words)
    #
    #         for target in targets:
    #             target.send(tagged_words)
    #
    # @coroutine
    # def named_entity_chunk_pipeline(self, targets):
    #     '''Pipeline for named-entity chunking.
    #     '''
    #     while True:
    #         tagged_words = (yield)
    #         ner_tagged = nltk.ne_chunk(tagged_words)
    #
    #         for target in targets:
    #             target.send(ner_tagged)


def main():
    pass

if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
