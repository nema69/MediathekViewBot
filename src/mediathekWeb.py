import requests
import util

def fetch_mediathek_results(params, verbose = False):
    url = "https://mediathekviewweb.de/api/query"

    ##get search parameters
    channel = params.get("channel", "ard")
    topic = params.get("topic", "Filme")
    min_duration = params.get("duration_min"*60, 90*60)
    max_duration =  params.get("duration_max"*60, 250*60)
    size = params.get("size", 100)

    #Verbose Output
    if verbose:
         print(f"Suche läuft... \n")
         print(f"Suchparameter:\n\
                Kanal: {channel}\n\
                Thema: {topic}\n\
                Minimale Dauer: {min_duration/60} Minuten\n\
                Maximale Dauer: {max_duration/60} Minuten\n\
                Anzahl Anfragen: {size}\n")
    else:
        print("Durchsuche Mediathek...")
    
    # 1. API-Abfrage zusammenbauen
    api_queries = []
    if params.get("channel"):
        api_queries.append({"fields": ["channel"], "query": channel})
    if params.get("topic"):
        api_queries.append({"fields": ["topic"], "query": topic})

    query_payload = {
        "queries": api_queries,
        "sortBy": "timestamp",
        "sortOrder": "desc",
        "future": False,
        "size": params.get("size", 100), # Größere Menge abfragen, da wir danach filtern
        "duration_min": min_duration,
        "duration_max": max_duration
    }

    try:
        response = requests.post(url, json=query_payload)
        response.raise_for_status()
        results = response.json().get("result", {}).get("results", [])
        
        # 2. Blacklist-Filterung
        blacklist = params.get("blacklist", [])
        filtered_results = []

        for entry in results:
            title = entry.get("title", "")
            # Prüfen, ob irgendein Wort der Blacklist im Titel vorkommt (Case-Insensitive)
            if not any(bad_word.lower() in title.lower() for bad_word in blacklist):
                filtered_results.append(entry)
            if verbose:
                util.printMovie(entry)
        
        print(f"{len(results)} potentielle Filme gefunden.\n")
        return filtered_results

    except Exception as e:
        print(f"Fehler: {e}")
        return []