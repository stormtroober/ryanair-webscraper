import sys
import os
from pathlib import Path
from django.core.management.base import BaseCommand
from django_apscheduler.jobstores import DjangoJobStore
from apscheduler.schedulers.blocking import BlockingScheduler

# Add telegram_bot folder to path so FlightSearcher is importable
SCRAPER_PATH = Path(__file__).resolve().parent.parent.parent.parent.parent / 'telegram_bot'
sys.path.insert(0, str(SCRAPER_PATH))


def scrape_active_routes():
    """Fetch prices for all active routes and save to DB."""
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webapp.settings')
    django.setup()

    from flights.models import Route, PriceRecord
    from FlightSearcher import FlightSearcher

    use_vpn = os.getenv("USE_VPN", "False").lower() == "true"
    searcher = FlightSearcher(vpn=use_vpn)

    active_routes = Route.objects.filter(is_active=True)
    if not active_routes.exists():
        print("[scraper] No active routes to scrape.")
        return

    for route in active_routes:
        date_str = route.date.strftime('%Y-%m-%d')
        print(f"[scraper] Searching {route.origin}-{route.destination} on {date_str}...")
        results = searcher.search_flights_with_retry(
            route.origin, route.destination, [date_str], max_retries=3
        )
        for key, data in results.items():
            if data and data.get('amount'):
                record = PriceRecord.objects.create(
                    route=route,
                    amount=data['amount'],
                    currency=data.get('currency', '?'),
                )
                print(f"[scraper] Saved: {record}")

                # Check alert
                if route.target_price and data['amount'] <= float(route.target_price):
                    print(f"[scraper] 🔔 PRICE DROP ALERT: {route} → {data['amount']} {data.get('currency','')}")


class Command(BaseCommand):
    help = 'Start the APScheduler to scrape flight prices on a schedule.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=5400,
            help='Interval in seconds between scrapes (default: 5400 = 90 min)'
        )
        parser.add_argument(
            '--run-now',
            action='store_true',
            help='Run a scrape immediately at startup, then follow the schedule.'
        )

    def handle(self, *args, **options):
        interval = options['interval']
        scheduler = BlockingScheduler(timezone='Europe/Rome')
        scheduler.add_jobstore(DjangoJobStore(), 'default')

        scheduler.add_job(
            scrape_active_routes,
            trigger='interval',
            seconds=interval,
            id='scrape_flights',
            replace_existing=True,
        )

        self.stdout.write(self.style.SUCCESS(
            f'Scraper scheduler started. Interval: {interval}s. Press Ctrl+C to stop.'
        ))

        if options['run_now']:
            self.stdout.write('Running initial scrape now...')
            scrape_active_routes()

        try:
            scheduler.start()
        except KeyboardInterrupt:
            scheduler.shutdown()
            self.stdout.write(self.style.WARNING('Scheduler stopped.'))
