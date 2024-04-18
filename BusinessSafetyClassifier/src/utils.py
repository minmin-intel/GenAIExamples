import pandas as pd
import argparse
import numpy as np
from torch.utils.data import Dataset
from torch.utils.data import DataLoader
from prompt_templates import PROMPT_BUSINESS_SENSITIVE
import os

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--filedir", type=str, default="", help="file directory where input and output are stored"
    )

    parser.add_argument(
        "--filename", type = str, default=""
    )

    parser.add_argument(
        "--output", type=str, default=""
    )

    parser.add_argument(
        "--model_name_or_path",
        default=None,
        type=str,
        required=True,
        help="Path to pre-trained model (on the HF Hub or locally).",
    )

    parser.add_argument(
        "--model_dir", type=str, default="", help="model directory to be used for vllm offline mode"
    )

    parser.add_argument(
        "--tokenizer", type=str, default="", help="tokenizer to be used"
    )

    parser.add_argument(
        "--prefix", type=str, default="", help="prefix for encoder"
    )

    parser.add_argument(
        "--max_seq_len", type=int, default=512, help="max sequence length for embedding model"
    )

    parser.add_argument(
        "--batch_size", type=int, default=32
    )

    parser.add_argument(
        "--threshold", type=float, default=0.5, help="threshold for classifier"
    )

    parser.add_argument(
        "--lr_clf", type=str, help="path to saved logistic regression classifier"
    )

    # parser.add_argument(
    #     "--use_m2_bert", action = "store_true"
    # )

    # parser.add_argument(
    #     "--use_st_encoder", action = "store_true"
    # )

    # parser.add_argument(
    #     "--use_decoder", action="store_true"
    # )


    # for logistic regression classifier training
    parser.add_argument(
        "--random_seed", type=int, default=123
    )

    parser.add_argument(
        "--max_iter", type=int, default=100
    )

    # for annotation with llm
    parser.add_argument(
        "--top_p", type = float, default=0.9
    )

    parser.add_argument(
        "--temperature", type = float, default=0.8, help="temperature for LLM generation"
    )

    parser.add_argument(
        "--max_new_tokens", type = int, default=128
    )

    # parser.add_argument(
    #     "--generate_with_pipeline", action = "store_true"
    # )

    # parser.add_argument(
    #     "--batch_model_generate", action = "store_true"
    # )

    parser.add_argument(
        "--vllm_offline", action = "store_true"
    )

    parser.add_argument(
        "--tgi_concurrent", action = "store_true"
    )

    parser.add_argument(
        "--optimum_habana", action = "store_true"
    )


    parser.add_argument(
        "--device", type = str, default='hpu', help="options: hpu, cuda, cpu"
    )

    parser.add_argument(
        "--run_prefilters", action = "store_true"
    )

    parser.add_argument(
        "--rerun_failed", action = "store_true"
    )
    

    parser.add_argument(
        "--tp_size", type=int, default=8, help="tensor parallel size"
    )

    parser.add_argument(
        "--run_eval", action = "store_true"
    )

    parser.add_argument(
        "--text_col", type = str, default='text', help="column name for text"
    )

    parser.add_argument(
        "--length_col", type = str, default='length', help="name of column that contains length of the text"
    )

    parser.add_argument(
        "--label_col", type = str, default='label', help="name of column that contains labels"
    )

    parser.add_argument(
        "--eval_size", type=int, default=300
    )

    parser.add_argument(
        "--max_concurrent_requests", type=int, default=256, help="Max number of concurrent requests"
    )

    parser.add_argument(
        "--server_address", type=str, default="http://localhost:8080", help="Address of the TGI server"
    )

    # args for text generation with optimum habana
    parser.add_argument(
        "--bf16",
        action="store_true",
        help="Whether to perform generation in bf16 precision.",
    )
    
    parser.add_argument(
        "--max_input_tokens",
        type=int,
        default=0,
        help="If > 0 then pad and truncate the input sequences to this specified length of tokens. \
            if == 0, then truncate to 16 (original default) \
            if < 0, then do not truncate, use full input prompt",
    )
    parser.add_argument("--warmup", type=int, default=3, help="Number of warmup iterations for benchmarking.")
    parser.add_argument("--n_iterations", type=int, default=5, help="Number of inference iterations for benchmarking.")
    parser.add_argument("--local_rank", type=int, default=0, metavar="N", help="Local process rank.")
    parser.add_argument(
        "--use_kv_cache",
        action="store_true",
        help="Whether to use the key/value cache for decoding. It should speed up generation.",
    )
    parser.add_argument(
        "--use_hpu_graphs",
        action="store_true",
        help="Whether to use HPU graphs or not. Using HPU graphs should give better latencies.",
    )

    parser.add_argument(
        "--do_sample",
        action="store_true",
        help="Whether to use sampling for generation.",
    )
    parser.add_argument(
        "--num_beams",
        default=1,
        type=int,
        help="Number of beams used for beam search generation. 1 means greedy search will be performed.",
    )
    parser.add_argument(
        "--trim_logits",
        action="store_true",
        help="Calculate logits only for the last token to save memory in the first step.",
    )
    parser.add_argument(
        "--seed",
        default=27,
        type=int,
        help="Seed to use for random generation. Useful to reproduce your runs with `--do_sample`.",
    )
    parser.add_argument(
        "--profiling_warmup_steps",
        default=0,
        type=int,
        help="Number of steps to ignore for profiling.",
    )
    parser.add_argument(
        "--profiling_steps",
        default=0,
        type=int,
        help="Number of steps to capture for profiling.",
    )
    
    parser.add_argument(
        "--bad_words",
        default=None,
        type=str,
        nargs="+",
        help="Optional argument list of words that are not allowed to be generated.",
    )
    parser.add_argument(
        "--force_words",
        default=None,
        type=str,
        nargs="+",
        help="Optional argument list of words that must be generated.",
    )
    parser.add_argument(
        "--peft_model",
        default=None,
        type=str,
        help="Optional argument to give a path to a PEFT model.",
    )
    parser.add_argument("--num_return_sequences", type=int, default=1)
    parser.add_argument(
        "--token",
        default=None,
        type=str,
        help="The token to use as HTTP bearer authorization for remote files. If not specified, will use the token "
        "generated when running `huggingface-cli login` (stored in `~/.huggingface`).",
    )
    parser.add_argument(
        "--model_revision",
        default="main",
        type=str,
        help="The specific model version to use (can be a branch name, tag name or commit id).",
    )
    parser.add_argument(
        "--attn_softmax_bf16",
        action="store_true",
        help="Whether to run attention softmax layer in lower precision provided that the model supports it and "
        "is also running in lower precision.",
    )
    
    parser.add_argument(
        "--bucket_size",
        default=-1,
        type=int,
        help="Bucket size to maintain static shapes. If this number is negative (default is -1) \
            then we use `shape = prompt_length + max_new_tokens`. If a positive number is passed \
            we increase the bucket in steps of `bucket_size` instead of allocating to max (`prompt_length + max_new_tokens`).",
    )
    parser.add_argument(
        "--bucket_internal",
        action="store_true",
        help="Split kv sequence into buckets in decode phase. It improves throughput when max_new_tokens is large.",
    )
    
    parser.add_argument(
        "--limit_hpu_graphs",
        action="store_true",
        help="Skip HPU Graph usage for first token to save memory",
    )
    parser.add_argument(
        "--reuse_cache",
        action="store_true",
        help="Whether to reuse key/value cache for decoding. It should save memory.",
    )
    parser.add_argument("--verbose_workers", action="store_true", help="Enable output from non-master workers")
    parser.add_argument(
        "--simulate_dyn_prompt",
        default=None,
        type=int,
        nargs="*",
        help="If empty, static prompt is used. If a comma separated list of integers is passed, we warmup and use those shapes for prompt length.",
    )
    parser.add_argument(
        "--reduce_recompile",
        action="store_true",
        help="Preprocess on cpu, and some other optimizations. Useful to prevent recompilations when using dynamic prompts (simulate_dyn_prompt)",
    )

    parser.add_argument("--fp8", action="store_true", help="Enable Quantization to fp8")
    parser.add_argument(
        "--use_flash_attention",
        action="store_true",
        help="Whether to enable Habana Flash Attention, provided that the model supports it.",
    )
    parser.add_argument(
        "--flash_attention_recompute",
        action="store_true",
        help="Whether to enable Habana Flash Attention in recompute mode on first token generation. This gives an opportunity of splitting graph internally which helps reduce memory consumption.",
    )
    parser.add_argument(
        "--flash_attention_causal_mask",
        action="store_true",
        help="Whether to enable Habana Flash Attention in causal mode on first token generation.",
    )
    
    parser.add_argument(
        "--torch_compile",
        action="store_true",
        help="Whether to use torch compiled model or not.",
    )
    
    parser.add_argument(
        "--const_serialization_path",
        "--csp",
        type=str,
        help="Path to serialize const params. Const params will be held on disk memory instead of being allocated on host memory.",
    )

    parser.add_argument(
        "--disk_offload",
        action="store_true",
        help="Whether to enable device map auto. In case no space left on cpu, weights will be offloaded to disk.",
    )
    
    parser.add_argument(
        "--gaudi_lazy_mode",
        action="store_true",
        help="Whether to use lazy mode, should improve performance.",
    )

    args = parser.parse_args()

    if args.torch_compile:
        args.use_hpu_graphs = False

    if not args.use_hpu_graphs:
        args.limit_hpu_graphs = False

    args.quant_config = os.getenv("QUANT_CONFIG", "")

    return args

