FROM python:3.11-slim
WORKDIR /app
COPY p1.py ./
COPY .env ./
RUN pip install --no-cache-dir boto3 python-dotenv requests
CMD ["python", "p1.py"]
