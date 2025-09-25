import logging
import sendgrid
import os
from sendgrid.helpers.mail import Mail, Email, To, PlainTextContent, HtmlContent

if os.environ.get('ENV') != "production":
    from dotenv import load_dotenv
    load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def run(event, context):
    try:
        sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
        mail = Mail(
            from_email = Email(os.environ.get('FROM_EMAIL_ADDRESS'), os.environ.get('FROM_EMAIL_NAME')),
            to_emails = To(os.environ.get('TO_EMAIL')),
            subject = "Weekly Report — Your AWS Billing Summary",
            plain_text_content = PlainTextContent('and easy to do anywhere, even with Python'),
            html_content = HtmlContent('<strong>and easy to do anywhere, even with Python</strong>')
        )

        mail_json = mail.get()

        response = sg.client.mail.send.post(request_body=mail_json)
        print(response.status_code)
        print(response.headers)
    except Exception as e:
        print(e.message)

if __name__ == "__main__":
    run()
