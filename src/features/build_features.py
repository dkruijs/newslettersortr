# -*- coding: utf-8 -*-
import click
import logging
from joblib import dump, load
from pathlib import Path
from dotenv import find_dotenv, load_dotenv

# TODO: one-time NLTK resource installs. Should this be in setup.py? 
# RE: https://www.nltk.org/data.html
import nltk
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('maxent_ne_chunker')
nltk.download('words')

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
        next(cr)
        return cr
    return start


class TextProcessor:
    def __init__(self, corpus, run_pipeline=True): 
        # keys: URL, values: text
        self.corpus = corpus
        self.processed_corpus = self.processing_pipeline(corpus)
        # TODO hier iets logischers doen; pipeline is ingericht op meerdere teksten, maar willen we niet één voor één?
        # Ik mis de context hier, maar neem aan dat we het hebben over batch vs 'streaming'?
    
    @coroutine
    def source(self, texts, targets):
        for key, text in texts.items():
            for t in targets:
                t.send(text)

    def processing_pipeline(self, texts):
        self.source(texts, targets=[
            self.sent_tokenize_pipeline(targets=[
                self.printer(),  # print the raw sentences
                self.word_tokenize_pipeline(targets=[
                    self.printer(),  # print the tokenized sentences
                    self.pos_tag_pipeline(targets=[
                        self.printer(),  # print the tagged sentences
                        self.named_entity_chunk_pipeline(targets=[
                            self.printer()]), # print the chunked sentences
                    ])
                ])
            ])
        ])

    @coroutine
    def sent_tokenize_pipeline(self, targets):
        '''Pipeline for tokenizing sentences.
        '''
        while True:
            text = (yield)
            sentences = nltk.sent_tokenize(text)
            for sentence in sentences:
                for target in targets:
                    target.send(sentence)

    @coroutine
    def word_tokenize_pipeline(self, targets):
        '''Pipeline for tokenizing words.
        '''
        while True:
            sentence = (yield)
            words = nltk.word_tokenize(sentence)
            for target in targets:
                target.send(words)

    @coroutine
    def pos_tag_pipeline(self, targets):
        '''Pipeline for tagging Parts Of Speech.
        '''
        while True:
            words = (yield)
            tagged_words = nltk.pos_tag(words)
    
            for target in targets:
                target.send(tagged_words)

    @coroutine
    def named_entity_chunk_pipeline(self, targets):
        '''Pipeline for named-entity chunking.
        '''
        while True:
            tagged_words = (yield)
            ner_tagged = nltk.ne_chunk(tagged_words)
    
            for target in targets:
                target.send(ner_tagged)
    
    @coroutine
    def printer(self):
        while True:
            line = (yield)
            print(line)
    




def main():
    logger = logging.getLogger(__name__)
    logger.info('making final data set from raw data')

    # DEVELOPMENT
    corpus = load('./corpus_temp.jbl')

    tp = TextProcessor(corpus=corpus)


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
