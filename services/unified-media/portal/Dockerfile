FROM python:3.12-alpine
WORKDIR /app
COPY server.py /app/server.py
EXPOSE 8787
USER nobody
CMD ["python", "/app/server.py"]
