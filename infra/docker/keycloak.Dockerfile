#
# Keycloak with the Agilina login theme.
#
# The theme's stylesheet is built with the Tailwind CLI from the same tokens as the web
# (web/src/tokens.css), so the login and the application cannot drift apart. Only the compiled
# theme reaches the final image; nothing generated is versioned.
#
# Build context: the repository root.
ARG KEYCLOAK_VERSION=26.0

# -------------------------------------------------------------------- theme --
FROM node:22-bookworm-slim AS theme
WORKDIR /app/web

# The web's dependencies and lock file: the same Tailwind version as the application.
COPY web/package.json web/package-lock.json ./
RUN npm ci

COPY web/src/tokens.css src/tokens.css
COPY web/public/favicon.svg /tmp/favicon.svg
COPY infra/keycloak/theme.css theme.css
COPY infra/keycloak/themes /app/infra/keycloak/themes

# The stylesheet, the two fonts it names and the favicon, next to the templates.
RUN set -eu; \
    resources=/app/infra/keycloak/themes/agilina/login/resources; \
    mkdir -p "$resources/css" "$resources/fonts" "$resources/img"; \
    npx @tailwindcss/cli --input theme.css --output "$resources/css/agilina.css" --minify; \
    cp node_modules/@fontsource-variable/inter/files/inter-latin-wght-normal.woff2 "$resources/fonts/"; \
    cp node_modules/@fontsource-variable/plus-jakarta-sans/files/plus-jakarta-sans-latin-wght-normal.woff2 "$resources/fonts/"; \
    cp /tmp/favicon.svg "$resources/img/favicon.svg"

# ----------------------------------------------------------------- keycloak --
FROM quay.io/keycloak/keycloak:${KEYCLOAK_VERSION}
COPY --from=theme /app/infra/keycloak/themes/agilina /opt/keycloak/themes/agilina
