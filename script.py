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

# Input email addresses
email_addresses = st.text_input("Enter recipient email address(es) (comma-separated):")

# File uploader for multiple files
uploaded_files = st.file_uploader("Upload documents", type=["pdf", "docx", "txt", "jpg", "png"], accept_multiple_files=True)

# Clear telegram_sent flag every time new files are uploaded
if uploaded_files:
    st.session_state["telegram_sent"] = False

if uploaded_files and not st.session_state["telegram_sent"]:
    st.success(f"Uploaded {len(uploaded_files)} file(s) successfully!")

    # Automatically send files to Telegram
    def send_telegram(file_name, file_content):
        for chat_id in TELEGRAM_CHAT_IDS:
            try:
                files = {"document": (file_name, io.BytesIO(file_content))}
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
                data = {"chat_id": chat_id.strip()}
                response = requests.post(url, data=data, files=files)

                if response.status_code == 200:
                    st.success(f"Document '{file_name}' sent to Telegram chat ID {chat_id.strip()} successfully!")
                else:
                    st.error(f"Failed to send document '{file_name}' to Telegram chat ID {chat_id.strip()}: {response.text}")
            except Exception as e:
                st.error(f"Failed to send document '{file_name}' to Telegram chat ID {chat_id.strip()}: {e}")

    for uploaded_file in uploaded_files:
        file_name = uploaded_file.name
        file_content = uploaded_file.read()
        send_telegram(file_name, file_content)

    # Mark Telegram files as sent
    st.session_state["telegram_sent"] = True

# Ask before sending files via Email
def send_email_with_all_files(uploaded_files, recipient_emails):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = ', '.join(recipient_emails)
        msg['Subject'] = "Documents from Streamlit App"

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

if st.button("Send All via Email"):
    if email_addresses:
        recipient_emails = [email.strip() for email in email_addresses.split(',')]
        send_email_with_all_files(uploaded_files, recipient_emails)
    else:
        st.error("Please enter at least one email address.")
