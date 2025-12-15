import smtplib
from email.mime.text import MIMEText

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# These must be your Gmail credentials
SENDER_EMAIL = "geetaglory96339@gmail.com"
SENDER_PASS = "qwctfmkrjrwiuamg"  # Use 16-digit app password

def send_email(to_email, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASS)
        server.sendmail(SENDER_EMAIL, [to_email], msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print("Email send failed:", e)
        return False
