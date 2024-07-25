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


def calculate_correlation_with_human(df, score_col, human_score_col):
    from scipy.stats import pearsonr
    # calculate correlation with human scores
    corr, _ = pearsonr(df[score_col], df[human_score_col])
    print('Pearsons correlation with human score: %.3f' % corr)
    return None

def calculate_f1_score(df, score_col, human_score_col):
    from sklearn.metrics import f1_score
    # calculate f1 score
    def f1_score_per_class(y_true, y_pred, score_class):
        y_true = [1 if x==score_class else 0 for x in y_true]
        y_pred = [1 if x==score_class else 0 for x in y_pred]
        f1 = f1_score(y_true, y_pred)
        print('F1 score for score class {} is: {:.3f}'.format(score_class, f1))
    
    for c in df[score_col].unique():
        f1_score_per_class(df[human_score_col], df[score_col], c)

    print('Macro F1 score: {:.3f}'.format(f1_score(df[human_score_col], df[score_col], average='macro')))
    return None

def count_failure_modes(df):
    categorical_column = 'failure_mode'
    value_counts = df[categorical_column].value_counts()
    print('Occurrences of categorical values:')
    print(value_counts)
    return None

def count_category(df, category):
    print('Occurrences of category {}:'.format(category))
    print(df[category].value_counts())
    return None


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--score_file', type=str, required=True)
    parser.add_argument('--meta_file', type=str, required=True)
    parser.add_argument("--score_col", type = str, default='score')
    parser.add_argument("--output", type = str, default='merged')
    parser.add_argument("--save_merged", action="store_true")
    parser.add_argument("--human_analysis", action="store_true")
    args = parser.parse_args()

    if args.human_analysis:
        df = read_data(args.score_file)
        print('Final score correlation: ')
        calculate_correlation_with_human(df, 'score', 'human_score')
        print('Relevance score correlation: ')
        calculate_correlation_with_human(df, 'relevance_score', 'human_relevance_score')
        count_failure_modes(df)
        print('F1 score for final answer scores: ')
        calculate_f1_score(df, 'score', 'human_score')
        print('F1 score for retrieval relevance scores: ')
        calculate_f1_score(df, 'relevance_score', 'human_relevance_score')
    else:
        df = merge_score_with_meta_info(args)
        calculate_average_score(df, args.score_col)
        count_category(df, args.score_col)