import requests
import mediathekWeb
import argparse
import util
import download as dl

# Globals
TMDB_API_KEY = "632ca26bdf69f230197d4a063ec62f10"
OMDB_API_KEY = "ddac1be6"
JELLYFIN_API_KEY = "5ddd91b4e53b430a9efae52655d60f20"
JELLYFIN_USER_ID = "1d5044ab79154b2f8a548ba9ede2aa2a"

validChannels = ["ard", "srf", "arte", "zdf", "zdfneo"]

# Parse CLI Arguments
parser = argparse.ArgumentParser(prog="MediathekViewBot",
                                 description="Scans MediathekView for films and checks their rating using TMDB. Generates a file with urls to the films matching the filter criteria.")
                                 
parser.add_argument("-v", "--verbose", action="store_true")
parser.add_argument("-s", "--size")
parser.add_argument("-c", "--channel", choices=validChannels,help="Auswahl des zu durchsuchenden Kanals.", default="ard")
parser.add_argument("-t", "--topic")
parser.add_argument("-r", "--min_rating")
parser.add_argument("-p", "--min_popularity")
parser.add_argument("-o", "--output_path")

def deduplicate_list(inputList, verbose = False):
    deduplicatedList = []
    titleList = []
    if verbose: 
        print("Deduplizierte Titel:")
    for entry in inputList:
        if entry["title"] not in titleList:
            titleList.append(entry["title"])
            deduplicatedList.append(entry)
            if verbose:
                print(entry["title"])
    return deduplicatedList

