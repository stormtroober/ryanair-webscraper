import requests
import time
import logging
import random # <-- Importazione necessaria per la rotazione

logger = logging.getLogger(__name__)

class FlightSearcher:
    def __init__(self):
        # L'URL di base richiede {origin} e {destination}
        self.base_url = "https://www.ryanair.com/api/farfnd/3/oneWayFares/{}/{}/cheapestPerDay"
        
        # Pool di User-Agent moderni e variati (Windows, Mac, Chrome, Firefox, Safari)
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]

    def _get_random_headers(self):
        """Genera dinamicamente gli headers scegliendo un User-Agent casuale"""
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
            # Opzionale ma consigliato: aggiunge header per sembrare una vera navigazione
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        }

    def close(self):
        pass

    def __get_unique_months(self, dates):
        months = set()
        for date in dates:
            month_prefix = date[:7]
            months.add(f"{month_prefix}-01")
        return list(months)

    def __execute_search(self, origin, destination, dates):
        valid_flights = {}
        target_months = self.__get_unique_months(dates)

        for month_date in target_months:
            url = self.base_url.format(origin, destination)
            params = {"outboundMonthOfDate": month_date}
            
            # Generiamo headers nuovi ad ogni iterazione
            headers = self._get_random_headers()

            try:
                # Passiamo i nuovi headers alla richiesta
                response = requests.get(url, headers=headers, params=params, timeout=15)
                response.raise_for_status()
                data = response.json()

                fares = data.get("outbound", {}).get("fares", [])
                
                for fare in fares:
                    day = fare.get("day")
                    if day in dates and not fare.get("unavailable", True):
                        price_info = fare.get("price", {})
                        if price_info:
                            key = f"{origin}-{destination} on {day}"
                            valid_flights[key] = {
                                'currency': price_info.get("currencySymbol", "€"),
                                'amount': float(price_info.get("value", 0)),
                                'date': day
                            }
                            
            except requests.exceptions.RequestException as e:
                logger.error(f"Errore API per la tratta {origin}-{destination} nel mese {month_date}: {e}")

        return valid_flights

    def search_flights_with_retry(self, origin, destination, dates, max_retries=3):
        for attempt in range(max_retries):
            flight_data = self.__execute_search(origin, destination, dates)
            if flight_data:
                return flight_data
            
            logger.info(f"Nessun dato trovato per {origin}-{destination} o chiamata fallita (Tentativo {attempt + 1}). Riprovo in 5s...")
            # Un'altra buona pratica: jitter sul delay
            # Aspettiamo tra i 4 e i 7 secondi invece di un valore fisso di 5
            time.sleep(random.uniform(4, 7))
            
        logger.warning(f'Tutti i tentativi falliti per {origin}-{destination}.')
        return {}