from huggingface_hub import hf_hub_download
import joblib
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--save_path", type=str, required=True)
args = parser.parse_args()

REPO_ID = "Intel/business_safety_logistic_regression_classifier"
FILENAME = "lr_clf.joblib"

model = joblib.load(
    hf_hub_download(repo_id=REPO_ID, filename=FILENAME)
)

save_path = args.save_path
joblib.dump(model, save_path)