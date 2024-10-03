## Setup
0. Make a work directory
```
export WORKDIR=<your-work-directory>
cd $WORKDIR
git clone GenAIExamples
```
1. Download TAG-Bench
```
cd $WORKDIR
git clone https://github.com/TAG-Research/TAG-Bench.git
```
2. Set up database
```
cd TAG-Bench/setup
chmod +x get_dbs.sh
./get_dbs.sh
```
3. Get query by database
```
cd $WORKDIR/GenAIExample/SQLAgent/data_preprocess
bash run_data_split.sh
```