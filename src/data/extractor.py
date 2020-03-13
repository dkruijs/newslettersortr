import logging
import base64
from pathlib import Path
from src.data.get_gmails import get_mail


def extract(mail_delta):
    for id, content in mail_delta.items():
        msg_str = base64.urlsafe_b64decode(content['raw'].encode('UTF8'))
        print(msg_str)


def main():
    messages = get_mail()
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


