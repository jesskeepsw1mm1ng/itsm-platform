from flask import Flask, render_template, request, redirect, url_for, flash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import boto3, json, os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "super-secret-key")

# Rate limiter setup
limiter = Limiter(get_remote_address, app=app)

# AWS SQS setup
sqs = boto3.client('sqs', region_name=os.getenv("AWS_REGION"))

@app.route("/")
def index():
    return render_template("submit_ticket.html")

@app.route("/submit", methods=["POST"])
@limiter.limit("5 per minute")  # Only limit ticket submissions
def submit_ticket():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    priority = request.form.get("priority", "").strip()

    if not title or not description or priority not in {"P1", "P2", "P3"}:
        flash("Please fill out all fields correctly.")
        return redirect(url_for("index"))

    ticket = {
        "title": title,
        "description": description,
        "priority": priority
    }

    queue_map = {
        "P1": os.getenv("SQS_P1_URL"),
        "P2": os.getenv("SQS_P2_URL"),
        "P3": os.getenv("SQS_P3_URL")
    }
    queue_url = queue_map.get(priority)

    if not queue_url:
        flash("No queue URL found for selected priority.")
        return redirect(url_for("index"))

    try:
        sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(ticket))
        flash(f"Ticket submitted to {priority} queue successfully")
    except Exception as e:
        flash(f"Failed to submit ticket: {str(e)}")

    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
