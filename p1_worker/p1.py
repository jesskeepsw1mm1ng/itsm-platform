import requests, os, json, boto3
from dotenv import load_dotenv

load_dotenv()

# Webhook and SQS setup
webhook = os.getenv("TEAMS_P1_WEBHOOK")
sqs = boto3.client('sqs', region_name=os.getenv("AWS_REGION"))
queue_url = os.getenv("SQS_P1_URL")


def forward_to_teams(ticket):
    payload = {
        "title": ticket["title"].strip(),
        "description": ticket["description"].strip().replace("\r", "").replace("\n", ""),
        "priority": ticket["priority"].strip()
    }

    headers = {
        "Content-Type": "application/json"
    }

    print("Sending payload to Teams webhook:", json.dumps(payload))
    response = requests.post(webhook, json=payload, headers=headers)
    print("Teams webhook response:", response.status_code)
    if response.status_code == 202:
        print("Webhook accepted by Power Automate (202 Accepted)")
    elif response.status_code != 200:
        print("Error posting to Teams:", response.text)


def run_worker():
    print("P1 worker started. Listening for tickets...")
    while True:
        response = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=10
        )
        messages = response.get("Messages", [])
        for msg in messages:
            try:
                raw_body = msg["Body"]
                ticket = json.loads(raw_body)

                if not isinstance(ticket, dict):
                    print("Skipping invalid ticket (not a dict):", raw_body)
                    continue

                required_keys = {"title", "description", "priority"}
                if not required_keys.issubset(ticket.keys()):
                    print("Skipping ticket with missing fields:", ticket)
                    continue

                print("Processing ticket:", ticket)
                forward_to_teams(ticket)

                sqs.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=msg["ReceiptHandle"]
                )

            except Exception as e:
                print("Error processing message:", e)
                print("Raw message body:", msg.get("Body"))

if __name__ == "__main__":
    run_worker()
