FROM python:3.12-slim
WORKDIR /app
COPY tools/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY tools/test_publisher.py .
ENTRYPOINT ["python", "-u", "test_publisher.py"]
