
import logging
import time
import torch
import habana_frameworks.torch.hpu as torch_hpu
from optimum_habana_text_gen_utils import initialize_model
import tqdm
from utils import setup_dataloader
from llm_inference import parse_output, convert_to_numeric_label


def setup_model_optimum_habana(args, text, prompt_template):
    logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
    level=logging.INFO,
    )   
    logger = logging.getLogger(__name__)

    model, tokenizer, generation_config = initialize_model(args, logger)
    generation_config.ignore_eos=False

    dataloader = setup_dataloader(args, text, tokenizer, prompt_template)
    
    complie_graph(dataloader, args, model, tokenizer,generation_config)

    return model, tokenizer, generation_config
  


def batch_generate_optimum_habana(args, batch, model, tokenizer,generation_config):
    # Move inputs to target device(s)
    batch = tokenizer.batch_encode_plus(batch, return_tensors="pt", padding="max_length", truncation=True, max_length=2048)
    # print(batch)
    for t in batch:
        if torch.is_tensor(batch[t]):
            # print(batch[t].shape)
            batch[t] = batch[t].to(args.device)
    # Generate new sequences
    outputs = model.generate(
        **batch,
        generation_config=generation_config,
        lazy_mode=args.gaudi_lazy_mode,
        hpu_graphs=args.use_hpu_graphs,
        profiling_steps=args.profiling_steps,
        profiling_warmup_steps=args.profiling_warmup_steps,
    ).cpu() 

    decoded = tokenizer.batch_decode(outputs, skip_special_tokens=True)

    return decoded   

def complie_graph(dataloader, args, model, tokenizer,generation_config):
    # compilation stage disable profiling
    # HabanaProfile.disable()
    # Compilation
    # logger.info("Graph compilation...")
    print('Compiling graph...')
    t0 = time.perf_counter()
    for i, batch in enumerate(dataloader):
        batch_generate_optimum_habana(args, batch, model, tokenizer,generation_config)
        # The first three iterations take longer because of graph compilation
        if (i + 1) == 3:
            break
    torch_hpu.synchronize()
    compilation_duration = time.perf_counter() - t0
    # HabanaProfile.enable()
    print('Graph compilation time: {:.2f} seconds'.format(compilation_duration))




def text_gen_optimum_habana(args, text, prompt_template, model, tokenizer, generation_config):
    predictions = []
    reasons = []

    dataloader = setup_dataloader(args, text, tokenizer, prompt_template)

    for batch in tqdm.tqdm(dataloader):
        # print(batch)
        outputs = batch_generate_optimum_habana(args, batch, model, tokenizer,generation_config)
        # print(outputs)

        for i in range(len(outputs)):
            decoded_txt = outputs[i]
            # print('decoded text: ', decoded_txt)
            out_dict = parse_output(decoded_txt, args)
            # print('parsed output: ',out_dict)
            predictions.append(convert_to_numeric_label(out_dict))
            reasons.append(out_dict['reason'])
            # print(predictions)

    return predictions, reasons


