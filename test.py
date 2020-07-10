import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(subject,texttosend,recipient):
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    sender_email = "neverfullybooked@gmail.com"  # Enter your address
    receiver_email = recipient  # Enter receiver address
    password = "PythonAnywhere!"
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = "Bookish Buys"
    message["To"] = receiver_email

    text = texttosend
    html = """\
    <html>
      <body>
        <p>""" + texttosend + """\
        </p>
      </body>
    </html>
    """
    print(html)

    # Turn these into plain/html MIMEText objects
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")

    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(part1)
    message.attach(part2)

    # Create secure connection with server and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(
            sender_email, receiver_email, message.as_string()
        )