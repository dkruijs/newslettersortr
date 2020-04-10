# -*- coding: utf-8 -*-
import click
import logging
import json
from pathlib import Path
from dotenv import find_dotenv, load_dotenv
import pickle
import os
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient import errors
from google.cloud import storage    


class GMailGetter:  
    def __init__(self, credentials=None, run_pipeline=True):
        self.service = self.initialize_login(credentials)
        if run_pipeline:
            self.unread_messages = self.get_unread_messages()
            if self.unread_messages is not None:
                gcp_metadata = {
                    'credentials_file': os.environ['GCP_CREDENTIALS_FILE'],
                    'bucket_name': os.environ['GCP_BUCKET_NAME'],
                    'bucket_path': os.environ['GCP_BUCKET_PATH'] 
                }
                self.saved_to_disk = self.persist_to_storage(self.unread_messages, **gcp_metadata)
                self.marked_as_read = self.mark_as_read(self.unread_messages)

    def initialize_login(self, credentials):
        """
        Initializes a `service` object based on the user's credentials, requiring a manual 
        log in and authorization via a web page for the first run. Loads cached token from a local file
        on subsequent runs. Function requires a `credentials.json` file from a Google API export 
        (https://developers.google.com/gmail/api/quickstart/python).

        Args:
            credentials (credentials object) -- optional

        Returns:
            GMail API `service` object.
        """
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if credentials is not None:
            service = build('gmail', 'v1', credentials=credentials)
            return service    
        else: 
            # Reload previously stored credentials from pickle if possible;
            if os.path.exists(os.environ['TOKEN_FILE']):
                with open(os.environ['TOKEN_FILE'], 'rb') as token:
                    credentials = pickle.load(token)

            # If there are no (valid) credentials available, let the user log in manually (using a web page).
            if not credentials or not credentials.valid:
                if credentials and credentials.expired and credentials.refresh_token:
                    credentials.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        os.environ['CREDENTIALS_FILE'], os.environ['SCOPES'].split(';')) # TODO: modularize
                    credentials = flow.run_local_server(port=0)
                # Save the credentials for the next run
                with open(os.environ['TOKEN_FILE'], 'wb') as token:
                    pickle.dump(credentials, token)

            service = build('gmail', 'v1', credentials=credentials)
            return service

    def get_unread_messages(self):
        """
        Retrieves all unread messages from the connected GMail account.

        Returns:
            A collection of GMail messages (actually threads).
        """
        service = self.service
        results = service.users().messages().list(userId='me',labelIds = ['INBOX', 'UNREAD']).execute()
        messages = results.get('messages', [])

        if not messages:
            print('No unread threads found.')
            return None
        else:
            return messages

    def mark_as_read(self, messages):
        """
        Marks each in a collection of messages (actually threads) as READ in the 
        connected GMail account.
        
        Args:
            messages: collection of GMail API messages objects.

        Returns:
            processed_messages (collection of GMail API messages objects)
        """
        service = self.service
        msg_labels = {'removeLabelIds': ['UNREAD'], 'addLabelIds': []}

        processed_messages = []
        for thread in messages:
            try:
                thread = service.users().threads().modify(userId='me', id=thread['id'],
                                              body=msg_labels).execute()

                thread_id = thread['id']
                label_ids = thread['messages'][0]['labelIds']

                # TODO: convert print statments to proper logging
                print(f'Thread ID: {thread_id} - With Label IDs {label_ids}')
                processed_messages.append(thread)

            except errors.HttpError as error:
                print(f'An error occurred: {error}')

        return processed_messages

    def persist_to_storage(self, messages, local_path='../../data/raw', 
                            credentials_file=None, bucket_name=None, bucket_path=None):
        """
        Persists a collection of messages to storage as JSON text files, optionally to GCP 
        object storage or to a local path. 
        Pass the arguments `credentials_file`, `bucket_name` and `bucket_path` to store 
        to GCP; do not pass them to store to a local path.
        
        Args:
            messages: collection of GMail API messages objects.
            local_path (optional): a local path to save the files to.
            **gcp_metadata: a dictionary object with required GCP metadata.

        Returns:
            file_names: a list of processed filenames or GCP object names.
        """
        service = self.service

        if credentials_file == bucket_name == bucket_path == None:
            print(f"Persisting to local storage at: {local_path}")
            file_names = []
            for message in messages:

                # TODO: msg['payload']['headers'][ITEREER if name=Received]['value'] om de afzender op te nemen in filename
                msg = service.users().messages().get(userId='me', id=message['id']).execute()
                out_file = os.path.join(local_path, "_".join([msg['internalDate'], msg['id']])) + '.json'

                with open(out_file, "w") as file:
                    json.dump(msg, file)
                    file_names.append(file.name)

            return file_names

        else:
            print(f"Persisting to GCP Storage at {bucket_name}/{bucket_path}")

            # Explicitly use service account credentials by specifying the private key file.
            storage_client = storage.Client.from_service_account_json(
                credentials_file) 

            bucket = storage_client.get_bucket(bucket_name) 

            for message in messages:
                msg = service.users().messages().get(userId='me', id=message['id']).execute()
                out_file = os.path.join(bucket_path, "_".join([msg['internalDate'], msg['id']])) + '.json'
                blob = bucket.blob(out_file)
                print('blob:', blob)
                blob.upload_from_string(str(msg))

            return blob.public_url
        

def main():
    """
    Main function mainly demonstrates the 'normal flow', can be called to simply
    retrieve new data.
    """
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    # project_dir = Path(__file__).resolve().parents[2]

    # Load ENV configuration
    load_dotenv(find_dotenv())
    
    # We instantiate a GMailGetter without credentials, instead using 
    # the manual authentication and credentials caching logic to demonstrate 
    # the steps.
    mail_getter = GMailGetter(run_pipeline=False)

    unread_messages = mail_getter.get_unread_messages()
    print('Found unread messages:', unread_messages, '\n')

    if unread_messages is not None:
        gcp_metadata = {
            'credentials_file': '../../NewsletterSortr-c019f9f5094d.json',
            'bucket_name': 'newslettersortr',
            'bucket_path': 'data/raw/'
        }
        saved_to_disk = mail_getter.persist_to_storage(unread_messages, **gcp_metadata)
        print('Persisted to storage:', saved_to_disk, '\n')

        marked_as_read = mail_getter.mark_as_read(unread_messages)
        print('Marked as read:', marked_as_read, '\n')


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
