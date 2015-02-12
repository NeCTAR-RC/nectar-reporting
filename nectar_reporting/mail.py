from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart
import smtplib

from nectar_reporting.config import CONFIG


def send(subject, text, csv_file=None, filename=None):

    msg = MIMEMultipart('mixed')
    msg_alt = MIMEMultipart('mixed')
    msg_alt.attach(MIMEText(text, 'plain', 'utf-8'))
    msg.attach(msg_alt)
    if csv_file:
        csv_attach = MIMEText(csv_file.read(), 'csv', 'utf-8')
        if filename:
            csv_attach.add_header("Content-Disposition", "attachment",
                                  filename=filename + '.csv')
        msg.attach(csv_attach)

    msg['From'] = CONFIG.get('email', 'from')
    msg['To'] = CONFIG.get('email', 'to')
    if CONFIG.get('email', 'reply-to'):
        msg['Reply-to'] = CONFIG.get('email', 'reply-to')
    msg['Subject'] = subject

    smtp_server = CONFIG.get('email', 'server')
    s = smtplib.SMTP(smtp_server)

    s.sendmail(msg['From'], msg['to'], msg.as_string())
