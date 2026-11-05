FROM python:3.13.9-alpine3.22
RUN addgroup -S -g 65532 aster && adduser -S -D -H -u 65532 -G aster aster
WORKDIR /app
COPY contract.py persistence.py broker.py auth.py audiobookshelf.py server.py /app/
USER 65532:65532
EXPOSE 8790
ENTRYPOINT ["python3", "-B", "/app/server.py"]
