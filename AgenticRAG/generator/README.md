## How to launch generator service
### Build llm microservice docker image
```
# Inside GenAIComps/
docker build --no-cache -t opea/llm-tgi:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/text-generation/tgi/Dockerfile .
```
### Launch
```
# Inside GenAIExamples/AgenticRAG/generator/
bash launch_generator.sh
```