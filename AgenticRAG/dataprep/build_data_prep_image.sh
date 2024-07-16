# run in local directory of this bash script
# make sure the GenAIComps are up to date with opea/GenAIComps main
# copy the dataprep code to GenAIComps
cp ingest_data.py /localdisk/minminho/GenAIComps/comps/dataprep/redis/langchain/prepare_doc_redis.py

# run from GenAIComps directory
cd /localdisk/minminho/GenAIComps
docker build --no-cache -t opea/dataprep-redis:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/redis/langchain/docker/Dockerfile .
