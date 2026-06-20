FROM node:22-alpine AS build

WORKDIR /app

ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL
ARG VITE_DELIVERY_PANEL_URL
ENV VITE_DELIVERY_PANEL_URL=$VITE_DELIVERY_PANEL_URL
ARG VITE_SHOP_OWNER_PANEL_URL
ENV VITE_SHOP_OWNER_PANEL_URL=$VITE_SHOP_OWNER_PANEL_URL

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

FROM nginx:1.27-alpine

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
