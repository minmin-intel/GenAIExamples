# from vllm import LLM, SamplingParams
from transformers import AutoTokenizer, AutoModelForCausalLM
from transformers import pipeline
import torch
import json
from utils import CustomDataset
from torch.utils.data import DataLoader


def format_prompt(text, tokenizer, prompt_template):
    chat = [
                {"role": "user",
                "content":prompt_template.format(text=text)}
            ]
    prompt = tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=True)
    return prompt


def clean_output(string, random_choice=True):
    labels = ["Yes", "No"]
    for category in labels:
        if category.lower() in string.lower():
            return category
    # if the output string cannot be mapped to one of the categories, we either return "FAIL" or choose a random label
    if random_choice:
        return random.choice(labels)
    else:
        return "FAIL"

def parse_output(output, args = None):
    try:
        if args.vllm_offline == False:
            output = output.split('[/INST]')[-1].strip(" ").strip("</s>")
        if args.optimum_habana == True:
            output = output.split('}')[0].strip()
            output = output+'}'
        output_dict = json.loads(output)
        # print(output_dict)
    except Exception as e:
        print(f"Parsing failed for output: {output}, Error: {e}")
        output_cl = clean_output(output, random_choice=False)
        output_dict = {"reason": "FAIL", "answer": output_cl}
    return output_dict


def convert_to_numeric_label(output):
    pred = output['answer']
    if "yes" in pred.lower():
        return 1
    elif "no" in pred.lower():
        return 0
    else:
        return 0
        
##########################################################
######################### vLLM #############################
#############################################################
def setup_vllm(args):  
    # initialize offline engine
    llm = LLM(
        model=args.model, 
        #download_dir =args.model_dir, 
        pipeline_parallel_size = 1,
        tensor_parallel_size = args.tp_size,)
        #dtype = 'half')

    return llm


def vllm_batched_offline_generation(args=None, llm=None, text = None, prompt_template=None):
    # ref: https://docs.vllm.ai/en/latest/getting_started/quickstart.html#offline-batched-inference

    sampling_params = SamplingParams(
        top_p=args.top_p, #0.90,
        temperature=args.temperature, #0.8,
        max_tokens=args.max_new_tokens, #128,
    )

    # make prompts
    tokenizer = AutoTokenizer.from_pretrained(args.tokenizer)
    prompts = []
    for txt in text:
        prompts.append(format_prompt(txt, tokenizer, prompt_template))

    # batch generate outputs
    outputs = llm.generate(prompts, sampling_params)

    # parse output
    predictions = []
    reasons = []
    for output in outputs:
        generated_text = output.outputs[0].text
        # print(generated_text)
        out_dict = parse_output(generated_text, args)
        predictions.append(convert_to_numeric_label(out_dict))
        reasons.append(out_dict['reason'])

    return predictions, reasons


#############################################################
############ TGI on Gaudi ###################################
#############################################################

def generate_with_tgi(args=None, text = None, labels = None):
    from huggingface_hub import InferenceClient
    from concurrent.futures import ThreadPoolExecutor
    #TGI runs continuous batching: https://github.com/huggingface/text-generation-inference/tree/main/router#simple-continuous-batching
    #Therefore sending multiple requests concurrently can leverage it.

    ############## Need to debug and uncomment these lines################
    ####################################################################
    # make prompts
    # tokenizer = AutoTokenizer.from_pretrained(args.tokenizer)
    # prompts = []
    # for txt in text:
    #     prompts.append(format_prompt(txt, tokenizer, prompt_template))

    prompts = text

    # make samples
    # {'text': text, 'label': label}

    tgi_client = TgiClient(
        args.server_address, args.max_concurrent_requests
    )

    tgi_client.run_generation(
        prompts, args.max_new_tokens
    )

    # for input, output in zip(, ):
    #     print('input: ', input)
    #     print('output: ', output)
    #     print('='*50)
    
    # parse output
    predictions = []
    reasons = []
    for output in tgi_client._generated_text:
        out_dict = parse_output(output, args)
        predictions.append(convert_to_numeric_label(out_dict))
        reasons.append(out_dict['reason'])

    return tgi_client._input_text, predictions, reasons



# TGI client code is adapted from: 
# https://github.com/huggingface/tgi-gaudi/blob/habana-main/examples/tgi_client.py
import os
import statistics
import threading
import time
import tqdm
from typing import List

