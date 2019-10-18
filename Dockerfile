FROM python:3.7

WORKDIR /app
RUN python -m venv /app/venv
COPY requirements.txt /app/
RUN /app/venv/bin/pip install -r requirements.txt

COPY molotov_scenarios.py entrypoint.sh generate_procfile.py /app/

FROM python:3.7-slim
## Required as the slim version is too tiny
RUN apt-get -qq update \
 && apt-get -qq install -y \
    bzip2 \
    curl \
	--no-install-recommends \
 && rm -rf /var/lib/apt/lists/*

COPY --from=0 /app /app
ENV PATH="/app/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
WORKDIR /app
CMD ["honcho", "start"]
ENTRYPOINT ["/app/entrypoint.sh"]
