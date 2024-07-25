# use LLM to generate relevance scores for documents
import pandas as pd
import argparse
import json

BINARY_RELEVANCE_SCORE_PROMPT='''\
Given the query, determain if the document is relevant to the query.\n
QUERY: {query}\n
DOCUMENT: {doc}\n
Output 1 if the document is relevant to the query, 0 otherwise.\n
ONLY output 1 or 0. NOTHING ELSE.\n
'''

RELEVANCE_SCORE_PROMPT='''\
Given the query and golden answer, determain how relevant the document is to the query.\n
QUERY: {query}\n
DOCUMENT: {doc}\n
GOLDEN ANSWER: {answer}\n
Output 2 if the document contains info to answer the query, 1 if the document contains partial info, 0 if the document is contains no useful info.\n
ONLY output 2, 1 or 0. NOTHING ELSE.\n
'''


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

def get_retrieved_docs(input_file):
    df = pd.read_json(input_file, lines=True)
    query = df["query"].tolist()
    context = df["context"].tolist()
    return query, context

def get_ref_answer(query, df):
    ref = df[df["query"] == query]["answer"].values[0]
    # print(ref)
    return ref

def run_openai_api(args, query, doc, ref):
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
        ("human", RELEVANCE_SCORE_PROMPT.format(query=query, doc=doc, answer=ref)),
    ]
    res = llm.invoke(messages)
    # print(res.content)
    return res.content


def run_opea_llm_endpoint():
    # run opea llm endpoint
    pass

def split_context_str_into_docs(context_str):
    return context_str.split("\n")

def generate_relevance_scores_for_retrieved_docs(args, query, context, ref):
    relevance_scores = []
    # split context
    context_list = split_context_str_into_docs(context)
    print('There are {} docs in the context'.format(len(context_list)))
    
    overall_relevance_score = int(run_openai_api(args, query, context, ref))
    for doc in context_list:
        if args.use_openai_api:
            res = run_openai_api(args, query, doc, ref)
        elif args.use_opea_llm_endpoint:
            pass
        else:
            raise ValueError("ONLY OpenAI API or OPEA LLM endpoint are supported!")
        relevance_scores.append(int(res))
    # average_relevance_score = sum(relevance_scores) / len(relevance_scores)
    return overall_relevance_score, relevance_scores
    
# for each candidate doc, generate a relevance score using LLM
def generate_relevance_scores_for_candidate_docs(args, query, candidate_docs):
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

def save_relevance_scores_to_file(output, output_file):
    with open(output_file, 'w') as f:
        for d in output:
            f.write(json.dumps(d) + '\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--query_file', type=str, default=None)
    parser.add_argument('--doc_file', type=str, default=None)
    parser.add_argument('--result_file', type=str, default=None)
    parser.add_argument('--ref_file', type=str, default=None)
    parser.add_argument('--use_openai_api', action='store_true')
    parser.add_argument('--use_opea_llm_endpoint', action='store_true')
    parser.add_argument('--model', type=str, default='gpt-4o-2024-05-13')
    parser.add_argument('--max_new_tokens', type=int, default=10)
    parser.add_argument('--score_retrieved_docs', action='store_true')
    parser.add_argument('--score_candidate_docs', action='store_true')
    args = parser.parse_args()
    print(args)

    if args.score_retrieved_docs:
        df_result = pd.read_json(args.result_file, lines=True)
        df = pd.read_json(args.ref_file, lines=True)
        # df_result = df_result.sample(2) # for debugging
        scores = []
        scores_per_doc = []
        for _, row in df_result.iterrows():
            query = row["query"]
            context = row["context"]
            ref = get_ref_answer(query, df)
            relevance_score, score_per_doc = generate_relevance_scores_for_retrieved_docs(args, query, context, ref)
            scores.append(relevance_score)
            scores_per_doc.append(score_per_doc)
            print('Query:\n{}\nContext:\n{}\nRef:\n{}'.format(query, context, ref))
            print('Relevance score: {}'.format(relevance_score))
            print('-'*50)
        # average scores across queries
        average_score = sum(scores) / len(scores)
        print("Average relevance score of retrieved docs for {} queries: {}".format(df_result.shape[0],average_score))
        df_result["relevance_score"] = scores
        df_result["relevance_scores_per_doc"] = scores_per_doc
        df_result.to_json(args.result_file.replace('.jsonl', '_relevance_scores_{}.jsonl'.format(args.model)), lines=True, orient='records')

    elif args.score_candidate_docs:
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
            relevance_scores = generate_relevance_scores_for_candidate_docs(args, query, candidate_docs)

            # save the relevance scores to a file
            for doc, score in zip(candidate_docs, relevance_scores):
                output.append({
                    "query": query,
                    "doc": doc,
                    "relevant": score
                })
            
        save_relevance_scores_to_file(output, args.result_file.replace('.jsonl', '_relevance_scores.jsonl'))
        
        