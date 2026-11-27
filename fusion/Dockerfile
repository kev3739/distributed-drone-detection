# Built from the repo root (it needs both fusion/ and schemas/)
FROM python:3.12-slim
WORKDIR /app
COPY fusion/requirements.txt fusion/requirements.txt
RUN pip install --no-cache-dir -r fusion/requirements.txt
COPY schemas schemas
COPY fusion fusion
WORKDIR /app/fusion
CMD ["python", "-u", "service.py"]
