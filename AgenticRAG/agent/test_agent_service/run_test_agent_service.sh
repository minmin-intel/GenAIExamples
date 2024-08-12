export RETRIEVAL_TOOL_URL=http://${host_ip}:8889/v1/retrievaltool
QUERYFILE=${WORKDIR}/datasets/crag_qas/crag_music_49queries_meta.csv
OUTPUT=${WORKDIR}/datasets/crag_results/test_agent_service.jsonl

python test_agent_service.py \
--query_file $QUERYFILE \
--output_file $OUTPUT \
