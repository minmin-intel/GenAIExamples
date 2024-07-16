from transformers import AutoTokenizer
import json
import argparse
import os

def count_tokens(tokenizer, text):
    return len(tokenizer.tokenize(text))

def count_tokens_in_file(tokenizer, file_path):
    tokens = []
    n = 0
    with open(file_path, 'r') as f:
        for line in f:
            data = json.loads(line)
            tokens.append(count_tokens(tokenizer, data['doc']))
            n+=1
            if n>5:
                break
    
    print('Max token length: ', max(tokens))
    print('Min token length: ', min(tokens))
    return tokens

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--filedir', type=str, default=None)
    parser.add_argument('--model_name', type=str, default=None)
    args = parser.parse_args()

    tokenizer = AutoTokenizer.from_pretrained(args.model_name)

    data_files = os.listdir(args.filedir)

    for file in data_files:
        print(file)
        file = os.path.join(args.filedir, file)
        count_tokens_in_file(tokenizer, file)
        print('-'*50)