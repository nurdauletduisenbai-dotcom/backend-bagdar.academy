# EduPlatform Frontend (Vue 3 + Vite)
#   docker build --target dev  -> Vite dev-сервер с HMR
#   docker build --target prod -> статика за nginx

# ---------- dev ----------
FROM node:22-alpine AS dev

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 5173
CMD ["npm", "run", "dev"]

# ---------- build ----------
FROM dev AS build
RUN npm run build

# ---------- prod ----------
FROM nginx:1.27-alpine AS prod
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
