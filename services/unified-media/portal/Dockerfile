FROM python:3.12-alpine
WORKDIR /app
COPY portal/server.py portal/refresh.py candidate_sources.py service_collectors.py snapshot_contract.py snapshot_readers.py recommendation_model.py recommendation_engine.py trakt_sources.py /app/
COPY portal/assets /app/assets
EXPOSE 8787
USER nobody
CMD ["python", "/app/server.py"]
