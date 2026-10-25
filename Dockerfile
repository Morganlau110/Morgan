FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY sros_audit ./sros_audit
RUN pip install --no-cache-dir . && useradd --uid 10001 --create-home auditor
COPY examples ./examples
RUN mkdir reports && chown auditor:auditor reports
USER auditor
ENTRYPOINT ["python", "-m", "sros_audit"]
