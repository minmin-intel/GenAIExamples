import os
from pycragapi import CRAG

print(os.environ.get("CRAG_SERVER", "http://localhost:8080"))
api = CRAG()
print(api.music_grammy_get_best_artist_by_year(2019))
print(api.music_grammy_get_award_count_by_artist("Taylor Swift"))
print(api.music_get_members("The Beatles"))
print(api.music_search_artist_entity_by_name("Taylor Swift"))
