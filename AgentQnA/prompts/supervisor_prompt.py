REACT_AGENT_LLAMA_PROMPT = """\
You are a helpful assistant engaged in multi-turn conversations with users.
You have the following worker agents working for you. You can call them as calling tools.
{tools}

**Procedure:**
1. Read the question carefully. Decide which agent you should call to answer the question.
2. The worker agents need detailed inputs. Ask the user to clarify when you lack certain info or are uncertain about something. Do not assume anything. For example, user asks about "recent earnings call of Microsoft", ask the user to specify the quarter and year.
3. Read the execution history if any to understand the worker agents that have been called and the information that has been gathered.
4. Reason about the information gathered so far and decide if you can answer the question or if you need to gather more info.

**Output format:**
You should output your thought process. Finish thinking first. Output tool calls or your answer at the end.
When calling worker agents, you should use the following tool-call format:
TOOL CALL: {{"tool": "tool1", "args": {{"arg1": "value1", "arg2": "value2", ...}}}}
TOOL CALL: {{"tool": "tool2", "args": {{"arg1": "value1", "arg2": "value2", ...}}}}

If you can answer the question, provide the answer in the following format:
FINAL ANSWER: {{"answer": "your answer here"}}

======= Conversations with user in previous turns =======
{thread_history}
======= End of previous conversations =======

======= Your execution History in this turn =========
{history}
======= End of execution history ==========

Now take a deep breath and think step by step to answer user's question in this turn.
USER MESSAGE: {input}
"""

FINQA_PROMPT = """\
You are a financial analyst. Given the question below, determine what financial document may contain the information needed to answer the question, for example, 10-K, 8-K, 10-Q, earnings report.
Reason through the question and provide the name of the document in {{<COMPANY> <YEAR> <QUARTER (optional)> <DOC TYPE>}}.

Examples:
Question: What is the FY2018 capital expenditure amount (in USD millions) for Apple?
Answer: Apple's FY2018 capital expenditure amount can be found in the 10-K filing for FY2018. So the document is {{Apple 2018 10-K}}.

Question: Does Apple have a reasonably healthy liquidity in Q2 of 2023?
Answer: Apple's liquidity profile in Q2 of 2023 can be found in the 10-Q filing for Q2 of 2023. So the document is {{Apple 2023 Q2 10-Q}}.

Now, here is the question:
{question}
What financial document may contain the information needed to answer the question?
"""

from openai import OpenAI
import pandas as pd
import os
import json

def generate_answer(args, prompt):
    """
    Use vllm endpoint to generate the answer
    """
    # send request to vllm endpoint
    client = OpenAI(
        base_url=f"{args.llm_endpoint_url}/v1",
        api_key="token-abc123",
    )

    params = {
        "max_tokens": args.max_new_tokens,
        "temperature": args.temperature,
    }

    completion = client.chat.completions.create(
        model=args.model,
        messages=[
            {"role": "user", "content": prompt}
        ],
        **params
        )

    # get response
    response = completion.choices[0].message.content

    return response

def parse_response(response):
    """
    Parse the response from the LLM
    """
    return response.split("{")[-1].split("}")[0]
    

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--llm_endpoint_url", type=str, default="http://localhost:8086")
    parser.add_argument("--model", type=str, default="meta-llama/Llama-3.3-70B-Instruct")
    parser.add_argument("--max_new_tokens", type=int, default=4096)
    parser.add_argument("--temperature", type=float, default=0.5)
    parser.add_argument("--test_supervisor", action="store_true")
    args = parser.parse_args()

    if args.test_supervisor:
        rag_agent = """question_answering_agent - answer financial questions about a company. use this agent if want to get answers about financial details, args: ['query (string): should include company name and time, for example, which business unit had the highest growth for Microsoft in 2024.']"""
        summary_agent = """summarization_agent - generate high-lelvel summary of a financial document, args: ['doc_title (string): the description of the document, should include company name and time, for example, Apple 2023 Q4 earnings call.']"""
        research_agent = """research_agent - generate research report on a specified company with fundamentals analysis, sentiment analysis and risk analysis, args: ['company (string): the company name']"""

        thread_history = ""
        turn_history = ""

        input_list = [
            "What is the FY2018 capital expenditure amount (in USD millions) for 3M?",
            "Does 3M have a reasonably healthy liquidity profile based on its quick ratio for Q2 of FY2023?",
            "What drove operating margin change as of FY2022 for 3M?",
            "Can you summarize Intel's Q1 2024 earnings call?",
            "Key takeaways of the recent earnings call of Tesla?",
            "Should I increase investment in Tesla?",
        ]


        for input in input_list:
            print(f"USER MESSAGE: {input}\n")
            prompt = REACT_AGENT_LLAMA_PROMPT.format(
                tools=f"{rag_agent}\n{summary_agent}\n{research_agent}",
                thread_history=thread_history,
                history=turn_history,
                input=input
            )

            response = generate_answer(args, prompt)
            print(response)
            print("="*50)
        else:
            WORKDIR=os.getenv('WORKDIR')
            DATAPATH=os.path.join(WORKDIR, 'financebench/data/')
            PDFPATH=os.path.join(WORKDIR, 'financebench/pdfs/')

            filename = "financebench_open_source.jsonl"
            df = pd.read_json(DATAPATH + filename, lines=True)

            for i, row in df.iterrows():
                query = row["question"]
                doc_name = row["doc_name"]

                print(f"Question: {query}")
                prompt = FINQA_PROMPT.format(question=query)
                response = generate_answer(args, prompt)
                response = parse_response(response)
                print(response)
                print("="*50)
                