DBPATH=$WORKDIR/TAG-Bench/dev_folder/dev_databases/california_schools/california_schools.sqlite
QUERYFILE=$WORKDIR/TAG-Bench/query_by_db/query_california_schools.csv
OUTFOLDER=$WORKDIR/sql_agent_output
KWFILE=$WORKDIR/sql_agent_output/keywords_hints_llam3.1-70b_noschema.csv

ip_address=$host_ip #$(hostname -I | awk '{print $1}')
LLM_ENDPOINT_URL="http://${ip_address}:8085"

# MODEL="gpt-4o-mini-2024-07-18"
MODEL="meta-llama/Llama-3.1-70B-Instruct"
MAX_NEW_TOKENS=8192

python3 test_sql_agent.py \
--path $DBPATH \
--query_file $QUERYFILE \
--output $OUTFOLDER \
--model $MODEL \
--max_new_tokens $MAX_NEW_TOKENS \
--debug \
--kw_file $KWFILE \
--llm_endpoint_url $LLM_ENDPOINT_URL \
--sql_llama | tee $OUTFOLDER/llama_v4_test_log.txt
