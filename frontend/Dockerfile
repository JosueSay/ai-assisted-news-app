FROM node:24-bookworm-slim AS development

ENV EXPO_NO_TELEMETRY=1 \
    npm_config_update_notifier=false

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

RUN chown -R node:node /app
USER node

EXPOSE 8081 19000 19001 19002 19006

CMD ["npm", "start", "--", "--host", "lan", "--port", "8081"]
