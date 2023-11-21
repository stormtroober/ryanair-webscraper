
class FlightURLBuilder:
    def __init__(self):
        # Default parameters
        self.base_url = "https://www.ryanair.com/it/it/trip/flights/select"
        self.params = {
            "adults": 1,
            "teens": 0,
            "children": 0,
            "infants": 0,
            "dateOut": "",
            "dateIn": "",
            "isConnectedFlight": "false",
            "discount": 0,
            "isReturn": "false",
            "promoCode": "",
            "originIata": "",
            "destinationIata": "",
            "tpAdults": 1,
            "tpTeens": 0,
            "tpChildren": 0,
            "tpInfants": 0,
            "tpStartDate": "",
            "tpEndDate": "",
            "tpDiscount": 0,
            "tpPromoCode": "",
            "tpOriginIata": "",
            "tpDestinationIata": ""
        }

    def set_origin(self, origin):
        self.params["originIata"] = origin
        self.params["tpOriginIata"] = origin

    def set_destination(self, destination):
        self.params["destinationIata"] = destination
        self.params["tpDestinationIata"] = destination

    def set_date_out(self, date_out):
        self.params["dateOut"] = date_out
        self.params["tpStartDate"] = date_out

    def build_url(self):
        # Construct the query string
        query_string = "&".join([f"{key}={value}" for key, value in self.params.items()])
        return f"{self.base_url}?{query_string}"
