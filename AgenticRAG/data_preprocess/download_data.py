# from datasets import load_dataset

# dataset = load_dataset("Intel/crag_music_web_search_snippets", split="train")
from huggingface_hub import hf_hub_download

hf_hub_download(repo_id="Intel/crag_music_web_search_snippets", 
                filename="crag_docs_music.jsonl", 
                repo_type="dataset",
                local_dir="/localdisk/minminho/datasets/test_download")

