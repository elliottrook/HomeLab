ARG PYTHON_BASE
FROM ${PYTHON_BASE}

RUN addgroup -S broker && adduser -S -G broker -u 10001 broker
WORKDIR /app
COPY aster_games_broker /app/aster_games_broker
USER 10001:10001
EXPOSE 8099
ENTRYPOINT ["python", "-m", "aster_games_broker"]

