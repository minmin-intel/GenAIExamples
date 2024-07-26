from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

llm = HuggingFaceEndpoint(
    endpoint_url="http://localhost:9009",
    task="text-generation",
    max_new_tokens=10,
    do_sample=False,
)
res = llm.invoke("Hugging Face is")
print(res)
print('-------------------')

llm_engine_hf = ChatHuggingFace(llm=llm, model_id = "Intel/neural-chat-7b-v3-3")
res = llm_engine_hf.invoke("Hugging Face is")
print(res)
