import logging
from pathlib import Path
from email.parser import BytesParser
from base64 import b64decode
from src.data.get_gmails import main as get_mails


def extract(mail_delta):
    extractor = BytesParser()
    for key, bytestr_msg in mail_delta:
        bit_msg = b64decode(bytestr_msg)
        msg = extractor.parsebytes(bit_msg, headersonly=False)
        print(msg)


def main():
    messages = get_mails()
    tmp = extract(messages)


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    # load_dotenv(find_dotenv())

    main()


