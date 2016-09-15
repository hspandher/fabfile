import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from . import config

def send_mail(to_address, subject, message, from_address = config.SERVER_EMAIL, is_html = False):
    smtp_server = smtplib.SMTP(host = config.EMAIL_HOST, port = config.EMAIL_PORT)

    body = MIMEMultipart()

    body['From'] = from_address
    body['To'] = to_address
    body['Subject'] = subject

    message_type = 'text/html' if is_html else 'plain'

    body.attach(MIMEText(message, message_type))

    with smtplib.SMTP(host = config.EMAIL_HOST, port = config.EMAIL_PORT) as smtp_server:
        return smtp_server.sendmail(from_address, to_address, body.as_string())
