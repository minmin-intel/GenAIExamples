import os
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

def setup_llm(args):
    generation_params = {
        "max_new_tokens": args.max_new_tokens,
        "top_k": args.top_k,
        "top_p": args.top_p,
        "temperature": args.temperature,
        "repetition_penalty": args.repetition_penalty,
        "return_full_text": args.return_full_text,
        "streaming": args.streaming,
    }

    llm_endpoint_url = os.environ.get("TGI_LLM_ENDPOINT", "localhost:8080")

    llm = HuggingFaceEndpoint(
        endpoint_url=llm_endpoint_url,
        task="text-generation",
        timeout=1200, # for testing 70B model on CPU
        **generation_params,
    )
    return llm

def setup_hf_tgi_client(args):
    
    llm = setup_llm(args)

    print('Testing llm endpoint...')
    print(llm.invoke("Hello!"))

    model = ChatHuggingFace(llm=llm, model_id=args.model_id)

    print('Testing Chat model...')
    print(model.invoke("Hello!"))

    return model