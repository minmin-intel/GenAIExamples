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