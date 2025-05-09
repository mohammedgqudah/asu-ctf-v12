FROM node:23
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/


# Install Python and pip
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
	nginx

RUN pip install supervisor --break-system-packages

WORKDIR /app

COPY ./config/supervisord.conf /etc/supervisor/supervisord.conf

COPY ./app /app/

RUN uv sync --frozen --no-dev
ENV PATH="/app/.venv/bin:$PATH"


# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []
EXPOSE 5002
ENV C_FORCE_ROOT=1
CMD ["supervisord", "-c", "/etc/supervisor/supervisord.conf"]
