import os, json, boto3
from dotenv import load_dotenv

load_dotenv()

sqs = boto3.client('sqs', region_name=os.getenv("AWS_REGION"))
dlq_url = os.getenv("SQS_DLQ_URL")

# map priorities to queues
priority_map = {
    "P1": os.getenv("SQS_P1_URL"),
    "P2": os.getenv("SQS_P2_URL"),
    "P3": os.getenv("SQS_P3_URL")
}

def inspect_dlq():
    print("Inspecting DLQ...")
    response = sqs.receive_message(
        QueueUrl=dlq_url,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=10
    )
    messages = response.get("Messages", [])
    for msg in messages:
        body = msg["Body"]
        print("DLQ Message:", body)

        try:
            ticket = json.loads(body)
            priority = ticket.get("priority")
            target_queue = priority_map.get(priority)

            if target_queue:
                print(f"Replaying ticket to {priority} queue...")
                sqs.send_message(QueueUrl=target_queue, MessageBody=json.dumps(ticket))
            else:
                print("Unknown priority, skipping replay.")

            sqs.delete_message(QueueUrl=dlq_url, ReceiptHandle=msg["ReceiptHandle"])

        except Exception as e:
            print("Error processing DLQ message:", e)
            print("Raw body:", body)

if __name__ == "__main__":
    inspect_dlq()
