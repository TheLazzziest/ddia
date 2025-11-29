FROM python:3.12-slim

#Install protoc compiler
RUN apt-get update && apt-get install -y protobuf-compiler && rm -rf /var/lib/apt/lists/*

WORKDIR /app

#Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#Copy the source code
COPY . .

CMD ["python3"]