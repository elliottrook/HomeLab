FROM python:3.12-alpine
WORKDIR /app
COPY server.py refresh.py /app/
EXPOSE 8787
USER nobody
CMD ["python", "/app/server.py"]
