#!/bin/bash

# dataset
FILEDIR=/home/user/workspace/datasets/patronus_enterprise_pii/
FILENAME=processed_patronus_enterprise_pii.csv
OUTPUT=annotated_patronus_enterprise_pii

#model
MODEL=mistralai/Mixtral-8x7B-Instruct-v0.1 #AetherResearch/Cerebrum-1.0-8x7b #
TOKENIZER=mistralai/Mixtral-8x7B-Instruct-v0.1 #AetherResearch/Cerebrum-1.0-8x7b #
MAX_INPUT_TOKENS=2048
MAXNEWTOKEN=256

# runtime args
BATCHSIZE=1

# train test split
TESTSIZE=300

python src/annotate_data_with_llm.py \
--filedir $FILEDIR \
--filename $FILENAME \
--output $OUTPUT \
--model_name_or_path $MODEL \
--tokenizer $TOKENIZER \
--max_input_tokens $MAX_INPUT_TOKENS \
--max_new_tokens $MAXNEWTOKEN \
--eval_size $TESTSIZE \
--batch_size $BATCHSIZE \
--run_prefilters \
--rerun_failed \
--run_eval \
--optimum_habana \
--use_kv_cache \
--gaudi_lazy_mode \
--use_hpu_graphs \
--bf16







