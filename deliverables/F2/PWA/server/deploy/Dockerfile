# f2-api — built from pre-compiled dist/ (tsc runs on the dev machine; the box
# only needs prod deps). Context = /opt/f2-api with this file at its root.
FROM node:22-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev
COPY dist ./dist
USER node
EXPOSE 8787
CMD ["node", "dist/index.js"]
