import csv
from pathlib import Path

_airport_data = None
_iata_to_city = None

def load_airports():
    global _airport_data, _iata_to_city
    if _airport_data is not None:
        return _airport_data, _iata_to_city

    # Path to the CSV file
    csv_path = Path(__file__).resolve().parent.parent.parent / 'resources' / 'airports.csv'
    
    airports = []
    iata_mapping = {}

    try:
        if csv_path.exists():
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    iata = row.get('iata_code', '').strip()
                    if iata:
                        city = row.get('municipality', '').strip()
                        name = row.get('name', '').strip()
                        display_name = city if city else name
                        
                        # Remove accents for robust searching
                        import unicodedata
                        city_clean = unicodedata.normalize('NFD', city).encode('ascii', 'ignore').decode('utf-8')
                        name_clean = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8')
                        
                        # Save mapping
                        iata_mapping[iata] = display_name
                        
                        # For the autocomplete
                        airports.append({
                            'iata': iata,
                            'city': city,
                            'name': name,
                            'search_text': f"{city_clean} {name_clean} {iata}".lower()
                        })
    except Exception as e:
        print(f"Error loading airports.csv: {e}")

    # sort alphabetically by city name
    airports.sort(key=lambda x: x['city'])

    _airport_data = airports
    _iata_to_city = iata_mapping
    return _airport_data, _iata_to_city

def get_airport_list():
    airports, _ = load_airports()
    return airports

def get_city_by_iata(iata):
    if not iata:
        return iata
    _, mapping = load_airports()
    city = mapping.get(iata.upper())
    if city:
        return city
    return iata
