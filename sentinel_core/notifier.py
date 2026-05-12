import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_email(subject: str, html_body: str, to_email: str = None):
    TARGET_EMAIL = os.getenv("EMAIL_RECIPIENT", "shivau1006@gmail.com")
    final_to_email = to_email or TARGET_EMAIL
    SMTP_SERVER = os.getenv("SMTP_HOST")
    SMTP_PORT = os.getenv("SMTP_PORT", "587")
    SMTP_USERNAME = os.getenv("SMTP_USER")
    
    raw_password = os.getenv("SMTP_PASSWORD", "")
    SMTP_PASSWORD = raw_password.replace(" ", "")
    
    SENDER_EMAIL = os.getenv("SMTP_USER")

    if not all([SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD, SENDER_EMAIL]):
        print("[Notifier] Warning: Missing SMTP credentials. Returning early.")
        return

    try:
        smtp_port = int(SMTP_PORT)
    except ValueError:
        smtp_port = 587

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = final_to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(html_body, 'html'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, smtp_port)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"[Notifier] Failed to send email: {e}")
