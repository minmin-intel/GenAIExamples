RESULT=/localdisk/minminho/datasets/crag_results/crag_results_music_sampled_baseline_neuralchat3-3.jsonl
REF=/localdisk/minminho/datasets/crag_qas/crag_qa_music_sampled.jsonl

python generate_relevance_scores_for_docs.py \
--result_file $RESULT \
--ref_file $REF \
--use_openai_api \
--max_new_tokens 10 \
--score_retrieved_docs