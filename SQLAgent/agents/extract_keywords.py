from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage, SystemMessage
import os
from .prompt import HINT_TEMPLATE_BM25

def setup_tgi(args):
    from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

    llm = HuggingFaceEndpoint(
        endpoint_url=args.llm_endpoint_url,
        task="text-generation",
        max_new_tokens=128,
        do_sample=False,
    )

    chat_model = ChatHuggingFace(llm=llm)
    return chat_model

class HintNodeKeywordExtraction:
    def __init__(self, args):
        if args.tgi:
            llm = setup_tgi(args)
        else:
            llm = ChatOpenAI(model=args.model,temperature=0)
        prompt = PromptTemplate(
            template=HINT_TEMPLATE_BM25,
            input_variables=["DOMAIN","QUESTION"],
        )
        self.chain = prompt | llm
        self.args = args
        # complete_descriptions, _ = generate_column_descriptions(db_name=args.db_name)
        # documents = make_documents_from_column_descriptions(complete_descriptions)
        # topk=1
        # self.retriever = BM25Retriever.from_documents(documents, k = topk)
        # self.cols_descriptions, self.values_descriptions = generate_column_descriptions(db_name=args.db_name)
        # self.embed_model = SentenceTransformer('BAAI/bge-base-en-v1.5')
        # self.column_embeddings = self.embed_model.encode(self.values_descriptions)


    def __call__(self, state):
        print("----------Call Hint Node----------")
        question = state["messages"][0].content
        response = self.chain.invoke(
            {
                "DOMAIN": str(self.args.db_name),
                "QUESTION": question,
            }
        )
        keywords = response.content
        print("@@@@@ Keywords: ", keywords)
        return keywords
        # hints = []
        # for keyword in keywords.split(","):
        #     # hints_bm25 = pick_hints_bm25(self.retriever, keyword)
        #     hints_kw = pick_hints(keyword, self.column_embeddings,self.cols_descriptions)
        #     hints.append(hints_kw)
        # hints_set = set(hints)
        # selected_hints = "\n".join(hints_set)
        # print("@@@@@ Selected Hints: ", selected_hints)
        # return {"hint": selected_hints}


if __name__ == "__main__":
    import argparse
    import pandas as pd
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="meta-llama/Llama-3.1-70B-Instruct")
    parser.add_argument("--db_name", type=str, default="california_schools")
    parser.add_argument("--query_file", type=str, default="query.json")
    parser.add_argument("--tgi", action="store_true")
    parser.add_argument("--llm_endpoint_url", type=str, default="http://localhost:8085")

    args = parser.parse_args()

    hint_gen=HintNodeKeywordExtraction(args)

    df = pd.read_csv(f"{os.getenv('WORKDIR')}/TAG-Bench/query_by_db/query_california_schools.csv")
    hint_col = []
    for _, row in df.iterrows():
        query = row["Query"]
        print("Query: ", query)
        state = {
            "messages": [HumanMessage(content=query)],
            # "is_last_step": IsLastStep(False),
            # "hint": ""
        }
        res = hint_gen(state)
        hint_col.append(res)
        print("=="*20)
    df["keywords"] = hint_col
    df.to_csv(f"{os.getenv('WORKDIR')}/sql_agent_output/keywords.csv", index=False)
    
    # # query = "Of the cities containing exclusively virtual schools which are the top 3 safest places to live?"
    # # query = "Of the schools with the top 3 SAT excellence rate, which county of the schools has the strongest academic reputation?"
    # query = "Please list the top three continuation schools with the lowest eligible free rates for students aged 5-17 and rank them based on the overall affordability of their respective cities."
    # state = {
    #     "messages": [HumanMessage(content=query)],
    #     "is_last_step": IsLastStep(False),
    #     "hint": ""
    # }
    # hint_gen(state)
