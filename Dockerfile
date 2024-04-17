FROM python:3.9

WORKDIR /app
RUN python -m venv /app/venv
COPY requirements.txt /app/
RUN /app/venv/bin/pip install wheel
RUN /app/venv/bin/pip install -r requirements.txt

COPY molotov_scenarios.py entrypoint.sh generate_procfile.py /app/
COPY dyno /app/dyno
COPY scenarios/ /app/scenarios

FROM python:3.9-slim
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
