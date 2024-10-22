DBPATH=$WORKDIR/TAG-Bench/dev_folder/dev_databases/california_schools/california_schools.sqlite
QUERYFILE=$WORKDIR/TAG-Bench/query_by_db/query_california_schools.csv
OUTFOLDER=$WORKDIR/sql_agent_output
KWFILE=$WORKDIR/sql_agent_output/keywords_hints_llam3.1-70b_noschema.csv



MODEL="gpt-4o-mini-2024-07-18"

python3 test_sql_agent.py \
--path $DBPATH \
--query_file $QUERYFILE \
--output $OUTFOLDER \
--model $MODEL \
--debug \
--kw_file $KWFILE \
--sql_agent_hint_fixer | tee $OUTFOLDER/v13_log.txt
# --hier_sql_agent

# --multiagent