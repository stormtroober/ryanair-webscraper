from datetime import datetime
import json
from pymongo import MongoClient

class FlightSaver:
    def __init__(self, db_name='flights_db', collection_name='flights'):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def save(self, flights_dict):
        if not flights_dict:
            return
        for key, value in flights_dict.items():
            flight_doc = {
                "route": key.split(' on ')[0],
                "date": value['date'],
                "price": f"{value['amount']}{value['currency']}",
                "saved_at": datetime.today().strftime("%Y-%m-%d %H:%M")
            }
            self.collection.insert_one(flight_doc)


    def get_summary(self):
        summary = {}
        cursor = self.collection.find()
        for doc in cursor:
            route = doc['route']
            date = doc['date']
            price = doc['price']
            if route not in summary:
                summary[route] = {'dates': set(), 'prices': [], 'date_counts': {}}
            summary[route]['dates'].add(date)
            summary[route]['prices'].append(price)
            summary[route]['date_counts'][date] = summary[route]['date_counts'].get(date, 0) + 1
        # Format summary for display
        result = []
        for route, info in summary.items():
            date_info = ", ".join(
                f"{d} ({info['date_counts'][d]} voli)" for d in sorted(info['dates'])
            )
            result.append(
                f"Rotta: {route}\n"
                f"Date monitorate: {date_info}\n"
                f"Prezzi salvati: {', '.join(info['prices'])}\n"
            )
        return "\n".join(result) if result else "Nessun volo salvato nel database."   
    
    def export_json(self, filename="flights_export.json"):
        cursor = self.collection.find()
        flights = [doc for doc in cursor]
        # Rimuovi l'_id di MongoDB per evitare problemi di serializzazione
        for flight in flights:
            flight.pop('_id', None)
        with open(filename, "w") as f:
            json.dump(flights, f, indent=2, ensure_ascii=False)
        return filename