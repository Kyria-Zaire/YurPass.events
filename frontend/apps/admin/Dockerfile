# YurPass Admin — DEV mode only (TICKET-005)
FROM node:22-alpine

WORKDIR /app

ENV NEXT_TELEMETRY_DISABLED=1

RUN corepack enable && corepack prepare pnpm@10.16.1 --activate

COPY package.json pnpm-workspace.yaml pnpm-lock.yaml turbo.json ./
COPY frontend ./frontend

RUN pnpm install --frozen-lockfile

EXPOSE 3001

CMD ["pnpm", "--filter", "@yurpass/admin", "dev", "--hostname", "0.0.0.0"]
