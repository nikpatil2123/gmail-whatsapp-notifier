import os
import base64
import logging
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import schedule
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Gmail API setup
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Direct configuration
TWILIO_ACCOUNT_SID = 'ACbbf76566f82a6e3299ad12cca12a860d'
TWILIO_AUTH_TOKEN = '1fc6a09afc047fbd69a4fd829b4b1db6'
TWILIO_WHATSAPP_NUMBER = 'whatsapp:+14155238886'
TO_WHATSAPP_NUMBER = 'whatsapp:+917096589655'
CHECK_INTERVAL = 1  # Changed to 1 minute for faster checking
MAX_RETRIES = 3

def get_gmail_service():
    creds = None
    if os.path.exists('token.json'):
        try:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        except Exception as e:
            logger.error(f"Error reading token file: {e}")
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.error(f"Error refreshing credentials: {e}")
        else:
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                logger.error(f"Error in authentication flow: {e}")
                return None
    
    return build('gmail', 'v1', credentials=creds)

def get_email_body(service, msg_id):
    try:
        message = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
        if 'payload' in message:
            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        if 'data' in part['body']:
                            body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                            return body[:200] + '...' if len(body) > 200 else body
            elif 'body' in message['payload']:
                if 'data' in message['payload']['body']:
                    body = base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')
                    return body[:200] + '...' if len(body) > 200 else body
        return "No body content available"
    except Exception as e:
        logger.error(f"Error getting email body: {e}")
        return "Error retrieving email body"

def get_unread_emails(service):
    try:
        results = service.users().messages().list(
            userId='me',
            labelIds=['INBOX', 'UNREAD'],
            maxResults=10  # Limit to 10 results
        ).execute()
        messages = results.get('messages', [])
        
        if not messages:
            logger.info('No unread messages found.')
            return []
        
        unread_emails = []
        for message in messages[:10]:  # Process only first 10 messages
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            email_data = {
                'id': msg['id'],
                'timestamp': datetime.fromtimestamp(int(msg['internalDate'])/1000).strftime('%Y-%m-%d %H:%M:%S'),
                'body': get_email_body(service, msg['id'])
            }
            
            headers = msg['payload']['headers']
            for header in headers:
                if header['name'] == 'From':
                    email_data['sender'] = header['value']
                if header['name'] == 'Subject':
                    email_data['subject'] = header['value']
            
            unread_emails.append(email_data)
        
        return unread_emails
    
    except Exception as e:
        logger.error(f'Error fetching emails: {e}')
        return []

def send_whatsapp_message(message, retry_count=0):
    if retry_count >= MAX_RETRIES:
        logger.error(f"Max retries ({MAX_RETRIES}) reached for message")
        return False

    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=message,
            from_=TWILIO_WHATSAPP_NUMBER,
            to=TO_WHATSAPP_NUMBER
        )
        logger.info(f'WhatsApp message sent: {message.sid}')
        return True
    except TwilioRestException as e:
        logger.error(f'Twilio error: {str(e)}')
        time.sleep(2 ** retry_count)
        return send_whatsapp_message(message, retry_count + 1)
    except Exception as e:
        logger.error(f'Unexpected error sending WhatsApp message: {str(e)}')
        return False

def check_and_notify():
    logger.info('Checking for new emails...')
    service = get_gmail_service()
    if not service:
        logger.error("Failed to initialize Gmail service")
        return

    unread_emails = get_unread_emails(service)
    print(f"Found {len(unread_emails)} unread emails")  # Debug line
    
    for email in unread_emails:
        message = (
            f"📧 New Email\n"
            f"From: {email['sender']}\n"
            f"Subject: {email['subject']}\n"
            f"Time: {email['timestamp']}\n"
            f"Preview: {email['body']}"
        )
        
        if send_whatsapp_message(message):
            try:
                service.users().messages().modify(
                    userId='me',
                    id=email['id'],
                    body={'removeLabelIds': ['UNREAD']}
                ).execute()
                logger.info(f"Marked email {email['id']} as read")
            except Exception as e:
                logger.error(f"Error marking email as read: {e}")

def main():
    logger.info("Starting Email to WhatsApp notification service...")
    schedule.every(CHECK_INTERVAL).minutes.do(check_and_notify)
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}")

if __name__ == '__main__':
    check_and_notify()  # Immediate first check
    main()
