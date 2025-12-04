FROM python:3.12-slim

#Install protoc compiler
RUN apt-get update && apt-get install -y protobuf-compiler && rm -rf /var/lib/apt/lists/*

WORKDIR /app

#Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#Copy the source code
COPY . .

# Copy and make entrypoint executable
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Set entrypoint
ENTRYPOINT ["/docker-entrypoint.sh"]

CMD ["python3"]