FROM python:3.13-slim

WORKDIR /app

COPY App/ /app/App/

ENV CSV_EDITOR_PORT=8555
ENV PRODUCTS_DIR=/data/Products

EXPOSE 8555

CMD ["python3", "/app/App/server.py"]
