# Business Safety Classifier

## Overview
This folder contains a tested recipe for training a Business Safety Classifier with custom data. No human annotation is required. However, a few tens of human annotations are needed if you want to get a sense of the accuracy of the LLM annotations. We provide evaluation code to show accuracy of LLM annotations by comparing to human annotations as gold labels. We also show discuss how to apply this recipe to your own data after going through the instructions on running this recipe on a public dataset.

### Use cases of Business Safety classifier
Enterprise applications often require the output content from LLMs or RAG systems to be free of business senstive information such as private financial figures, sales accounts and confidential customer information. Another source of sensitive information that enterprises may want to exclude from LLMs and RAG output is human resources data such as employee performance reviews. A binary classifier that can detect such sensitive content is imperative in protecting business safety of enterprises running Gen AI applications.

### Overall workflow of this recipe
1. Annotate dataset using a LLM (evaluation of LLM annotations is optional)
2. Train a logistic-regression classifier using LLM-annotated data
3. Evaluate the logistic-regression classifier

### Validated models and dataset
We have validated this recipe with the following models.
Annotator LLM: ```mistralai/Mixtral-8x7B-Instruct-v0.1```
Embedding model: ```nomic-ai/nomic-embed-text-v1```

We showcase our recipe with the open-sourced [Patronus EnterprisePII dataset](https://www.patronus.ai/announcements/patronus-ai-launches-enterprisepii-the-industrys-first-llm-dataset-for-detecting-business-sensitive-information), which is used in MosaicML's LLM Eval Gauntlet and the [Enterprise Scenarios Leaderboard](https://huggingface.co/blog/leaderboard-patronus) on Huggingface.

## Prerequisites
We use Docker containers so make sure you have docker installed on your system. We also expect that you have access to a Linux machine or cloud instance that has [Intel Gaudi2](https://habana.ai/products/gaudi2/) cards.

1. Set up a work directory:
In the directory where you want to work, use the following command to create the workspace directory and set up `WORKDIR` and `DATADIR` environment variables.
    ```shell
    mkdir workspace
    export WORKDIR=workspace
    cd workspace
    mkdir datasets
    mkdir datasets/patronus_enterprise_pii/
    export DATADIR=datasets/patronus_enterprise_pii/
    ```

2. Clone this repository into `workspace`:

    ```shell
    cd ../ #come back to workspace
    git clone  
    ```


3. Download the Patronus EnterprisePII dataset to follow along the example:
We will need to get the Patronus EnterprisePII dataset from the llm-foundry repo. You can either clone the llm-foundry repo and then copy the dataset from the repo to your data folder as shown below, or you can directly download the file by click on the "Download raw file" button.

    ```shell
    git clone https://github.com/mosaicml/llm-foundry.git
    cp llm-foundry/scripts/eval/local_data/safety/enterprise_pii_classification.jsonl $DATADIR
    ```

4. Navigate to the project directory:

    ```shell
    cd BusinessSafetyClassifier
    ```
5. Set up Huggingface access token and cache directory:
In this example, we use mistralai/Mixtral-8x7B-v0.1, which requires Huggingface access token to download from Huggingface hub. You can follow the instruction on [Huggingface website](https://huggingface.co/docs/text-embeddings-inference/en/private_models) to generate an access token, and then use the command below to set up your environment.
    ```
    export HUGGING_FACE_HUB_TOKEN=<YOUR READ TOKEN>
    export HF_HOME=<path-to-your-desired-cache-directory>
    ```

## Preprocess dataset
 Follow the steps below to annotate the Patronus EnterprisePII dataset with `mistralai/Mixtral-8x7B-Instruct-v0.1`. 

1. Build and run the `classifier` docker container.
    ```shell
    cd docker
    bash build_classifier_image.sh
    ```
    After the image is built, run the command below to launch the container.
    ```shell
    bash launch_classifier_docker.sh
    ```
    It will take you inside the container to interactively run commands.

2. Run the preprocessing script.
The preprocessing step is specific to the Patronus EnterprisePII dataset where we get the actual text components and the gold labels from the original jsonl file. Run the command below to process this dataset.

    ```
    cd workspace/GenAIExamples/BusinessSafetyClassifier
    bash run_process_enterprisepii_dataset.sh
    ```
Once the data processing is finished, open another terminal and then proceed with the steps below.

## Annotate dataset with LLM
1. Build and run the `annotation-gaudi` container.
    ```shell
    cd docker
    bash build_image.sh
    ```
    After the image is built, run the command below to launch the container.
    ```shell
    bash launch_annotation_docker.sh
    ```
    It will take you inside the container to interactively run commands. Behind the scene, [optimum-habana](https://github.com/huggingface/optimum-habana/tree/main) (part of Huggingface optimum) enables the LLM inference acceleration on Intel Gaudi platform.

2. Run the annotation script.

    ```
    cd workspace/GenAIExamples/BusinessSafetyClassifier
    bash run_annotation.sh
    ```
After the script is successfully completed, you will get three csv files with LLM annotations: 1) the whole dataset, 2) a randomly sampled training set, 3) a test set that is exclusive of the training set. Note: by default, the test set size is 300. If you want to change the test set size, you can change the `TESTSIZE` variable in the `run_annotation.sh` script.

For the Patronus EnterprisePII dataset, we also enabled calculation of annotation accuracy with respect to the golden labels in the dataset. You should see metrics printed out that are similar to the ones listed below. Since there is randomness in LLM generation, you may not see exactly the same numbers. Randomness is introduced as to allow for re-generation of annotations if the annotation failed in the first round.


| Metric    | Value |
|-----------|-------|
| Accuracy  | 0.909 |
| Precision | 0.883 |
| Recall    | 0.940 |


## Train and evaluate the Business Safety classifier
Once you have obtained the annotated dataset using an LLM, you can train a classifier with the dataset. The classifier consists of two part: 1) an encoder model that converts text into embedding vectors, and 2) a logistic regression model that takes the embedding vectors as input and output prediction labels.

