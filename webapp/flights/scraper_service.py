"""
Scraper service — runs FlightSearcher in a background thread and
broadcasts log lines to connected SSE clients.
"""
import sys
import threading
import collections
import time
from pathlib import Path
import os

# Make telegram_bot importable
SCRAPER_PATH = Path(__file__).resolve().parent.parent.parent / 'telegram_bot'
sys.path.insert(0, str(SCRAPER_PATH))

# ------- shared state -------
_log_deque: collections.deque = collections.deque(maxlen=200)
_log_lock  = threading.Lock()
_sse_events: list = []           # one threading.Event per connected SSE client
_sse_lock   = threading.Lock()
_scraper_thread: threading.Thread | None = None
_scraper_running = threading.Event()
_use_vpn: bool = False           # off by default


def _push_log(msg: str) -> None:
    """Append a log line and wake up all SSE clients."""
    with _log_lock:
        _log_deque.append(msg)
    with _sse_lock:
        for ev in _sse_events:
            ev.set()


def get_log_snapshot() -> list[str]:
    with _log_lock:
        return list(_log_deque)


def clear_logs() -> None:
    with _log_lock:
        _log_deque.clear()


def get_vpn() -> bool:
    return _use_vpn


def set_vpn(enabled: bool) -> None:
    global _use_vpn
    _use_vpn = enabled


def register_sse_client() -> threading.Event:
    ev = threading.Event()
    with _sse_lock:
        _sse_events.append(ev)
    return ev


def unregister_sse_client(ev: threading.Event) -> None:
    with _sse_lock:
        try:
            _sse_events.remove(ev)
        except ValueError:
            pass


# ------- scraper logic -------

def _run_scrape(route_pks: list[int] | None = None) -> None:
    """
    Run a scrape cycle. If route_pks is given, only scrape those routes.
    This function is meant to be called from a thread.
    """
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webapp.settings')
    django.setup()

    from flights.models import Route, PriceRecord
    from FlightSearcher import FlightSearcher

    clear_logs()
    _push_log(f"🚀 Scraper started {'(VPN ON)' if _use_vpn else '(VPN OFF)'}")

    try:
        searcher = FlightSearcher(vpn=_use_vpn)

        if route_pks:
            routes = Route.objects.filter(pk__in=route_pks, is_active=True)
        else:
            routes = Route.objects.filter(is_active=True)

        if not routes.exists():
            _push_log("⚠️  No active routes to scrape.")
            return

        for route in routes:
            date_str = route.date.strftime('%Y-%m-%d')
            _push_log(f"🔍 Searching {route.origin} → {route.destination} ({date_str})...")

            results = searcher.search_flights_with_retry(
                route.origin, route.destination, [date_str], max_retries=3
            )

            if results:
                for key, data in results.items():
                    if data and data.get('amount'):
                        record = PriceRecord.objects.create(
                            route=route,
                            amount=data['amount'],
                            currency=data.get('currency', '?'),
                        )
                        _push_log(f"✅ Saved: {route} → {record.currency} {record.amount}")
            else:
                _push_log(f"❌ No flights found for {route}")

    except Exception as e:
        _push_log(f"💥 Scraper error: {e}")
    finally:
        _push_log("✔️  Scrape completed.")
        _scraper_running.clear()


def trigger_scrape(route_pks: list[int] | None = None) -> bool:
    """
    Fire a one-shot scrape in a daemon thread.
    Returns False if a scrape is already in progress.
    """
    global _scraper_thread
    if _scraper_running.is_set():
        _push_log("⏳ Scrape already in progress, request ignored.")
        return False

    # Set the flag early to prevent race conditions before thread wakes up
    _scraper_running.set()

    _scraper_thread = threading.Thread(
        target=_run_scrape,
        args=(route_pks,),
        daemon=True,
    )
    _scraper_thread.start()
    return True


def is_running() -> bool:
    return _scraper_running.is_set()
