FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

EXPOSE 3000

WORKDIR /app

ADD ./app /app

# Setup UV
RUN uv sync --frozen --no-dev
ENV PATH="/app/.venv/bin:$PATH"

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []
CMD ["uv", "run", "main.py"]
