FROM        python:3.9-slim
WORKDIR     /opt/em
RUN         mkdir -p /opt/em/input
ENV         PYTHONPATH="${PYTHONPATH}:/opt/em/python:/opt/em/input"
COPY        requirements.txt requirements.txt
RUN         pip install -r requirements.txt
COPY        .   .
ENTRYPOINT  ["python", "python/em"]
CMD         ["--input_dir", "/opt/em/input"]