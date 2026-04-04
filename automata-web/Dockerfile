# 生产镜像：npm run build 使用 Vite mode=production，自动加载 .env.production（及 .env.production.local 若存在）
FROM node:24-alpine AS builder

WORKDIR /app

COPY package*.json /app/
RUN npm ci

COPY . /app
# CI 可覆盖：与 .env.production 中注释一致；空则运行时仍用 window.location.origin
ARG VITE_PUBLIC_SITE_ORIGIN=
ENV VITE_PUBLIC_SITE_ORIGIN=$VITE_PUBLIC_SITE_ORIGIN
RUN npm run build

FROM nginx:1.27-alpine

RUN apk add --no-cache tzdata
ENV TZ=Asia/Shanghai

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
