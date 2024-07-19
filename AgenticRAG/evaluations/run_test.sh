QUERY=/localdisk/minminho/datasets/crag_qas/crag_qa_music_sampled.jsonl
OUTPUT=/localdisk/minminho/datasets/crag_results/crag_results_music_sampled_baseline_neuralchat3-3.jsonl

python test_rag_baseline.py \
--query_file $QUERY \
--output_file $OUTPUT
