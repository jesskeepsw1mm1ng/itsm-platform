import requests, os, json, boto3, ast
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

load_dotenv()

# AWS SQS setup
sqs = boto3.client('sqs', region_name=os.getenv("AWS_REGION"))
queue_url = os.getenv("SQS_P2_URL")

# Jira setup
jira_domain = os.getenv("JIRA_DOMAIN")
jira_email = os.getenv("JIRA_EMAIL")
jira_token = os.getenv("JIRA_API_TOKEN")
jira_project_key = os.getenv("JIRA_PROJECT_KEY")

jira_url = f"https://{jira_domain}/rest/api/3/issue"
auth = HTTPBasicAuth(jira_email, jira_token)

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

priority_map = {
    "P1": "Highest",
    "P2": "Medium",
    "P3": "Low"
}


def safe_parse(body):
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return ast.literal_eval(body)


def format_description_adf(text):
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": text.strip()
                    }
                ]
            }
        ]
    }


def forward_to_jira(ticket):
    payload = {
        "fields": {
            "project": { "key": jira_project_key },
            "summary": ticket["title"].strip(),
            "description": format_description_adf(ticket["description"]),
            "issuetype": { "name": "Task" },
            "priority": { "name": priority_map.get(ticket["priority"], "Medium") }
        }
    }

    print("Sending payload to Jira:", json.dumps(payload))
    response = requests.post(jira_url, headers=headers, auth=auth, data=json.dumps(payload))
    print("Jira response:", response.status_code)
    if response.status_code == 201:
        print("Ticket created in Jira")
    else:
        print("Jira error:", response.text)


def run_worker():
    print("P2 worker started. Listening for tickets...")
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
                ticket = safe_parse(raw_body)

                if not isinstance(ticket, dict):
                    print("Skipping invalid ticket (not a dict):", raw_body)
                    continue

                required_keys = {"title", "description", "priority"}
                if not required_keys.issubset(ticket.keys()):
                    print("Skipping ticket with missing fields:", ticket)
                    continue

                print("Processing ticket:", ticket)
                forward_to_jira(ticket)

                sqs.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=msg["ReceiptHandle"]
                )

            except Exception as err:
                print("Error processing message:", err)
                print("Raw message body:", msg.get("Body"))

if __name__ == "__main__":
    run_worker()
