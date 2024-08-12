## Build agent docker image
```
docker build -t opea/comps-agent-langchain:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/agent/langchain/docker/Dockerfile .
```
## Launch agent microservice
### Option 1: use OpenAI llm
1. set up your OpenAI API token
```
export OPENAI_API_KEY=<your-openai-token>
```
2. Run command below
```
bash launch_agent_service_openai.sh
```
### Option 2: use Huggingface TGI to serve open-source LLM
1. launch TGI microservice
2. Launch agent microservice with command below