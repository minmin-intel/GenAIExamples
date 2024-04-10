import pandas as pd
import numpy as np
from business_safety_classifier import BusinessSafetyClassifier
from utils import get_args, load_data_for_st_encoders, make_batches
from sentence_transformers import SentenceTransformer
import tqdm


def prepare_data(args):
    text, labels = load_data_for_st_encoders(args)
    # run btaches thru embedding model to get embeddings
    model = SentenceTransformer(model_name_or_path=args.model, trust_remote_code=True)
    n = 0
    for batch in tqdm.tqdm(make_batches(text, args.batch_size)):
        embeddings = model.encode(batch, convert_to_tensor=True)    
        embeddings = embeddings.cpu().detach().numpy()

        # print('Shape of emb of this batch: ', embeddings.shape)

        if n == 0:
            all_embeddings = embeddings
        else:
            all_embeddings = np.append(all_embeddings, embeddings, axis = 0)
        
        n += 1

    print('Shape of all embedding: ', all_embeddings.shape)

    return all_embeddings, labels
    


def main():
    args = get_args()
    print('preparing training data...')
    data, labels = prepare_data(args)
    biz_safety_clf = BusinessSafetyClassifier(args)
    biz_safety_clf.train(args, data, labels)
    biz_safety_clf.save_clf(args.lr_clf)

if __name__=="__main__":
    main()




