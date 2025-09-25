import logging
import os
from decimal import Decimal
from datetime import date, timedelta
import boto3
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, PlainTextContent, HtmlContent

if os.environ.get('ENV') != "production":
    from dotenv import load_dotenv
    load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class TextContent:
    def __init__(self, type):
        match type:
            case 'text/plain':
                with open('./mail/text_plain.txt') as f:
                    __read_data = f.read()
                    self.plain_text = __read_data[:]
            case 'text/html':
                with open('./mail/text_html.html') as f:
                    __read_data = f.read()
                    self.html_text = __read_data[:]
            case _:
                raise Exception()


def run(event, context):
    try:
        today = date.today()

        client = boto3.client('ce')
        response = client.get_cost_and_usage(
            TimePeriod={
                'Start': (today - timedelta(days=7)).strftime('%Y-%m-%d'),
                'End': today.strftime('%Y-%m-%d')
            },
            Granularity='MONTHLY',
            Metrics=[
                'BlendedCost'
            ],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ]
        )

        print(response)

        text = TextContent('text/plain').plain_text
        html = TextContent('text/html').html_text
        list_text = []
        list_html = []
        total = Decimal('0')
        has_other_than_usd = False
        for group in response['ResultsByTime'][0]['Groups']:
            key = group['Keys'][0]
            amount = Decimal(group['Metrics']['BlendedCost']['Amount'])
            unit = group['Metrics']['BlendedCost']['Unit']

            total += amount
            list_text.append(f'{key}: {amount} {unit}')
            list_html.append(f'<p><strong>{key}</strong>: {amount} {unit}</p>')

            if unit != 'USD':
                has_other_than_usd = True
        
        text += '\n'.join(list_text)
        html += ''.join(list_html)

        if not has_other_than_usd:
            text += f'\nTotal: {total} USD'
            html += f'<p><strong>Total: {total} USD</strong></p>'

                

        sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
        mail = Mail(
            from_email = Email(os.environ.get('FROM_EMAIL_ADDRESS'), os.environ.get('FROM_EMAIL_NAME')),
            to_emails = To(os.environ.get('TO_EMAIL')),
            subject = "Weekly Report — Your AWS Billing Summary",
            plain_text_content = PlainTextContent(text),
            html_content = HtmlContent(html)
        )

        mail_json = mail.get()

        response = sg.client.mail.send.post(request_body=mail_json)
        print(response.status_code)
        print(response.headers)
    except Exception as e:
        print(e.message)

if __name__ == "__main__":
    run(None, None)
