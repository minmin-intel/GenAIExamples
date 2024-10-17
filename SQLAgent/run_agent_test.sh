DBPATH=$WORKDIR/TAG-Bench/dev_folder/dev_databases/california_schools/california_schools.sqlite
QUERYFILE=$WORKDIR/TAG-Bench/query_by_db/query_california_schools.csv
OUTFOLDER=$WORKDIR/sql_agent_output



MODEL="gpt-4o-mini-2024-07-18"

python3 test_sql_agent.py \
--path $DBPATH \
--query_file $QUERYFILE \
--output $OUTFOLDER \
--model $MODEL \
--hier_sql_agent

# --multiagent