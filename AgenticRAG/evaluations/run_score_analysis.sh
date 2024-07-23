SCOREFILE=/localdisk/minminho/datasets/crag_results/crag_music_sampled_baseline_human_eval.csv
METAFILE=/localdisk/minminho/datasets/crag_qas/crag_qa_music_sampled.jsonl
SCORECOL=human_score
OUTPUT=crag_music_sampled_baseline_score_meta_neuralchat3-3_gpt-4o

python score_analysis.py \
--score_file $SCOREFILE \
--meta_file $METAFILE \
--score_col $SCORECOL \
--output $OUTPUT

# --save_merged \

