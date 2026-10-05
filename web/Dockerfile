#
# Web image of Agilina. Targets:
#
#   dev    `ng serve` with live reload; src/ and public/ are bind-mounted.
#          config.json is rendered from the environment before serving.
#   test   dev plus Chromium, to run the Karma tests headless.
#   prod   the production build served by an unprivileged nginx, which renders
#          config.json from the environment when the container starts.
#
# Build context: web/
ARG NODE_VERSION=22

# --------------------------------------------------------------------- deps --
FROM node:${NODE_VERSION}-bookworm-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./
# `npm ci` installs exactly what package-lock.json pins and fails if it does not match
# package.json (run `make lock`).
RUN npm ci

# ---------------------------------------------------------------------- dev --
FROM deps AS dev
COPY . .
EXPOSE 4200
# 0.0.0.0 so the browser on the host can reach the dev server in the container.
CMD ["sh", "-c", "node scripts/render-runtime-config.mjs && exec npx ng serve --host 0.0.0.0 --port 4200"]

# --------------------------------------------------------------------- test --
FROM dev AS test
RUN apt-get update \
    && apt-get install -y --no-install-recommends chromium \
    && rm -rf /var/lib/apt/lists/*
ENV CHROME_BIN=/usr/bin/chromium
CMD ["npm", "run", "test:container"]

# -------------------------------------------------------------------- build --
FROM dev AS build
RUN npm run build

# --------------------------------------------------------------------- prod --
FROM nginxinc/nginx-unprivileged:1.27-alpine AS prod
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY security-headers.conf /etc/nginx/security-headers.conf
# The image's entrypoint runs envsubst on /etc/nginx/templates/*.template at startup
# and writes the result to NGINX_ENVSUBST_OUTPUT_DIR; nginx.conf serves it as
# /config.json. Same template that scripts/render-runtime-config.mjs uses in dev.
ENV NGINX_ENVSUBST_OUTPUT_DIR=/etc/nginx/runtime
RUN mkdir -p /etc/nginx/runtime
COPY runtime-config.template.json /etc/nginx/templates/config.json.template
COPY --from=build /app/dist/agilina-web/browser /usr/share/nginx/html
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=3s --retries=5 \
    CMD wget -qO- http://localhost:8080/ >/dev/null || exit 1
