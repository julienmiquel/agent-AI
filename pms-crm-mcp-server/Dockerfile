FROM node:22-slim
WORKDIR /app
COPY package*.json ./
RUN npm install --production --registry=https://registry.npmjs.org/
COPY dist ./dist
ENV NODE_ENV=production
ENV PORT=8080
EXPOSE 8080
CMD ["node", "dist/main.js"]
