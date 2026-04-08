from django.db import models

class Route(models.Model):
    origin = models.CharField(max_length=3)
    destination = models.CharField(max_length=3)
    date = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('origin', 'destination', 'date')

    def __str__(self):
        return f"{self.origin}-{self.destination} on {self.date}"

    @property
    def origin_display(self):
        from flights.utils import get_city_by_iata
        city = get_city_by_iata(self.origin)
        return f"{city} ({self.origin})" if city != self.origin else self.origin

    @property
    def destination_display(self):
        from flights.utils import get_city_by_iata
        city = get_city_by_iata(self.destination)
        return f"{city} ({self.destination})" if city != self.destination else self.destination

class PriceRecord(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='price_records')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3)
    scraped_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-scraped_at']

    def __str__(self):
        return f"{self.route}: {self.amount} {self.currency} at {self.scraped_at}"
