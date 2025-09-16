import os
import boto3
import json
from dotenv import load_dotenv

load_dotenv()

# AWS setup
sqs = boto3.client('sqs', region_name=os.getenv("AWS_REGION"))
ses = boto3.client('ses', region_name=os.getenv("AWS_REGION"))
queue_url = os.getenv("SQS_P3_URL")

# Email config
sender = os.getenv("SES_EMAIL_SOURCE")
recipients = [os.getenv("SES_EMAIL_RECIPIENT")]


def format_email(ticket):
    subject = f"[{ticket['priority']}] New IT Ticket: {ticket['title']}"
    text = f"""
    A new ticket has been submitted.

    Title: {ticket['title']}
    Description: {ticket['description']}
    Priority: {ticket['priority']}
    """
    html = f"""
    <html>
    <body>
        <h2>New P3 Ticket</h2>
        <p><strong>Title:</strong> {ticket['title']}</p>
        <p><strong>Description:</strong> {ticket['description']}</p>
        <p><strong>Priority:</strong> {ticket['priority']}</p>
    </body>
    </html>
    """
    return subject, text, html


def send_email(subject, text, html):
    response = ses.send_email(
        Source=sender,
        Destination={'ToAddresses': recipients},
        Message={
            'Subject': {'Data': subject},
            'Body': {
                'Text': {'Data': text},
                'Html': {'Data': html}
            }
        }
    )
    print("SES response:", response['MessageId'])


def run_worker():
    print("P3 worker started. Listening for tickets...")
    while True:
        response = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=10
        )
        messages = response.get("Messages", [])
        for msg in messages:
            try:
                ticket = json.loads(msg["Body"])
                required_keys = {"title", "description", "priority"}
                if not isinstance(ticket, dict) or not required_keys.issubset(ticket.keys()):
                    print("Skipping invalid ticket:", msg["Body"])
                    continue

                print("Processing ticket:", ticket)
                subject, text, html = format_email(ticket)
                send_email(subject, text, html)

                sqs.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=msg["ReceiptHandle"]
                )

            except Exception as err:
                print("Error processing message:", err)

if __name__ == "__main__":
    run_worker()
