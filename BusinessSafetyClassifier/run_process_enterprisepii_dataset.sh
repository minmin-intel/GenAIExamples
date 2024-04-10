#!/bin/bash

FILEDIR=/home/user/workspace/datasets/patronus_enterprise_pii/
FILENAME=enterprise_pii_classification.jsonl
OUTPUT=processed_patronus_enterprise_pii

python3 src/process_enterprise_pii_data.py \
--filedir $FILEDIR \
--filename $FILENAME \
--output $OUTPUT