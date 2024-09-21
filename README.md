# EM

### Build and push image
docker buildx build --platform linux/arm64,linux/amd64 -t simplecon/em:latest --push .

### Run image
docker run -v ./examples/postgres/input:/opt/em/input simplecon/em:latest --scenario init --debug