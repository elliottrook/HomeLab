FROM python:3.12-alpine
WORKDIR /app
COPY portal/server.py portal/refresh.py candidate_sources.py service_collectors.py snapshot_contract.py snapshot_readers.py recommendation_model.py recommendation_engine.py trakt_sources.py trakt_oauth.py spotify_oauth.py aster_seerr_contract.py aster_seerr_broker.py aster_seerr_episode_contract.py aster_tv_discovery.py aster_acquisition_contract.py aster_acquisition_broker.py aster_acquisition_providers.py /app/
COPY portal/assets /app/assets
EXPOSE 8787
USER nobody
CMD ["python", "/app/server.py"]