def add_prefix(text_batch, prefix):
    rt_text = [prefix+': '+t for t in text_batch]
    return rt_text

def load_data_for_st_encoders(args):
    df = pd.read_csv(args.filedir+args.filename)
    text = df[args.text_col].to_list()
    text = add_prefix(text, args.prefix)
    labels = df[args.label_col].to_list()
    return text, labels

def make_batches(text_list, bs):
    l = len(text_list)
    for i in range(0, l, bs):
        yield text_list[i:min(l, i+bs)]


def calculate_metrics(predictions, labels):
    assert len(labels) == len(predictions), "labels and predictions have different lengths"
    labels = np.array(labels)
    predictions = np.array(predictions)
    # accuracy
    acc = np.mean(labels == predictions)
    print('accuracy: {:.3f}'.format(acc))

    # true positive
    tp = np.sum((predictions ==1)&(labels==1))

    # false positive rate
    # find # of fp
    fp = np.sum((predictions == 1) & (labels == 0))
    tn = np.sum((predictions == 0) & (labels == 0))
    fpr = fp/(fp+tn)
    print('false positive rate: {:.3f}'.format(fpr))

    # false negative
    fn = np.sum((predictions==0)&(labels==1))

    # precision
    precision = tp/(tp+fp)
    # recall
    recall = tp/(tp+fn)
    print('precision: {:.3f}, recall: {:.3f}'.format(precision, recall))





class CustomDataset(Dataset):
    def __init__(self, data, tokenizer, prompt_template):
        self.data = data
        self.tokenizer = tokenizer
        self.prompt_template = prompt_template

    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, i):
        # output = pipe(prompt)[0]['generated_text'][-1]
        chat = [
            {"role": "user",
            "content":self.prompt_template.format(text=self.data[i])}
        ]
        prompt = self.tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=True)
        return prompt


def setup_dataloader(args, text, tokenizer, prompt_template):
    input_dataset = CustomDataset(text, tokenizer,prompt_template)
    input_dataloader = DataLoader(input_dataset, batch_size=args.batch_size)
    return input_dataloader


