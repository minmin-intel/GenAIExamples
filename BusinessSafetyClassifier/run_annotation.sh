#!/bin/bash

# dataset
FILEDIR=/home/user/workspace/datasets/patronus_enterprise_pii/
FILENAME=processed_patronus_enterprise_pii.csv
OUTPUT=annotated_patronus_enterprise_pii

#model
MODEL=mistralai/Mixtral-8x7B-Instruct-v0.1
TOKENIZER=mistralai/Mixtral-8x7B-Instruct-v0.1
MAXNEWTOKEN=256

# tensor parallel for vllm
TP=4

# Args for optimum habana
BATCHSIZE=16

# train test split
TESTSIZE=300

python src/annotate_data_with_llm.py \
--filedir $FILEDIR \
--filename $FILENAME \
--output $OUTPUT \
--model $MODEL \
--tokenizer $TOKENIZER \
--max_new_tokens $MAXNEWTOKEN \
--tp_size $TP \
--eval_size $TESTSIZE \
--batch_size $BATCHSIZE \
--run_prefilters \
--rerun_failed \
--run_eval \
--optimum_habana \
--use_kv_cache \
--gaudi_lazy_mode \
--do_sample \



#--vllm_offline \
# --use_hpu_graphs \



