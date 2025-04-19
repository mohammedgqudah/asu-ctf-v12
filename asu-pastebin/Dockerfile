FROM node:23
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/


# Install Python and pip
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
	nginx

RUN apt-get install -yq gconf-service libasound2 libatk1.0-0 libc6 libcairo2 \
    libcups2 libdbus-1-3 libexpat1 libfontconfig1 libgbm1 libgcc1 libgconf-2-4 \
    libgdk-pixbuf2.0-0 libglib2.0-0 libgtk-3-0 libnspr4 libpango-1.0-0 \ 
    libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 \ 
    libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 \ 
    libxss1 libxtst6 ca-certificates fonts-liberation libnss3 lsb-release \
    xdg-utils wget

RUN pip install supervisor --break-system-packages

WORKDIR /bot

COPY ./bot /bot/
RUN npm ci

WORKDIR /app

COPY ./config/supervisord.conf /etc/supervisor/supervisord.conf
COPY ./config/nginx.conf /etc/nginx/nginx.conf

COPY ./pastebin /app/

RUN uv sync --frozen --no-dev
ENV PATH="/app/.venv/bin:$PATH"

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

CMD ["supervisord", "-c", "/etc/supervisor/supervisord.conf"]
