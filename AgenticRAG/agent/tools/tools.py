from langchain_core.tools import tool
import requests
import os
from tools.pycragapi import CRAG

@tool
def search_knowledge_base(query:str)->str:
    '''Search knowledge base for a given query. Returns text related to the query.'''
    retrieval_url = os.environ.get("RETRIEVAL_TOOL_URL", "http://localhost:8889/v1/retrievaltool")
    data = {"text":query}
    # header = {"Content-Type": "application/json"}
    proxies = {"http": ""}
    response = requests.post(retrieval_url, json=data, proxies=proxies) #, headers=header)
    return response.json()["text"]


@tool
def retrieve_from_knowledge_base(query:str)->str:
    '''Search knowledge base for a given query. Returns text related to the query.'''
    retrieval_url = os.environ.get("RETRIEVAL_TOOL_URL", "http://localhost:8889/v1/retrievaltool")
    data = {"text":query}
    # header = {"Content-Type": "application/json"}
    proxies = {"http": ""}
    response = requests.post(retrieval_url, json=data, proxies=proxies) #, headers=header)
    return response.json()["text"]
   

@tool
def search_artist_entity_by_name(artist_name: str) -> dict: 
    '''Search for music artists by name.'''
    api = CRAG()
    return api.music_search_artist_entity_by_name(artist_name)

@tool
def search_song_entity_by_name(song_name: str) -> dict:
    '''Search for songs by name.'''
    api = CRAG()
    return api.music_search_song_entity_by_name(song_name)

@tool
def get_billboard_rank_date(rank: int, date: str = None) -> dict:
    '''Get Billboard ranking for a specific rank and date.'''
    api = CRAG()
    rank = int(rank)
    return api.music_get_billboard_rank_date(rank, date)

@tool
def get_billboard_attributes(date: str, attribute: str, song_name: str) -> dict:
    '''Get attributes of a song from Billboard rankings.'''
    api = CRAG()
    return api.music_get_billboard_attributes(date, attribute, song_name)

@tool
def get_grammy_best_artist_by_year(year: int) -> dict:
    '''Get the Grammy Best New Artist for a specific year.'''
    api = CRAG()
    year = int(year)
    return api.music_grammy_get_best_artist_by_year(year)

@tool
def get_grammy_award_count_by_artist(artist_name: str) -> dict:
    '''Get the total Grammy awards won by an artist.'''
    api = CRAG()
    return api.music_grammy_get_award_count_by_artist(artist_name)

@tool
def get_grammy_award_count_by_song(song_name: str) -> dict:
    '''Get the total Grammy awards won by a song.'''
    api = CRAG()
    return api.music_grammy_get_award_count_by_song(song_name)

@tool
def get_grammy_best_song_by_year(year: int) -> dict:
    '''Get the Grammy Song of the Year for a specific year.'''
    api = CRAG()
    year = int(year)
    return api.music_grammy_get_best_song_by_year(year)


@tool
def get_grammy_award_date_by_artist(artist_name: str) -> dict:
    '''Get the years an artist won a Grammy award.'''
    api = CRAG()
    return api.music_grammy_get_award_date_by_artist(artist_name)

@tool
def get_grammy_best_album_by_year(year: int) -> dict:
    '''Get the Grammy Album of the Year for a specific year.'''
    api = CRAG()
    year = int(year)
    return api.music_grammy_get_best_album_by_year(year)

@tool
def get_all_awarded_artists() -> dict:
    '''Get all artists awarded the Grammy Best New Artist.'''
    api = CRAG()
    return api.music_grammy_get_all_awarded_artists()

@tool
def get_artist_birth_place(artist_name: str) -> dict:
    '''Get the birthplace of an artist.'''
    api = CRAG()
    return api.music_get_artist_birth_place(artist_name)

@tool
def get_artist_birth_date(artist_name: str) -> dict:
    '''Get the birth date of an artist.'''
    api = CRAG()
    return api.music_get_artist_birth_date(artist_name)

@tool
def get_members(band_name: str) -> dict:
    '''Get the member list of a band.'''
    api = CRAG()
    return api.music_get_members(band_name)

@tool
def get_lifespan(artist_name: str) -> dict:
    '''Get the lifespan of an artist.'''
    api = CRAG()
    return api.music_get_lifespan(artist_name)

@tool
def get_song_author(song_name: str) -> dict:
    '''Get the author of a song.'''
    api = CRAG()
    return api.music_get_song_author(song_name)

@tool
def get_song_release_country(song_name: str) -> dict:
    '''Get the release country of a song.'''
    api = CRAG()
    return api.music_get_song_release_country(song_name)

@tool
def get_song_release_date(song_name: str) -> dict:
    '''Get the release date of a song.'''
    api = CRAG()
    return api.music_get_song_release_date(song_name)

@tool
def get_artist_all_works(artist_name: str) -> dict:
    '''Get all works by an artist.'''
    api = CRAG()
    return api.music_get_artist_all_works(artist_name)


def get_all_available_tools():
    tools = [search_artist_entity_by_name, 
         search_song_entity_by_name, 
         get_billboard_rank_date, 
         get_billboard_attributes, 
         get_grammy_best_artist_by_year, 
         get_grammy_award_count_by_artist, 
         get_grammy_award_count_by_song,
         get_grammy_best_song_by_year,
         get_grammy_award_date_by_artist,
         get_grammy_best_album_by_year,
            get_all_awarded_artists,
            get_artist_birth_place,
            get_artist_birth_date,
            get_members,
            get_lifespan,
            get_song_author,
            get_song_release_country,
            get_song_release_date,
            get_artist_all_works]
    return tools

# music_search_song_entity_by_name(song_name: str) -> dict: Search for songs by name.
# music_get_billboard_rank_date(rank: int, date: str = None) -> dict: Get Billboard ranking for a specific rank and date.
# music_get_billboard_attributes(date: str, attribute: str, song_name: str) -> dict: Get attributes of a song from Billboard rankings.
# music_grammy_get_best_artist_by_year(year: int) -> dict: Get the Grammy Best New Artist for a specific year.
# music_grammy_get_award_count_by_artist(artist_name: str) -> dict: Get the total Grammy awards won by an artist.
# music_grammy_get_award_count_by_song(song_name: str) -> dict: Get the total Grammy awards won by a song.
# music_grammy_get_best_song_by_year(year: int) -> dict: Get the Grammy Song of the Year for a specific year.
# music_grammy_get_award_date_by_artist(artist_name: str) -> dict: Get the years an artist won a Grammy award.
# music_grammy_get_best_album_by_year(year: int) -> dict: Get the Grammy Album of the Year for a specific year.
# music_grammy_get_all_awarded_artists() -> dict: Get all artists awarded the Grammy Best New Artist.
# music_get_artist_birth_place(artist_name: str) -> dict: Get the birthplace of an artist.
# music_get_artist_birth_date(artist_name: str) -> dict: Get the birth date of an artist.
# music_get_members(band_name: str) -> dict: Get the member list of a band.
# music_get_lifespan(artist_name: str) -> dict: Get the lifespan of an artist.
# music_get_song_author(song_name: str) -> dict: Get the author of a song.
# music_get_song_release_country(song_name: str) -> dict: Get the release country of a song.
# music_get_song_release_date(song_name: str) -> dict: Get the release date of a song.
# music_get_artist_all_works(artist_name: str) -> dict: Get all works by an artist.