from huggingface_hub import InferenceClient


def except_hook(args):
    print(f"Thread failed with error: {args.exc_value}")
    os._exit(1)

threading.excepthook = except_hook


class TgiClient:
    def __init__(
        self,
        server_address: str,
        max_num_threads: int
    ) -> None:
        self._lock = threading.Lock()
        self._semaphore = threading.Semaphore(max_num_threads)
        self._client = InferenceClient(server_address)

        self._ttft = []
        self._tpot = []
        self._generated_text = []
        self._input_text = []

    def run_generation(
        self,
        samples: List[str],
        max_new_tokens: int
    ) ->  None:
        """
        Run generation for every sample in dataset.
        Creates a separate thread for every sample.
        """
        threads: List[threading.Thread] = []
        for sample in tqdm.tqdm(samples):
            self._semaphore.acquire()
            threads.append(
                threading.Thread(
                    target=self._process_sample, args=[sample, max_new_tokens]
                )
            )
            threads[-1].start()
        for thread in threads:
            if thread is not None:
                thread.join()

    def _process_sample(
        self,
        sample: str,
        max_new_tokens: int,
        # streaming: bool,
    ) -> str:
        """
        Generates response stream for a single sample.
        Collects performance metrics.
        """
        timestamp = time.perf_counter_ns()
        response = self._client.text_generation(
            sample, max_new_tokens=max_new_tokens, stream=False, details=True
        )
        
        self._semaphore.release()
        self._generated_text.append(response.generated_text)
        self._input_text.append(sample)

    def print_performance_metrics(
        self,
        duration_s: float
    ) -> None:
        def line():
            print(32*"-")

        line()
        print("----- Performance  summary -----")
        line()
        print(f"Throughput: {sum(self._generated_tokens) / duration_s:.1f} tokens/s")
        print(f"Throughput: {len(self._generated_tokens) / duration_s:.1f} queries/s")
        line()
        print(f"First token latency:")
        print(f"\tMedian: \t{statistics.median(self._ttft)*1e-6:.2f}ms")
        print(f"\tAverage: \t{statistics.fmean(self._ttft)*1e-6:.2f}ms")
        line()
        print(f"Output token latency:")
        print(f"\tMedian: \t{statistics.median(self._tpot)*1e-6:.2f}ms")
        print(f"\tAverage: \t{statistics.fmean(self._tpot)*1e-6:.2f}ms")
        line()


######################################################################
########### model.generate with optimum-habana ###################
#####################################################################
# Ref: https://github.com/huggingface/optimum-habana/blob/main/examples/text-generation/utils.py
def setup_env(args):
    import shutil
    import os
    # # Will error if the minimal version of Transformers is not installed. Remove at your own risks.
    # check_min_version("4.34.0")
    # check_optimum_habana_min_version("1.9.0.dev0")
    # # TODO: SW-167588 - WA for memory issue in hqt prep_model
    # os.environ.setdefault("EXPERIMENTAL_WEIGHT_SHARING", "FALSE")

    # if args.global_rank == 0 and not args.torch_compile:
    os.environ.setdefault("GRAPH_VISUALIZATION", "true")
    shutil.rmtree(".graph_dumps", ignore_errors=True)

    # if args.world_size > 0:
    #     os.environ.setdefault("PT_HPU_LAZY_ACC_PAR_MODE", "0")
    #     os.environ.setdefault("PT_HPU_ENABLE_LAZY_COLLECTIVES", "true")

    # Tweak generation so that it runs faster on Gaudi
    from optimum.habana.transformers.modeling_utils import adapt_transformers_to_gaudi
    adapt_transformers_to_gaudi()


def setup_device(args):
    if args.device == "hpu":
        import habana_frameworks.torch.core as htcore
    return torch.device(args.device)

