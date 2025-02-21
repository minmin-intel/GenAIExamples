REACT_AGENT_LLAMA_PROMPT = """\
You are a helpful assistant engaged in multi-turn conversations with users.
You have the following worker agents working for you. You can call them as calling tools.
{tools}

**Procedure:**
1. Read the question carefully. Decide which agent you should call to answer the question.
2. Ask the user for more information if needed.
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

from openai import OpenAI

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

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--llm_endpoint_url", type=str, default="http://localhost:8086")
    parser.add_argument("--model", type=str, default="meta-llama/Llama-3.3-70B-Instruct")
    parser.add_argument("--max_new_tokens", type=int, default=4096)
    parser.add_argument("--temperature", type=float, default=0.5)
    args = parser.parse_args()

    rag_agent = """question_answering_agent - answer financial questions about a company, args: [query: str]"""
    summary_agent = """summarization_agent - summarize financial documents, args: [doc_name: str]"""
    research_agent = """research_agent - do investment research on a specified company, args: [company: str]"""

    thread_history = ""
    turn_history = ""

    input_list = [
        "What is the FY2018 capital expenditure amount (in USD millions) for 3M?",
        "Can you summarize Apple's Q1 2021 earnings call?",
    ]


    for input in input_list:
        prompt = REACT_AGENT_LLAMA_PROMPT.format(
            tools=f"{rag_agent}\n{summary_agent}\n{research_agent}",
            thread_history=thread_history,
            history=turn_history,
            input=input
        )

        response = generate_answer(args, prompt)
        print(response)
        print("="*50)