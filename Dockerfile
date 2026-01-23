FROM node:20-alpine AS ui-build

WORKDIR /ui
COPY App/ui/package*.json /ui/
RUN npm install
COPY App/ui/ /ui/
RUN npm run build

FROM python:3.13-slim

WORKDIR /app

COPY App/ /app/App/
RUN pip install --no-cache-dir -r /app/App/requirements.txt
COPY --from=ui-build /ui/dist /app/App/ui/dist

ENV CSV_EDITOR_PORT=8555
ENV PRODUCTS_DIR=/data/Products

EXPOSE 8555

CMD ["python3", "/app/App/server.py"]
