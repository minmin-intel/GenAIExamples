# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

import requests
from tools.pycragapi import CRAG

def question_answering_agent(query: str) -> str:
    pass

def summarization_agent(doc_title: str) -> str:
    ret = """
Twilio reported strong Q4 2023 financial results, with revenue of $1.076 billion exceeding guidance and growing 5% reported and 8% organically year-over-year. The company demonstrated improved profitability, with non-GAAP income from operations of $173 million, beating expectations due to robust revenue and cost discipline. Twilio also made significant operational progress, signing its largest-ever messaging deal and showcasing its platform's reliability during Cyber Week. Looking ahead, Twilio provided Q1 2024 guidance of $1.025-1.035 billion in revenue and $120-130 million in non-GAAP income from operations. The company expects to exceed 2023's non-GAAP income for the full year 2024, despite $90 million in bonus expenses. Strategically, Twilio is conducting an operational review of its underperforming Segment business and plans to provide an update in March. The company continues to innovate by integrating AI capabilities into its products, aiming to create more personalized interactions for customers. However, Twilio faces challenges with its Segment business, which led to a $286 million impairment charge on acquisition intangibles. The company also expects continued revenue growth headwinds from crypto customers in Q1 2024. Management highlighted the significant progress made in 2023 on revenue growth, profitability, cash flow, and stock-based compensation reduction. New CEO Khozema Shipchandler expressed optimism in Twilio's opportunity as a leading customer engagement platform and reaffirmed the company's vision. Overall, Twilio delivered strong Q4 results and made progress on its strategic initiatives, positioning the company for durable growth. However, the company must address challenges in its Segment business to maintain its momentum.
    """
    return ret

def research_agent(company: str) -> str:
    pass


def search_web(query: str)->str:
    '''Search the web for information not contained in databases.'''
    from langchain_core.tools import Tool
    from langchain_google_community import GoogleSearchAPIWrapper

    search = GoogleSearchAPIWrapper()

    tool = Tool(
        name="google_search",
        description="Search Google for recent results.",
        func=search.run,
    )

    response = tool.run(query)
    return response

# if __name__ == "__main__":
#     print(search_web('Who is the lead singer of the band Queen?'))


def search_knowledge_base(query: str) -> str:
    """Search a knowledge base about music and singers for a given query.

    Returns text related to the query.
    """
    url = os.environ.get("WORKER_AGENT_URL")
    print(url)
    proxies = {"http": ""}
    payload = {
        "messages": query,
    }
    response = requests.post(url, json=payload, proxies=proxies)
    return response.json()["text"]


def search_sql_database(query: str) -> str:
    """Search a SQL database on artists and their music with a natural language query.

    Returns text related to the query.
    """
    url = os.environ.get("SQL_AGENT_URL")
    print(url)
    proxies = {"http": ""}
    payload = {
        "messages": query,
    }
    response = requests.post(url, json=payload, proxies=proxies)
    return response.json()["text"]


def get_grammy_best_artist_by_year(year: int) -> dict:
    """Get the Grammy Best New Artist for a specific year."""
    api = CRAG()
    year = int(year)
    return api.music_grammy_get_best_artist_by_year(year)


def get_members(band_name: str) -> dict:
    """Get the member list of a band."""
    api = CRAG()
    return api.music_get_members(band_name)


def get_artist_birth_place(artist_name: str) -> dict:
    """Get the birthplace of an artist."""
    api = CRAG()
    return api.music_get_artist_birth_place(artist_name)


def get_billboard_rank_date(rank: int, date: str = None) -> dict:
    """Get Billboard ranking for a specific rank and date."""
    api = CRAG()
    rank = int(rank)
    return api.music_get_billboard_rank_date(rank, date)


def get_song_release_date(song_name: str) -> dict:
    """Get the release date of a song."""
    api = CRAG()
    return api.music_get_song_release_date(song_name)
