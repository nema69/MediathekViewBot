import re

class Colors:
    RED    = '\033[31m'
    GREEN  = '\033[32m'
    YELLOW = '\033[33m'
    BLUE   = '\033[34m'
    BOLD   = '\033[1m'
    RESET  = '\033[0m'

def printMovie(movieDict):
    layout = [
            ("Titel",       "title",           ""),
            ("TMDB Titel",  "matched_title",   ""),
            ("Original",    "original_title",  ""), # Falls vorhanden
            ("Jahr",        "year",            ""),
            ("Thema",       "topic",           ""),
            ("Bewertung",   "rating",          "/10 ⭐"),
            ("Beliebtheit", "popularity",      ""),
            ("Dauer",       "duration",        " Sek."),
            ("Sender",      "channel",         ""),
            ("TMDB-ID",     "tmdbID",          ""),
            ("Video",       "url_video_hd",    ""), # Bevorzugt HD
            ("Video (SD)",  "url_video",       "")  # Fallback
        ]

    print("\n" + "═" * 80) # Schicke Trennlinie
        
    # 2. Iteration durch das Layout
    for label, key, suffix in layout:
        value = movieDict.get(key)
        
        # Nur drucken, wenn ein Wert existiert (nicht None und nicht leer)
        if value:
            # Formatierung:
            # {label:<12} -> Reserviert 12 Zeichen Platz für das Label (linksbündig)
            # {value}     -> Der eigentliche Wert
            print(f" {Colors.BOLD}{label:<12}{Colors.RESET} : {value}{suffix}")

    # Beschreibung oft zu lang für eine Zeile, daher separat behandeln
    desc = movieDict.get("description")
    if desc:
        print("-" * 80)
        print(f" {desc[:200]}..." if len(desc) > 200 else f" {desc}")
    
    print("═" * 80 + "\n")

    # def printMovies(movieList):
    # for movie in movieList:
    #     print(f"Mediathek Titel: {movie.get("title")}")
    #     print(f"TMDB Titel:      {movie.get("matched_title")}")
    #     print(f"Original Titel:  {movie.get("original_title")}")
    #     print(f"Bewertung:       {movie.get("rating")}")
    #     print(f"Beliebtheit:     {movie.get("popularity")}")
    #     print(f"Link:            {movie.get("url_video_hd")}")
    #     print("-----------------------------------------------------------")


def cleanTitle(title, cleaning_rules=None, verbose = False):
    """
    Bereinigt einen Filmtitel basierend auf modularen Regeln.
    """
    if cleaning_rules is None:
        # Standard-Regeln, falls nichts übergeben wurde
        cleaning_rules = [
            r"\|.*",                  # Alles nach einem senkrechten Strich (oft Datumsangaben)
            r"\(S\d+ / E\d+\).*",     # Staffel- und Episodeninfos wie (S01 / E02)
            r"\(.*\)",                # Alles in Klammern (Zusatzinfos)
            r"Video verfügbar.*",     # Verfügbarkeitshinweise
            r"AD$|UT$|GS$",           # Kürzel am Ende: Audiodeskription, Untertitel, Gebärdensprache
            r"\d{2}\.\d{2}\.\d{4}",   # Datumsformate (dd.mm.yyyy)
            r"–.*",                   # Alles nach einem Gedankenstrich
            r"[«»\"]"
        ]

    cleaned = title
    
    for pattern in cleaning_rules:
        # Ersetzt das gefundene Muster durch einen leeren String
        cleaned["title"] = re.sub(pattern, "", cleaned["title"], flags=re.IGNORECASE)
        cleaned["title"] = cleaned["title"].strip()
    
    return cleaned

def userConfirm(movie):
    printMovie(movie)
    print("Film herunterladen? (y/N)")
    ans = input()
    
    if ans.lower() == "y":
        return True
    else:
        return False
    
def confirmMovies(movieList):
    confirmedMovies =  []
    for movie in movieList:
        if userConfirm(movie):
            confirmedMovies.append(movie)
    return confirmedMovies