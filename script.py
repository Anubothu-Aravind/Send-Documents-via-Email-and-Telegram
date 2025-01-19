import streamlit as st
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import io
import requests
from dotenv import load_dotenv
import os

# Load secrets from .env file
load_dotenv()

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_IDS = os.getenv('TELEGRAM_CHAT_IDS', '').split(',')  # Comma-separated list

# Email Configuration
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))

st.title("Send Documents via Email and Telegram")

# Initialize session state
if "sent_files" not in st.session_state:
    st.session_state["sent_files"] = set()  # Track sent files by name

# Input email addresses
email_addresses = st.text_input("Enter recipient email address(es) (comma-separated):")

# File uploader for multiple files
uploaded_files = st.file_uploader("Upload documents", type=["pdf", "docx", "txt", "jpg", "png"], accept_multiple_files=True)

# Function to send files via Telegram
def send_telegram(uploaded_files):
    for uploaded_file in uploaded_files:
        file_name = uploaded_file.name
        file_content = uploaded_file.read()

        # Skip already sent files
        if file_name in st.session_state["sent_files"]:
            continue

        try:
            for chat_id in TELEGRAM_CHAT_IDS:
                files = {"document": (file_name, io.BytesIO(file_content))}
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
                data = {"chat_id": chat_id.strip()}
                response = requests.post(url, data=data, files=files)

                if response.status_code == 200:
                    st.success(f"Document '{file_name}' sent to Telegram chat ID {chat_id.strip()} successfully!")
                    st.session_state["sent_files"].add(file_name)  # Mark as sent
                else:
                    st.error(f"Failed to send document '{file_name}' to Telegram chat ID {chat_id.strip()}: {response.text}")
        except Exception as e:
            st.error(f"Failed to send document '{file_name}' to Telegram: {e}")

# Automatically send new files via Telegram
if uploaded_files:
    send_telegram(uploaded_files)

# Function to send files via Email
def send_email_with_all_files(uploaded_files, recipient_emails):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = ', '.join(recipient_emails)
        msg['Subject'] = "New File Detected At The Destined Area"

        for uploaded_file in uploaded_files:
            file_name = uploaded_file.name
            file_content = uploaded_file.read()

            # Attach file
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(file_content)
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{file_name}"')
            msg.attach(part)

        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        st.success("All documents sent via email successfully!")
    except Exception as e:
        st.error(f"Failed to send email: {e}")

# Button to send files via Email
if st.button("Send All via Email"):
    if uploaded_files:
        if email_addresses:
            recipient_emails = [email.strip() for email in email_addresses.split(',')]
            send_email_with_all_files(uploaded_files, recipient_emails)
        else:
            st.error("Please enter at least one email address.")
    else:
        st.error("Please upload at least one file to send via Email.")
