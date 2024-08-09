QUERY=${WORKDIR}/datasets/crag_qas/crag_music_49queries_meta.csv
OUTPUT=${WORKDIR}/datasets/crag_results/crag_49queries_retrieval_dataprepv2.csv

python test_retrieval.py \
--query_file $QUERY \
--output_file $OUTPUT \