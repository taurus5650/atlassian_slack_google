"""
TODO: Connection works, but send email feature doesn't works.
"""
import base64
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from google.oauth2 import service_account
from googleapiclient import discovery, errors

from utility import logger, log_class

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

@log_class
class GmailSender:
    def gen_mail(self, send_from, send_to, subject, content, method="plain"):
        try:
            message = MIMEMultipart('mixed')
            message['From'] = send_from
            message['Subject'] = Header(subject, 'utf-8')
            message['To'] = send_to

            if method == "html":
                part = MIMEText(content, 'html', 'utf-8')
            else:
                part = MIMEText(content, 'plain', 'utf-8')

            message.attach(part)
            logger.debug(message)
            return message
        except Exception as error:
            logger.error(f"Error: {error}")

    def send_mail(self, config_json, user_email, send_from, msg):
        try:
            credentials = service_account.Credentials.from_service_account_info(config_json, scopes=SCOPES)
            delegated_credentials = credentials.with_subject(user_email)
            service = discovery.build('gmail', 'v1', credentials=delegated_credentials)
            message = (
                service.users().messages().send(
                    userId='me' or send_from,
                    body={'raw': base64.urlsafe_b64encode(msg.as_string().encode()).decode()
                          }).execute()
            )
            logger.debug(f"Message Id: {message['id']}")
        except errors.HttpError as err:
            logger.error(f"Error: {err}")
        except errors.Error as err:
            logger.error(f"Error: {err}")
