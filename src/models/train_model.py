# -*- coding: utf-8 -*-
import click
import logging
import nltk
from pathlib import Path
from dotenv import find_dotenv, load_dotenv
from datetime import date
from gensim import models, corpora
from os.path import exists
from os import remove
from src.data.get_gmails import GMailGetter
from src.data.retrieve_text_from_link import LinkParser
from src.data.extract_hyperlinks import InboxDelta
from src.features.build_features import TextProcessor
from joblib import dump, load

# TODO: one-time NLTK resource installs. Should this be in setup.py?
# RE: https://www.nltk.org/data.html
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('maxent_ne_chunker')
nltk.download('words')
nltk.download('stopwords')


class LdaFitter:
    def __init__(self):
        self.path = "./processed_batch_" + str(date.today()) + ".txt" # TODO: Pass from pipeline persist step
        self.raw_text = self.data_load(self.path) # TODO: Reference to GCloud
        self.text_list = self.data_parse(self.raw_text)
        self.model = self.train_model(self.text_list, 20)

    def data_load(self, path):
        with open(self.path, 'r') as infile:
            full_text = ""
            for line in infile:
                full_text = full_text + str(line)
        infile.close()
        return full_text

    def data_parse(self, text):
        corpus = []
        split_text = text.split("\n\nEvert-Jan en Daan zijn absolute helden\n\n")
        for part in split_text:
            result = part.split("\n\nDeze regel gaat heel snel weer weg\n\n")
            if len(result) == 2:
                tmpstr = result[1].lstrip('[').rstrip(']').split("', '")
                corpus.append(tmpstr)
            else:
                pass
        return corpus

    def train_model(self, texts, n_topics):
        dictionary = corpora.Dictionary(texts)
        corpus = [dictionary.doc2bow(text) for text in texts]
        lda_model = models.LdaModel(corpus=corpus, num_topics=n_topics, id2word=dictionary)
        return lda_model

def main():
    logger = logging.getLogger(__name__)
    logger.info('making final data set from raw data')

    # DEVELOPMENT
    if not exists ("./parser.jbl"):
        mails = GMailGetter()
        messages = InboxDelta(mails.retrieved_delta)
        parser = LinkParser(messages.hyperlinks)
        dump(parser, "parser.jbl")
    else:
        parser = load("./parser.jbl")
    crp = parser.parse_text(parser.corpus)
    dump(crp, "./corpus_tmp.jbl")
    print("Corpus dumped.")

    fpath = "./processed_batch_" + str(
                    date.today()) + ".txt"
    if exists(fpath):
        remove(fpath)
        print("File re-initialized.")

    tp = TextProcessor(corpus=crp)

    LDA_fit = LdaFitter()
    print(LDA_fit.model)

if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()