# Email to WhatsApp Notification System

A Python-based notification system that forwards unread Gmail messages to WhatsApp using the Gmail API and Twilio WhatsApp API.

## Features

- Real-time monitoring of unread Gmail messages
- Automatic WhatsApp notifications for new emails
- Email preview with sender, subject, and body content
- Automatic marking of processed emails as read
- Robust error handling and retry mechanism
- Detailed logging system

## Prerequisites

- Python 3.6 or higher
- Gmail API credentials
- Twilio account with WhatsApp capabilities
- Google Cloud Console project with Gmail API enabled

## Required Dependencies

bash
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client twilio schedule


## Setup Instructions

1. *Go to Google Cloud Console*
    - Create a new project
    - Enable Gmail API
    - Create OAuth 2.0 credentials
    - Download credentials and save as <mark-credentials.json> in the project directory

2. *Twilio Setup*
    - Create a Twilio account
    - Enable WhatsApp sandbox
    - Update the following variables in the code:

      plaintext
      TWILIO_ACCOUNT_SID
      TWILIO_AUTH_TOKEN
      TWILIO_WHATSAPP_NUMBER
      TO_WHATSAPP_NUMBER
      

3. *Configuration*
    - Place credentials.json in the project directory
    - First run will generate token.json for Gmail authentication

## Usage

Run the script using:

```bash
python email_to_whatsapp.py
```
