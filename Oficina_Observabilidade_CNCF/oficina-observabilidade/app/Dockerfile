FROM python:3.12-slim
WORKDIR /opt/app
COPY server.py /opt/app/server.py
RUN mkdir -p /var/log/oficina && chown -R 65534:65534 /var/log/oficina
USER 65534:65534
EXPOSE 8080
CMD ["python", "-u", "server.py"]