def get_tmdb_rating(movie, api_key, verbose = False):
    """
    Fragt das TMDB-Rating für einen bereinigten Titel ab.
    Gibt das Rating, die ID und das Jahr zurück oder None, wenn kein Match gefunden wurde.
    """
    if not movie:
        return None

    # TMDB Search Endpoint
    url = "https://api.themoviedb.org/3/search/movie"
    
    params = {
        "api_key": api_key,
        "query": movie.get("title"),
        "language": "de-DE", # WICHTIG: Sucht gezielt nach deutschen Titeln
        "include_adult": False,
        "region": "DE"       # Optimiert die Suche für den deutschen Markt
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        # Prüfen, ob Ergebnisse gefunden wurden
        results = data.get("results", [])
        if results:
            # Wir nehmen das erste Ergebnis (Top Match)
            best_match = results[0]
            
            # TMDB nutzt 'vote_average' statt 'imdbRating'
            rating = best_match.get("vote_average")
            release_date = best_match.get("release_date", "")
            popularity = best_match.get("popularity")
            matched_title = best_match.get("title")
            orig_title = best_match.get("original_title")
            tmdb_id = best_match.get("id")
            tmdb_url = "https://www.tmdb.org/movie/"+str(tmdb_id)
            
            #Debug Output
            if(verbose):
                print(f"Gesucht nach: {movie.get("title")}\nGefundener Titel: {best_match.get("title")}\nOriginal Titel: {best_match.get("original_title")}\nBewertung: {rating}\nPopularität: {best_match.get("popularity")}")
                print("-------------------------------------------------------------------------")
            else:
                print(f"Berwertung für {movie.get("title")} gefunden.")
            #Add new fields
            movie["popularity"] = popularity
            movie["release_date"] = release_date
            movie["rating"] = rating
            movie["matched_title"] = matched_title
            movie["original_title"] = orig_title
            movie["tmdb_id"] = tmdb_id
            movie["tmdb_url"] = tmdb_url
            
            return movie    
        return None

    except Exception as e:
        print(f"Fehler bei TMDB Abfrage für '{movie["title"]}': {e}")
        return None
        
def process_movies(movie_list, api_key, verbose = False):
    
    results_with_rating = []
    print("Durchsuche TMDB...")
    for movie in movie_list: 
        # 2. Rating abfragen
        rating_data = get_tmdb_rating(movie, api_key, verbose)
    
        if rating_data:
            results_with_rating.append(movie)
            # print(f"Bewertung für \"{movie["title"]}\" gefunden!")
                        
    # 4. Nach Rating sortieren (höchstes zuerst)
    results_with_rating.sort(key=lambda x: x['rating'], reverse=True)
    
    return results_with_rating

def cullMovies(movie_list, min_rating = 7.5, min_popularity = 5.0, verbose=False):
    culledMovies = []
    for movie in movie_list:
        if movie.get("rating") >= min_rating and movie.get("popularity") >= min_popularity:
            culledMovies.append(movie)
            if verbose:
                print(f"{movie.get("title")} aufgenommen. (Bewertung: {movie.get("rating"):.1f}/{min_rating} Popularität: {movie.get("popularity"):.1f}/{min_popularity})")
        else:
            if verbose:
                print(f"{movie.get("title")} aussortiert. (Bewertung: {movie.get("rating"):.1f}/{min_rating} Popularität: {movie.get("popularity"):.1f}/{min_popularity})")
    print(f"{len(movie_list)-len(culledMovies)} von {len(movie_list)} Filme aussortiert.")
    return culledMovies



def writeLinkList(movieList, filename="videoURLlist.txt"):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            count = 0
            for movie in movieList:
                # Wir prüfen zuerst auf HD, falls nicht vorhanden, nehmen wir die normale URL
                url = movie.get("url_video_hd") or movie.get("url_video")

                if url:
                    f.write(f"{url}\n")
                    count += 1

        print(f"Erfolg: {count} URLs wurden in '{filename}' gespeichert.")
    
    except IOError as e:
        print(f"Fehler beim Schreiben der Datei: {e}")

def checkJellyfin(movieList, server_url, api_key,user_id, verbose = False):
    url = f"{server_url}/Users/{user_id}/Items"
    notInJellyList =  []
    params = {
        "api_key": api_key,
        "Recursive": "true",
        "IncludeItemTypes": "Movie",
        "Fields": "ProviderIds"  # WICHTIG: Wir fordern explizit die externen IDs an
    }

    try:
        print("\nLade Jellyfin-Bibliothek...")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        items = data.get("Items", [])
        
        existing_ids = set()
        
        for item in items:
            # Zugriff auf das ProviderIds Dictionary (z.B. {"Tmdb": "12345", "Imdb": "..."})
            provider_ids = item.get("ProviderIds", {})
            tmdb_id = provider_ids.get("Tmdb")
            
            if tmdb_id:
                # TMDB IDs sind oft Strings in der API, wir speichern sie als Int oder String, 
                # je nachdem wie wir sie später vergleichen. Hier als String zur Sicherheit.
                existing_ids.add(str(tmdb_id))
                
        print(f"{len(existing_ids)} Filme mit TMDB-ID in Jellyfin gefunden.")

    except Exception as e:
        print(f"Fehler beim Laden der Jellyfin-Bibliothek: {e}")

    for movie in movieList:
        tmdb_id_str = movie.get("tmdb_id")
        if str(tmdb_id_str) in existing_ids:
            print(f"--- [BEREITS VORHANDEN] {movie['title']}\n\
          TMDB-ID: {movie.get("tmdb_id")}\n")
       
        else:
            print(f"+++ [NEU] {movie['title']}\n\
          TMDB-ID: {movie.get("tmdb_id")}\n")
            notInJellyList.append(movie)
    return notInJellyList  
   
# --- ANWENDUNG ---

if __name__ == "__main__":
    #Variables
    cleanedTitles = []
    #Parse CLI arguments
    args = parser.parse_args()
    print(args.verbose)
    print(args.size)
    print(args.channel)


    search_config_default = {
    "channel": "ard",
    "topic": "Film",
    "duration_min": 90,
    "duration_max": 250,
    "size": 100,
    "blacklist": ["Hörfassung", "Audiodeskription", "Gebärdensprache", "OmdU", "Teaser", "Trailer", "Ein Gespräch", "Interview mit", "Originalversion"]
}
    search_config = search_config_default
    #check channel arg
    search_config["channel"] = args.channel.lower()

    #check topic arg
    if args.topic:
        search_config["topic"] = args.topic.lower()
    else:
        print("Kein gültiges Thema übergeben. Verwende Standard \"Film\"")

    # check size arg
    if(args.size):
        search_config["size"] = args.size

    #check min rating arg
    if(args.min_rating):
        min_rating = float(args.min_rating)
    else:
        min_rating = 7.5

      #check min popularity arg
    if(args.min_popularity):
        min_popularity = float(args.min_popularity)
    else:
        min_popularity = 3.0


    #Title Blacklist
    blacklist = ["Hörfassung", "Audiodeskription", "Gebärdensprache", "OmdU", "Teaser", "Trailer", "Ein Gespräch", "Interview mit", "Originalversion"]

    movies = mediathekWeb.fetch_mediathek_results(search_config, args.verbose)
    for t in movies:
        cleanTitle = util.cleanTitle(t, verbose=args.verbose)
        cleanedTitles.append(cleanTitle)
    deduplicatedList = deduplicate_list(cleanedTitles, verbose=args.verbose)
    moviesRated = process_movies(deduplicate_list(deduplicatedList), TMDB_API_KEY, verbose = args.verbose)
    moviesCulled = cullMovies(moviesRated, min_rating=min_rating, min_popularity=min_popularity, verbose=args.verbose)
    newToJelly = checkJellyfin(moviesCulled, "https://jellyfin.lsarebhan.de", JELLYFIN_API_KEY, JELLYFIN_USER_ID, verbose=True)
    
    userList = []
    for movie in newToJelly:
        if(util.userConfirm(movie)):
            userList.append(movie)
    writeLinkList(userList)