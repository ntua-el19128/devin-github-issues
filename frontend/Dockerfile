FROM node:18 AS build

WORKDIR /frontend
COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# Nginx to serve static files
FROM nginx:alpine

COPY --from=build /frontend/dist /usr/share/nginx/html

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
