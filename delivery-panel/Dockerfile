FROM node:22-alpine AS build

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci

WORKDIR /app/delivery-panel
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

COPY delivery-panel/ .
RUN npm run build

FROM nginx:1.27-alpine

COPY delivery-panel/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/delivery-panel/dist /usr/share/nginx/html

EXPOSE 80
