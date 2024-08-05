# How to build dataprep docker image
1. clone repo
```
export WORKDIR=<your-work-directory> # should be one level above GenAIExamples
cd $WORKDIR
# clone GenAIComps into WORKDIR
git clone https://github.com/minmin-intel/GenAIComps.git
git checkout crag-dev
```
2. Run script
```
bash build_data_prep_image.sh
```
3. Launch dataprep service
```
# go into retrieval_tool folder
# launch dataprep service with other services
```
4. Ingest data into vectordb
```
# before running the python script
bash ingest_data.sh
```