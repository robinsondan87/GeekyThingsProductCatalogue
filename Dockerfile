FROM python:3.13-slim

WORKDIR /app

COPY ProductMgmt/ /app/ProductMgmt/

ENV CSV_EDITOR_PORT=8555
ENV PRODUCTS_DIR=/data/Products

EXPOSE 8555

CMD ["python3", "/app/ProductMgmt/server.py"]
