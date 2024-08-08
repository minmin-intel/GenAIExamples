from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

rlm_rag_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "human",
            "You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.Question: {question} Context: {context} Answer:",
        ),
    ]
)


DOC_GRADER_PROMPT="""\
Given the QUERY, determine if a relevant answer can be derived from the DOCUMENT.\n
QUERY: {question} \n
DOCUMENT:\n{context}\n\n
Give score 'yes' if the document provides sufficient and relevant information to answer the question. Otherwise, give score 'no'. ONLY answer with 'yes' or 'no'. NOTHING ELSE."""


PROMPT = """\
### You are a helpful, respectful and honest assistant.
You are given a Question and the time when it was asked in the Pacific Time Zone (PT), referred to as "Query
Time". The query time is formatted as "mm/dd/yyyy, hh:mm:ss PT".
Please follow these guidelines when formulating your answer:
1. If the question contains a false premise or assumption, answer “invalid question”.
2. If you are uncertain or do not know the answer, respond with “I don’t know”.
3. Refer to the search results to form your answer.
4. Give concise, factual and relevant answers.

### Search results: {context} \n
### Question: {question} \n
### Query Time: {time} \n
### Answer:
"""

RAGv1_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "human",
            PROMPT,
        ),
    ]
)

REACT_SYS_MESSAGE="""\
Please follow these guidelines when formulating your answer:
1. If the question contains a false premise or assumption, answer “invalid question”.
2. If you are uncertain or do not know the answer, respond with “I don’t know”.
3. Refer to the search results to form your answer.
4. Give concise, factual and relevant answers.
"""

REACT_SYS_MESSAGE_V2="""\
Decompose the user request into a series of simple tasks when necessary and solve the problem step by step.
When you cannot get the answer at first, do not give up. Reflect on the info you have from the tools and try to solve the problem in a different way.
Please follow these guidelines when formulating your answer:
1. If the question contains a false premise or assumption, answer “invalid question”.
2. If you are uncertain or do not know the answer, respond with “I don’t know”.
3. Give concise, factual and relevant answers.
"""



REWRITER_PROMPT_TEMPLATE ="""\
Reason about the underlying semantic intent and meaning of the original query and write an improved version.
Original Query: {question}\n
The re-formulated query should be affirmative form sentences.
Reformulated Query:
"""
REWRITER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "assistant",
            REWRITER_PROMPT_TEMPLATE,
        ),
    ]
)