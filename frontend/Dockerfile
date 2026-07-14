FROM node:22-slim AS builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
RUN npm run build

FROM node:22-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./
COPY --from=builder /app/public ./public 2>/dev/null || true
EXPOSE 3000
# ASK_API_URL and ASK_API_KEY are read server-side at runtime (not build
# time) by app/api/[...path]/route.ts, so they never end up in the client
# bundle. Set them when running the container, e.g.:
#   docker run -e ASK_API_URL=http://ask-api:8000 -e ASK_API_KEY=... ask-web
CMD ["npm", "start"]
