# EM

### Build and push image (Windows)
docker buildx build --platform linux/arm64,linux/amd64 -t simplecon/em:latest --push .

### Run image
docker run -v ./input:/opt/em/input simplecon/em:latest --scenario init --debug