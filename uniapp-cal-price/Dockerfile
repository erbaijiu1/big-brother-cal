# uniapp-cal-price/Dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY . .
RUN npm install && npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
# 如果有自定义 nginx.conf，放在 uniapp-cal-price 目录下
COPY ./nginx.conf /etc/nginx/conf.d/default.conf
