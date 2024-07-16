import json
import os
import argparse
import tqdm


def preprocess_data(input_file):
    snippet = []
    return_data = []
    n = 0
    with open(input_file, 'r') as f:
        for line in f:
            data = json.loads(line)

            # research results snippets --> retrieval corpus docs
            docs = data['search_results']
            for doc in docs:
                snippet.append({
                    "query": data['query'],
                    "domain": data['domain'],
                    "doc":doc['page_snippet']})
            
            # qa pairs without search results
            output = {}
            for k, v in data.items():
                if k != 'search_results':
                    output[k] = v
            return_data.append(output)

            # n += 1
            # if n>=5:
            #     break

    return snippet, return_data

    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--filedir', type=str, default=None)
    parser.add_argument('--docout', type=str, default=None)
    parser.add_argument('--qaout', type=str, default=None)
    
    args = parser.parse_args()

    if not os.path.exists(args.docout):
        os.makedirs(args.docout)

    if not os.path.exists(args.qaout):
        os.makedirs(args.qaout)

    data_files = os.listdir(args.filedir)

    qa_pairs = []
    docs = []
    for file in tqdm.tqdm(data_files):
        file = os.path.join(args.filedir, file)
        doc, data = preprocess_data(file)
        docs.extend(doc)
        qa_pairs.extend(data)
    
    # group by domain
    domains = ["finance", "music", "movie", "sports", "open"]

    for domain in domains:
        with open(os.path.join(args.docout, "crag_docs_"+domain + ".jsonl"), 'w') as f:
            for doc in docs:
                # print(doc.keys())
                if doc['doc']!="" and doc['domain'] == domain:
                    f.write(json.dumps(doc) + '\n')

        with open(os.path.join(args.qaout, "crag_qa_"+domain + ".jsonl"), 'w') as f:
            for d in qa_pairs:
                if d['domain'] == domain:
                    f.write(json.dumps(d) + '\n')