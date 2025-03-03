def search_knowledge_base(query: str) -> str:
    # from langchain_core.tools import Tool
    # from langchain_google_community import GoogleSearchAPIWrapper

    # search = GoogleSearchAPIWrapper()

    # tool = Tool(
    #     name="google_search",
    #     description="Search Google for recent results.",
    #     func=search.run,
    # )

    # response = tool.run(query)
    # return response
    ret_text = """
    The Linux Foundation AI & Data announced the Open Platform for Enterprise AI (OPEA) as its latest Sandbox Project.
    OPEA aims to accelerate secure, cost-effective generative AI (GenAI) deployments for businesses by driving interoperability across a diverse and heterogeneous ecosystem, starting with retrieval-augmented generation (RAG).
    """
    return ret_text