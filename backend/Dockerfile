ARG PYTHON_IMAGE=python:3.11-slim
FROM ${PYTHON_IMAGE}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Shanghai

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir \
    --index-url https://mirrors.aliyun.com/pypi/simple/ \
    --trusted-host mirrors.aliyun.com \
    -r requirements.txt

COPY app ./app
COPY database ./database

RUN groupadd --gid 10001 auditpro \
    && useradd --uid 10001 --gid auditpro --no-create-home --shell /usr/sbin/nologin auditpro \
    && mkdir -p /data/auditpro/uploads \
    && chown -R auditpro:auditpro /app /data/auditpro/uploads

USER auditpro

EXPOSE 38808

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:38808/health', timeout=3)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "38808", "--workers", "1"]
