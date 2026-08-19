FROM python:3.11-slim
RUN useradd --create-home --uid 10001 horde
WORKDIR /app
COPY pyproject.toml README.md /app/
COPY src /app/src
RUN pip install --no-cache-dir .
USER horde
ENV HORDE_DATA_DIR=/var/lib/horde HORDE_EXECUTE_TOOLS=false
VOLUME ["/var/lib/horde"]
ENTRYPOINT ["horde"]
