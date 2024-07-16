# use GPT-4 to generate relevance scores for documents
import pandas as pd
import argparse
import json

# read the sampled data
def read_sampled_data(input_file):
    df = pd.read_json(input_file, lines=True)
    return df["query"].tolist()

# for each query, get the candidate docs from the doc jsonl file
def get_candidate_docs(query, df):
    # filter the docs based on the query
    candidate_docs = df[df["query"] == query]["doc"].tolist()
    print(len(candidate_docs))
    # print(candidate_docs[:2])
    return candidate_docs

RELEVANCE_SCORE_PROMPT='''\
Given the query, determain if the document is relevant to the query.\n
QUERY: {query}\n
DOCUMENT: {doc}\n
Output 1 if the document is relevant to the query, 0 otherwise.\n
ONLY output 1 or 0. NOTHING ELSE.\n
'''


def run_openai_api(args, query, doc):
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        model=args.model,
        temperature=0,
        max_tokens=args.max_new_tokens,
        timeout=None,
        max_retries=2,
        # api_key="...",
        # base_url="...",
        # organization="...",
        # other params...
    )

    messages = [
        ("human", RELEVANCE_SCORE_PROMPT.format(query=query, doc=doc)),
    ]
    res = llm.invoke(messages)
    print(res.content)
    return res.content



def run_opea_llm_endpoint():
    # run opea llm endpoint
    pass
    
# for each candidate doc, generate a relevance score using LLM
def generate_relevance_scores(args, query, candidate_docs):
    relevance_scores = []
    for doc in candidate_docs:
        if args.use_openai_api:
            res = run_openai_api(args, query, doc)
        elif args.use_opea_llm_endpoint:
            pass
        else:
            raise ValueError("ONLY OpenAI API or OPEA LLM endpoint are supported!")
        relevance_scores.append(res)
    return relevance_scores

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--query_file', type=str, default=None)
    parser.add_argument('--doc_file', type=str, default=None)
    parser.add_argument('--use_openai_api', action='store_true')
    parser.add_argument('--use_opea_llm_endpoint', action='store_true')
    parser.add_argument('--model', type=str, default='gpt-4o-2024-05-13')
    parser.add_argument('--max_new_tokens', type=int, default=10)
    args = parser.parse_args()
    print(args)

    # read the query data
    queries = read_sampled_data(args.query_file)
    queries = queries[:2] # for debugging
    print(queries)

    # read the document data
    df = pd.read_json(args.doc_file, lines=True)



    # for each query, get the candidate docs from the doc jsonl file
    output = []
    for query in queries:
        candidate_docs = get_candidate_docs(query, df)

        # for each candidate doc, generate a relevance score using LLM
        relevance_scores = generate_relevance_scores(args, query, candidate_docs)

        # save the relevance scores to a file
        for doc, score in zip(candidate_docs, relevance_scores):
            output.append({
                "query": query,
                "doc": doc,
                "relevant": score
            })
    
    # save the output to a file
    with open(args.query_file.replace('.jsonl', '_relevant_score.jsonl'), 'w') as f:
        for d in output:
            f.write(json.dumps(d) + '\n')
        