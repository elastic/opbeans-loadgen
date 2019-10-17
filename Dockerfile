FROM python:3.7-slim

## Required as the slim version is too tiny
RUN apt-get -qq update \
 && apt-get -qq install -y \
	gcc \
    libc-dev \
    bzip2 \
    curl \
	--no-install-recommends \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/
RUN pip install -r requirements.txt

COPY molotov_scenarios.py entrypoint.sh generate_procfile.py /app/

ENV PYTHONUNBUFFERED=1

CMD ["honcho", "start"]
ENTRYPOINT ["/app/entrypoint.sh"]
