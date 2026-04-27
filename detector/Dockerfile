FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends iptables tini \
     && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY *.py .
RUN mkdir -p /var/log/detector
ENTRYPOINT ["/usr/bin/tini",  "--"]
CMD ["python",  "-u",  "main.py"]
