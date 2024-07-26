## Build agent docker container
```
# inside AgenticRAG/
docker build -t agent-dev:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f agent/docker/Dockerfile .
```
## Start CRAG mock API server
```
export IMAGE_NAME="docker.io/aicrowd/kdd-cup-24-crag-mock-api:v0"
docker run -d -p=8080:8000 $IMAGE_NAME
```

## Start agent docker container
```
bash docker/launch_agent_dev_container.sh
```
