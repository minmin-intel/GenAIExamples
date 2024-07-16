# export OPENAI_API_KEY="your-api-key"
DOMAIN=music
QUERY=/localdisk/minminho/datasets/crag_qas/crag_qa_${DOMAIN}_sampled.jsonl
DOC=/localdisk/minminho/datasets/crag_docs/crag_docs_${DOMAIN}.jsonl

python generate_relevance_scores_for_docs.py \
--query_file $QUERY \
--doc_file $DOC \
--use_openai_api