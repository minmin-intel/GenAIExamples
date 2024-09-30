import os
import requests



def search_knowledge_base(query: str) -> str:
    """Search the knowledge base for a specific query."""
    # use worker agent (DocGrader) to search the knowledge base
    url = os.environ.get("WORKER_AGENT_URL")
    print(url)
    proxies = {"http": "", "https": ""}
    payload = {
        "query": query,
    }
    response = requests.post(url, json=payload, proxies=proxies)
    return response.json()["text"]


if __name__ == "__main__":
    print(search_knowledge_base("Who is the best new artist in 2020?"))