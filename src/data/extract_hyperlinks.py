import email
import logging
import base64
import re
from requests import get
from pathlib import Path

# see https://stackoverflow.com/questions/39373243/what-is-the-encoding-of-the-body-of-gmail-message-how-to-decode-it
# TODO: Make sure solution handless mime and non-mime


class InboxDelta:

    def __init__(self, msg_dict):
        self.retrieved = msg_dict
        self.string_msgs = self.extract(self.retrieved)
        self.hyperlinks = self.parse(self.string_msgs)

    def extract(self, raw_msgs):
        """
        :param raw_msgs: A dictionary of raw e-mail messages retrieved from the gmail API, with structure {gmail_msg_id:
        raw_msg_bytestring}

        Takes a dict of raw messages, decodes them from base64 into utf-8, reads them into e-mail messages using the
        email library with the appropriate policy, and parses them. Parsing involves walking through a multipart
        structure and extracting the text if the message is multipart, or extracting the text if otherwise. As per
        Todor Minakov's answer at https://stackoverflow.com/questions/17874360/python-how-to-parse-the-body-from-a-raw-email-given-that-raw-email-does-not
        Then parses the e-mail line endings from the file and stores the resulting string in a dict with structure
        {msg_id: parsed string}.

        :return extract_store: A dict of email message strings with structure {msg_id: parsed string}.
        """
        extract_store = {}
        for msg_id, content in raw_msgs.items(): # TODO: Make sure this handles NoneType for msgs
            msg_str = base64.urlsafe_b64decode(content['raw'].encode('UTF8'))
            b = email.message_from_bytes(msg_str, policy=email.policy.SMTPUTF8)
            body = ""
            if b.is_multipart():
                for part in b.walk():
                    ctype = part.get_content_type()
                    cdispo = str(part.get('Content-Disposition'))

                    # skip any text/plain (txt) attachments
                    if ctype == 'text/plain' and 'attachment' not in cdispo:
                        body = part.get_payload(decode=True)  # decode
                        extract_store[msg_id] = body
                        continue
            # not multipart - i.e. plain text, no attachments, keeping fingers crossed
            else:
                body = b.get_payload(decode=True)
                extract_store[msg_id] = body
        for key, val in extract_store.items():
            val_parsed = re.sub('\r\n', ' ', val.decode("utf-8"))
            extract_store[key] = val_parsed
        return extract_store

    def parse(self, string_msg_dict):
        """
        :param string_msg_dict: A dictionary of string e-mail messages, with structure {gmail_msg_id:
        content_string}

        Takes a dictionary of extracted e-mail messages that have been processed to strings, parses out a link starting
         with 'https://', cleans the link according to a number of selection rules, and returns a list of hyperlinks.

        :return msg_hyperlink_store: A list of hyperlinks extrated from e-mail messages, not including mails from
        google or subscription related mails.
        """
        parsed_list = []
        msg_hyperlink_store = []
        for key, msg_string in string_msg_dict.items():
            msg_word_list = msg_string.split(" ")
            hyperlink_list = [word for word in msg_word_list if 'http' in word]
            for link in hyperlink_list:
                if re.match('.*\(http.*://', link):
                    link = link.split(sep='(')[1]
                    link = link.rsplit(sep=')')[0]
                parsed_list.append(link)
        checklist = []
        for link in parsed_list:
            if (link not in checklist) and \
                ('accounts.google.com' not in link) and \
                ('subscr' not in link) and \
                ('aiohttp' not in link) and \
                ('http' in link) and \
                ('://' in link): # TODO: Into config for rules related to the various newsletter configurations
                try:
                    code = get(link).status_code
                except:
                    code = 201
                if code == 200:
                    msg_hyperlink_store.append(link) # TODO: Consider adding a header based check for valid url using requests (but perhaps not given higher amount of website calls)
                    checklist.append(link)
        print("Hyperlinks extracted")
        return msg_hyperlink_store


def main():
    pass

if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    # load_dotenv(find_dotenv())

    main()


