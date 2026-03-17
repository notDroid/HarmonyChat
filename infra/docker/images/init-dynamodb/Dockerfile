FROM python:3.11-alpine

WORKDIR /app

RUN pip install --no-cache-dir boto3

COPY scripts/init_dynamodb.py .

CMD ["python", "init_dynamodb.py"]