import json
import os
import argparse
import tqdm
from langchain_text_splitters import RecursiveCharacterTextSplitter

def split_text(text, chunk_size=2000, chunk_overlap=400):
    text_splitter = RecursiveCharacterTextSplitter(
        # Set a really small chunk size, just to show.
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False,
        separators=["\n\n", "\n", ".", "!"],
    )
    return text_splitter.split_text(text)

def process_html_string(text):
    from bs4 import BeautifulSoup
    # print(text)
    soup = BeautifulSoup(text, features="html.parser")

    # kill all script and style elements
    for script in soup(["script", "style"]):
        script.extract()    # rip it out

    # get text
    text_content = soup.get_text()

    # break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text_content.splitlines())
    # break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # drop blank lines
    final_text = '\n'.join(chunk for chunk in chunks if chunk)
    print(final_text)
    return final_text

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
                print('PAGE RESULT:')
                text = process_html_string(doc['page_result'])
                chunks = split_text(text)
                for chunk in chunks:
                    snippet.append({
                        "query": data['query'],
                        "domain": data['domain'],
                        "doc":chunk})
                # print('PAGE SNIPPET:\n', doc['page_snippet'])
                # for d in doc['page_snippet'].split('.'):
                #     if d in text:
                #         print('Yes')
                #     else:
                #         print('No')
                snippet.append({
                    "query": data['query'],
                    "domain": data['domain'],
                    "doc":doc['page_snippet']})
                
                print('-----------------------------------')
                break
            
            # qa pairs without search results
            output = {}
            for k, v in data.items():
                if k != 'search_results':
                    output[k] = v
            return_data.append(output)

            n += 1
            if n>=1:
                break

    return snippet, return_data

    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--filedir', type=str, default=None)
    parser.add_argument('--docout', type=str, default=None)
    parser.add_argument('--qaout', type=str, default=None)
    
    args = parser.parse_args()

    # if not os.path.exists(args.docout):
    #     os.makedirs(args.docout)

    # if not os.path.exists(args.qaout):
    #     os.makedirs(args.qaout)

    data_files = os.listdir(args.filedir)

    qa_pairs = []
    docs = []
    for file in tqdm.tqdm(data_files):
        file = os.path.join(args.filedir, file)
        doc, data = preprocess_data(file)
        docs.extend(doc)
        qa_pairs.extend(data)
    
    # group by domain
    # domains = ["finance", "music", "movie", "sports", "open"]
    domains =["music"]

    for domain in domains:
        with open(os.path.join(args.docout, "test_docs_"+domain + ".jsonl"), 'w') as f:
            for doc in docs:
                # print(doc.keys())
                if doc['doc']!="" and doc['domain'] == domain:
                    f.write(json.dumps(doc) + '\n')

    #     with open(os.path.join(args.qaout, "crag_qa_"+domain + ".jsonl"), 'w') as f:
    #         for d in qa_pairs:
    #             if d['domain'] == domain:
    #                 f.write(json.dumps(d) + '\n')