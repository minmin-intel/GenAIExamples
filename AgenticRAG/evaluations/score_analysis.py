import pandas as pd
import argparse
import os

def read_data(filename):
    if filename.endswith('.csv'):
        df = pd.read_csv(filename)
    elif filename.endswith('.jsonl'):
        df = pd.read_json(filename, lines=True)
    return df

def merge_score_with_meta_info(args):
    df_score = read_data(args.score_file)
    categorical_column = 'failure_mode'
    value_counts = df_score[categorical_column].value_counts()
    print('Occurrences of categorical values:')
    print(value_counts)
    df_meta = read_data(args.meta_file)
    df = pd.merge(df_score, df_meta, on='query')
    print(df.shape)
    # save
    if args.save_merged:
        filename = os.path.join(os.path.dirname(args.score_file), '{}.csv'.format(args.output))
        df.to_csv(filename, index=False)
    return df

    
def calculate_average_score(df, score_column):
    # macro average
    print("Overall average: ",df[score_column].mean())

    # average per category
    print('Average per category: ')
    print(df.groupby('question_type')[score_column].mean())

    # average per dynamism
    print('Average per dynamism: ')
    print(df.groupby('static_or_dynamic')[score_column].mean())

    return None


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--score_file', type=str, required=True)
    parser.add_argument('--meta_file', type=str, required=True)
    parser.add_argument("--score_col", type = str, default='score')
    parser.add_argument("--output", type = str, default='merged')
    parser.add_argument("--save_merged", action="store_true")
    args = parser.parse_args()

    df = merge_score_with_meta_info(args)
    calculate_average_score(df, args.score_col)