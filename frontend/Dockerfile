# Build stage
FROM node:18-alpine as build-stage
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Production stage
FROM nginx:stable-alpine as production-stage
COPY --from=build-stage /app/dist /usr/share/nginx/html
# 复制自定义 Nginx 配置（如果有的话，这里我们先用默认的，稍后可能需要处理路由 fallback）
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
