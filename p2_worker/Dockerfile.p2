FROM python:3.11-slim
WORKDIR /app
COPY p2.py ./
COPY .env ./
RUN pip install --no-cache-dir boto3 python-dotenv requests
CMD ["python", "p2.py"]
