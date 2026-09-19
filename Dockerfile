# PineSentry-Fire — Streamlit demo image for HuggingFace Spaces.
#
# HF deprecated the built-in `sdk: streamlit` builder on 2025-04-30; Streamlit
# Spaces are now ordinary Docker Spaces built from this file. 8501 is the only
# port HF accepts for Streamlit and must match `app_port` in the README
# front-matter. See docs/HUGGINGFACE_SPACES.md.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

# curl is only here for the healthcheck below.
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

# Deps in their own layer so editing the app or the figures does not
# reinstall streamlit on every push.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "streamlit_app/app.py", \
            "--server.port=8501", "--server.address=0.0.0.0"]