def setup_generation_config(args, model):
    import copy
    # bad_words_ids = None
    # force_words_ids = None
    # if args.bad_words is not None:
    #     bad_words_ids = [tokenizer.encode(bad_word, add_special_tokens=False) for bad_word in args.bad_words]
    # if args.force_words is not None:
    #     force_words_ids = [tokenizer.encode(force_word, add_special_tokens=False) for force_word in args.force_words]

    # is_optimized = model_is_optimized(model.config)
    # Generation configuration
    generation_config = copy.deepcopy(model.generation_config)
    generation_config.max_new_tokens = args.max_new_tokens
    generation_config.use_cache = args.use_kv_cache
    generation_config.ignore_eos = False
    # generation_config.static_shapes = is_optimized # is_optimized not defined
    # generation_config.bucket_size = args.bucket_size if is_optimized else -1
    generation_config.bucket_size = -1 # not using the bucket size optimization
    generation_config.bucket_internal = args.bucket_internal
    generation_config.do_sample = args.do_sample
    generation_config.num_beams = args.num_beams
    # generation_config.bad_words_ids = bad_words_ids
    # generation_config.force_words_ids = force_words_ids
    generation_config.num_return_sequences = 1 #args.num_return_sequences # only generate 1 seq
    generation_config.trim_logits = args.trim_logits
    generation_config.attn_softmax_bf16 = args.attn_softmax_bf16
    # generation_config.limit_hpu_graphs = args.limit_hpu_graphs # we do want to use graph mode
    generation_config.reuse_cache = args.reuse_cache
    # generation_config.reduce_recompile = args.reduce_recompile # not using reduce_recompile optimization
    # if generation_config.reduce_recompile:
    #     assert generation_config.bucket_size > 0
    generation_config.use_flash_attention = args.use_flash_attention
    generation_config.flash_attention_recompute = args.flash_attention_recompute
    generation_config.flash_attention_causal_mask = args.flash_attention_causal_mask
    return generation_config



def setup_model_optimum_habana(args):
    setup_env(args)
    setup_device(args)

   
    model = AutoModelForCausalLM.from_pretrained(args.model, torch_dtype=torch.bfloat16)

    if args.use_hpu_graphs:
        from habana_frameworks.torch.hpu import wrap_in_hpu_graph
        model = wrap_in_hpu_graph(model)

    model = model.eval().to(args.device)
    tokenizer = AutoTokenizer.from_pretrained(args.tokenizer)

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        model.generation_config.pad_token_id = model.generation_config.eos_token_id

    generation_config = setup_generation_config(args, model)

    return model, tokenizer, generation_config


def batch_generate_gaudi(args, text, tokenizer, model, generation_config, prompt_template):
    import habana_frameworks.torch.hpu as torch_hpu
    input_dataset = CustomDataset(text, tokenizer,prompt_template)
    input_dataloader = DataLoader(input_dataset, batch_size=args.batch_size)

    predictions = []
    reasons = []

    for batch in tqdm.tqdm(input_dataloader):
        input_tokens = tokenizer.batch_encode_plus(batch, return_tensors="pt", padding=True) # padding has to be true otherwise error
        # input_shape = input_tokens.input_ids.shape[1]
        # send data to hpu device
        for t in input_tokens:
            if torch.is_tensor(input_tokens[t]):
                input_tokens[t] = input_tokens[t].to(args.device)
        
        outputs = model.generate(
                    **input_tokens,
                    generation_config=generation_config,
                    lazy_mode=args.gaudi_lazy_mode,
                    hpu_graphs=args.use_hpu_graphs,
                    # profiling_steps=args.profiling_steps,
                    # profiling_warmup_steps=args.profiling_warmup_steps,
                ).cpu()
        # print('Generated tokens number: ', outputs.shape[1]-input_shape)
        
        decoded_outputs = tokenizer.batch_decode(outputs, skip_special_tokens=True)

        for i in range(len(decoded_outputs)):
            decoded_txt = decoded_outputs[i]
            # print('decoded text: ', decoded_txt)
            out_dict = parse_output(decoded_txt, args)
            # print(out_dict)
            predictions.append(convert_to_numeric_label(out_dict))
            reasons.append(out_dict['reason'])
            # print(predictions)

        # print(decoded_outputs)
        # print("="*50)
    return predictions, reasons

def single_generate_gaudi(args, text, tokenizer, model, generation_config, prompt_template):
    chat = [
            {"role": "user",
            "content":prompt_template.format(text=text)}
        ]
    prompt = tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=True)
    input_tokens = tokenizer.encode_plus(prompt, return_tensors="pt")
    for t in input_tokens:
        if torch.is_tensor(input_tokens[t]):
            input_tokens[t] = input_tokens[t].to(args.device)
    
    outputs = model.generate(
                    **input_tokens,
                    generation_config=generation_config,
                    lazy_mode=args.gaudi_lazy_mode,
                    hpu_graphs=args.use_hpu_graphs,
                    # profiling_steps=args.profiling_steps,
                    # profiling_warmup_steps=args.profiling_warmup_steps,
                ).cpu()
        
    decoded_outputs = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(decoded_outputs)


