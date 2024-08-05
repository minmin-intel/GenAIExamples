# run in local directory of this bash script
# copy the dataprep code to GenAIComps
# Make sure WORKDIR has been set
# It should be one level up from GenAIComps and GenAIExamples
echo $WORKDIR
cp ingest_data.py ${WORKDIR}/GenAIComps/comps/dataprep/redis/langchain/prepare_doc_redis.py

# run from GenAIComps directory
cd ${WORKDIR}/GenAIComps
docker build --no-cache -t opea/dataprep-redis:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/redis/langchain/docker/Dockerfile .
