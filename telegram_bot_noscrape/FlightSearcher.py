import requests
import time
import logging

logger = logging.getLogger(__name__)

class FlightSearcher:
    def __init__(self):
        # L'URL di base richiede {origin} e {destination}
        self.base_url = "https://www.ryanair.com/api/farfnd/3/oneWayFares/{}/{}/cheapestPerDay"
        
        # Header essenziali per simulare un browser ed evitare blocchi
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
        }

    def close(self):
        # Mantenuto per retrocompatibilità con main.py (non fa più nulla)
        pass

    def __get_unique_months(self, dates):
        """Estrae i mesi univoci dall'array di date e li formatta in YYYY-MM-01"""
        months = set()
        for date in dates:
            # Prende '2026-07' da '2026-07-29' e aggiunge '-01'
            month_prefix = date[:7]
            months.add(f"{month_prefix}-01")
        return list(months)

    def __execute_search(self, origin, destination, dates):
        valid_flights = {}
        target_months = self.__get_unique_months(dates)

        for month_date in target_months:
            url = self.base_url.format(origin, destination)
            params = {"outboundMonthOfDate": month_date}

            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=15)
                response.raise_for_status()
                data = response.json()

                fares = data.get("outbound", {}).get("fares", [])
                
                # Iteriamo il JSON per trovare le date che ci interessano
                for fare in fares:
                    day = fare.get("day")
                    
                    # Filtro: il giorno è tra quelli richiesti e il volo è disponibile
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
        """
        Effettua la ricerca gestendo eventuali fallimenti di rete.
        """
        for attempt in range(max_retries):
            flight_data = self.__execute_search(origin, destination, dates)
            if flight_data:
                return flight_data
            
            logger.info(f"Nessun dato trovato per {origin}-{destination} o chiamata fallita (Tentativo {attempt + 1}). Riprovo in 5s...")
            time.sleep(5)
            
        logger.warning(f'Tutti i tentativi falliti per {origin}-{destination}.')
        return {}