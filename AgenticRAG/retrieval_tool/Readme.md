# How to launch retrieval tool
## Build images for microservices
1. Embedding
```
# Inside GenAIComps/
docker build --no-cache -t opea/embedding-tei:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/embeddings/langchain/docker/Dockerfile .
```
2. Retriever
```
# Inside GenAIComps/
docker build --no-cache -t opea/retriever-redis:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/langchain/redis/docker/Dockerfile .
```
3. Reranker
```
# copy reranking python code into GenAIComps
cp ../GenAIExamples/AgenticRAG/retrieval_tool/reranking_baseline.py comps/reranks/tei/reranking_tei.py

# Inside GenAIComps/
docker build --no-cache -t opea/reranking-tei:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/reranks/tei/docker/Dockerfile .
```
3. Retrieval_tool
```
# Inside GenAIExamples/AgenticRAG/retrieval_tool/
docker build --no-cache -t opea/retrievaltool:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile_retrievaltool .
```
## Launch microservices
```
bash launch_retrieval_tool.sh
```