We picked the `nomic-ai/nomic-embed-text-v1` [model](https://blog.nomic.ai/posts/nomic-embed-text-v1) as it is one of the top-performing long-context (max sequence length = 8192 vs. 512 for other BERT-based encoders) encoder models that do well on [Huggingface MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard) as well as long-context [LoCo benchmark](https://hazyresearch.stanford.edu/blog/2024-01-11-m2-bert-retrieval). The long-context capability is useful when the generated content is long (>512 tokens).

You can run the commands below to train your classifier.
1. Go back to the terminal where you preprocessed the dataset. Or you can launch the `classifer` container using the command below.
    ```shell
    bash launch_classifier_docker.sh
    ```
2. Run the training script.
    ```shell
    cd workspace/GenAIExamples/BusinessSafetyClassifier
    bash run_logistic_regression.sh
    ```
After the script is successfully completed, you will get a logistic regression classifier model saved to disk.


3. Now that you have finished training the classifier. You can run the command below to evaluate the classifier trained in the previous step. Note: you can calculate accuracy metrics with respect to either LLM-annotated labels or human-annotated labels (if you have human annotations). Just specify the column name of the labels that you want to evaluate against in the script by specifying the `LABEL` variable.

    ```
    bash run_eval.sh
    ```

For the Patronus EnterprisePII dataset, the metrics on the test set are shown below. Interestingly, although the classifier was trained with LLM-annotated labels, the classifier performed perfectly on the 300 test samples when using the golden labels in the original dataset as the reference, while it achieves slighlty lower but still very good accuracy (around 0.9) when using the LLM annotations as reference.

| |Accuracy|Precision|Recall|
|--|-------|---------|------|
|Compared to golden labels|1.0|1.0|1.0|
|Compared to LLM annotated labels|0.903|0.927|0.886|


## Next step: apply this recipe to your own data
1. You can adapt our preprocessing code for your own dataset. Our preprocessing code takes a jsonl file as input and outputs a csv file. You can implement a custom `process_text` function in the `process_enterprise_pii_data.py` according to the specific formatting of your data.
2. You can customize the annotation prompt by editing `src/prompt_templates.py`. 
3. You can implement custom prefilter logic in `src/filters.py`. 

Enjoy and have fun!