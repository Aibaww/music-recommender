import requests

def get_song_recommendations(valence, energy, genres, token):
    '''Get recommendations from Spotify using seed genres and a target valence and energy'''
    url = "https://api.spotify.com/v1/recommendations"
    
    params = {
        "seed_genres": genres,
        "target_valence": valence,
        "target_energy": energy,
        "limit": 10
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers, params=params)
    response_data = response.json()
    
    if response.status_code == 200:
        print("**Got recommendations, returning...**")
        return [(track["name"], track["artists"][0]["name"]) for track in response_data["tracks"]]
    else:
        print("**ERROR: failed to get recommendations**")
        print(response_data)
        return []