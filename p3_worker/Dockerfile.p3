FROM python:3.11-slim
WORKDIR /app
COPY p3.py ./
COPY .env ./
RUN pip install --no-cache-dir boto3 python-dotenv
CMD ["python", "p3.py"]