#######################################################################

def generate_text(model = None, tokenizer= None, prompt = None, generation_params = None):
    
    tokenized_prompt = tokenizer.apply_chat_template(prompt, tokenize=True, add_generation_prompt=True, return_tensors="pt")
    # print('prompt applied with template: \n', tokenizer.apply_chat_template(prompt, tokenize=False))

    tokenized_prompt = tokenized_prompt.to('cuda')
    encoded_output = model.generate(tokenized_prompt, **generation_params)
    # print(encoded_output)
    output = tokenizer.decode(encoded_output[0])
    print('generated output:\n', output)
    return output


def sequential_generate_with_model_generate(args=None, generation_params=None, text = None):
    tokenizer = AutoTokenizer.from_pretrained(args.tokenizer) #"mistralai/Mixtral-8x7B-Instruct-v.01"
    model = AutoModelForCausalLM.from_pretrained(args.model, device_map="auto")

    predictions = []
    reasons =[]
    for t in tqdm(text):

        chat = [
            {"role": "user",
            "content":PROMPT.format(text=t)}
        ]

        # prompt_for_llm = tokenizer.apply_chat_template(chat, tokenize=False)

        output = generate_text(model, tokenizer, chat, generation_params)

        output = parse_output(output, args)

        predictions.append(convert_to_numeric_label(output))
        reasons.append(output['reason'])

        print("="*50)


    return predictions, reasons


def batch_generation_with_model_generate(args=None, generation_params=None, text = None):
    tokenizer = AutoTokenizer.from_pretrained(args.tokenizer) #"mistralai/Mixtral-8x7B-Instruct-v.01"
    tokenizer.pad_token = tokenizer.eos_token
    # tokenizer.padding_side = "left"

    model = AutoModelForCausalLM.from_pretrained(args.model, device_map="auto")
    input_dataset = CustomDataset(text, tokenizer)
    input_dataloader = DataLoader(input_dataset, batch_size=args.batch_size)

    predictions = []
    reasons = []

    for batch in input_dataloader:
        inputs = tokenizer(batch, padding=True, return_tensors = 'pt').to(args.device)
        # batch = {k: v.to(args.device) for k, v in batch.items()}
        with torch.no_grad():
            outputs = model.generate(**inputs, **generation_params)
            generated_txts = tokenizer.batch_decode(outputs)
            # print(generated_txts)

        for i in range(len(generated_txts)):
            txt = generated_txts[i]
            out_dict = parse_output(txt, args)
            predictions.append(convert_to_numeric_label(out_dict))
            reasons.append(out_dict['reason'])
    
    return predictions, reasons


def generate_with_pipeline(args = None, text= None, generation_params=None):
    tokenizer = AutoTokenizer.from_pretrained(args.tokenizer)
    
    inputs = CustomDataset(text, tokenizer)
    pipe = pipeline(
        "text-generation", 
        model = args.model, 
        device_map = "auto", 
        **generation_params)

    # Pipeline with tokenizer without pad_token cannot do batching.
    pipe.tokenizer.pad_token_id = tokenizer.eos_token_id

    for out in tqdm(pipe(inputs, batch_size = args.batch_size, **generation_params)):
        print(out)
        # for i in range(args.batch_size):
        #     print(out[i]['generated_text'])
        # generated_text_batch = out[0]['generated_text']
        # print(generated_text_batch)



def run_llm_inference_alternatives(args, text, prompt_template):
    generation_params = dict(
        top_p=args.top_p, #0.90,
        temperature=args.temperature, #0.8,
        max_new_tokens=args.max_new_tokens, #128,
        # return_full_text=False,
        do_sample=True,
        use_cache=False
    )
    if args.generate_with_pipeline == True:
        generate_with_pipeline(args, text, generation_params)

    elif args.batch_model_generate == True:
        predictions, reasons = batch_generation_with_model_generate(args, generation_params, text)

    elif args.vllm_offline == True:
        predictions, reasons = vllm_batched_offline_generation(args, text, prompt_template)
    elif args.tgi_concurrent == True:
        generate_with_tgi(args, text)
    else:
        predictions, reasons = sequential_generate_with_model_generate(args, generation_params, text)

    return predictions, reasons