import pandas as pd
import json

def get_test_dataset(args):
    if args.query_file.endswith('.jsonl'):
        df = pd.read_json(args.query_file, lines=True, convert_dates=False)
    elif args.query_file.endswith('.csv'):
        df = pd.read_csv(args.query_file)
    else:
        raise ValueError("Invalid file format")
    return df


def save_as_csv(output):
    df = pd.read_json(output, lines=True, convert_dates=False)
    df.to_csv(output.replace(".jsonl", ".csv"), index=False)


def save_results(output_file, output_list):       
    with open(output_file, "w") as f:
        for output in output_list:
            f.write(json.dumps(output))
            f.write("\n")


def get_messages_content(messages):
    print('Get message content...')
    output = []
    for m in messages:
        print(m)
        output.append(m.content)
        print('-'*50)
    return output


def get_query(args):
    query = []
    query_time = []
    n = 0
    with open(args.query_file, "r") as f:
        for line in f:
            data = json.loads(line)
            query.append(data["query"])
            query_time.append(data["query_time"])
            # n += 1
            # if n >= 2:
            #     break
    return query, query_time