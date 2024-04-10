from joblib import dump
from joblib import load
from sklearn.linear_model import LogisticRegression
from utils import load_data_for_st_encoders, make_batches, calculate_metrics
from sentence_transformers import SentenceTransformer
import os
import pandas as pd
import tqdm

class BusinessSafetyClassifier:
    def __init__(self, args):
        # Initialize any necessary variables or objects here
        self.model = SentenceTransformer(model_name_or_path=args.model, trust_remote_code=True)
        if os.path.exists(args.lr_clf):
            self.clf = load(args.lr_clf)
        else:
            self.clf = None
            print('Logistic regression classifier does not exist! Please train or load one.')
        pass
    
    def train(self, args, data, labels):
        print('Start training logistic regression classifier...')
        self.clf = LogisticRegression(random_state=args.random_seed,
                             max_iter=args.max_iter)
        self.clf.fit(data, labels)
        # accuracy on training set
        acc = self.clf.score(data, labels)
        print('Accuracy on training set: {:.3f}'.format(acc))
        return self.clf
    
    def predict_batch(self, args):
        # predict function for a batch of text
        # csv data will be loaded from disk 
        # and converted into format that can be consumed by sentence transformer
        assert self.clf != None, 'No classifier exists, please first train or load one.'

        eval_predictions = []

        eval_data, labels = load_data_for_st_encoders(args)

        for batch in tqdm.tqdm(make_batches(eval_data, args.batch_size)):
            embeddings = self.model.encode(batch, convert_to_tensor=True).cpu()
            # print('text embedding shape: ', embeddings.shape)
            # prediction
            predictions = self.clf.predict(embeddings)
            eval_predictions.extend(predictions)
            # print('='*50)

        # calculate accuracy, precision, recall.
        calculate_metrics(eval_predictions, labels)

        # save results to disk as csv
        df = pd.DataFrame({
            "text":eval_data,
            "label":labels,
            "predictions": eval_predictions
        })

        df.to_csv(args.filedir+args.output+'.csv')


        
    def predict(self, args, data):
        # predict function for one single piece of text
        assert self.clf != None, 'No classifier exists, please first train or load one.'
        embeddings = self.model.encode(data, convert_to_tensor=True).reshape(1, -1).cpu()
        # print('shape of embedding: ', embeddings.shape)
        predictions = self.clf.predict(embeddings)
        # print('shape of prediction: ', predictions.shape)
        return predictions
        

    def load_clf(self, path):
        assert os.path.exists(path), "Cannot find classifier at specified path. Please double check."
        self.clf = load(path)

    def save_clf(self, path):
        if self.clf:
            if not os.path.exists(os.path.dirname(path)):
                os.makedirs(os.path.dirname(path))
            dump(self.clf, path)
            print('Saved classifier at :', path)
        else:
            print('No classifier exists, please first train one.')
