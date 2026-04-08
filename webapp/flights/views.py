import json
import time
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, StreamingHttpResponse
from .models import Route, PriceRecord
from . import scraper_service


def dashboard(request):
    from .utils import get_airport_list
    routes = Route.objects.prefetch_related('price_records').all()
    route_data = []
    for route in routes:
        records = route.price_records.order_by('scraped_at')
        latest = records.last()
        lowest = records.order_by('amount').first()
        route_data.append({
            'route': route,
            'latest': latest,
            'lowest': lowest,
            'record_count': records.count(),
        })
    return render(request, 'flights/dashboard.html', {
        'route_data': route_data,
        'scraper_running': scraper_service.is_running(),
        'airports': get_airport_list(),
        'airports_json': json.dumps(get_airport_list()),
    })


def route_detail(request, pk):
    route = get_object_or_404(Route, pk=pk)
    records = route.price_records.order_by('scraped_at')
    labels = [r.scraped_at.strftime('%d/%m %H:%M') for r in records]
    prices = [float(r.amount) for r in records]
    return render(request, 'flights/route_detail.html', {
        'route': route,
        'records': records,
        'chart_labels': json.dumps(labels),
        'chart_prices': json.dumps(prices),
        'scraper_running': scraper_service.is_running(),
    })


def route_toggle(request, pk):
    route = get_object_or_404(Route, pk=pk)
    route.is_active = not route.is_active
    route.save()
    return redirect('dashboard')


def route_add(request):
    if request.method == 'POST':
        origin = request.POST.get('origin', '').upper().strip()
        destination = request.POST.get('destination', '').upper().strip()
        date = request.POST.get('date', '').strip()

        # If user submitted a city name instead of IATA, try to match it
        if len(origin) > 3 or len(destination) > 3:
            from .utils import get_airport_list
            import unicodedata
            airports = get_airport_list()
            
            def resolve_iata(val):
                if len(val) == 3: return val
                val_clean = unicodedata.normalize('NFD', val).encode('ascii', 'ignore').decode('utf-8').lower()
                for apt in airports:
                    if val_clean in apt['search_text']:
                        return apt['iata']
                return val[:3] # fallback

            origin = resolve_iata(origin)
            destination = resolve_iata(destination)

        if origin and destination and date:
            route, created = Route.objects.get_or_create(
                origin=origin,
                destination=destination,
                date=date,
                defaults={'is_active': True}
            )
            # Immediately trigger a scrape for this route
            scraper_service.trigger_scrape(route_pks=[route.pk])

    return redirect('dashboard')


def route_delete(request, pk):
    route = get_object_or_404(Route, pk=pk)
    route.delete()
    return redirect('dashboard')


def scrape_now(request):
    """Manually trigger a full scrape of all active routes."""
    if request.method == 'POST':
        started = scraper_service.trigger_scrape()
        return JsonResponse({'started': started})
    return JsonResponse({'error': 'POST required'}, status=405)


def vpn_toggle(request):
    """Toggle the VPN flag for the scraper."""
    if request.method == 'POST':
        current = scraper_service.get_vpn()
        scraper_service.set_vpn(not current)
        return JsonResponse({'vpn': scraper_service.get_vpn()})
    return JsonResponse({'vpn': scraper_service.get_vpn()})


def api_status(request):
    """Return current scraper status and VPN flag."""
    return JsonResponse({
        'running': scraper_service.is_running(),
        'vpn': scraper_service.get_vpn(),
    })


def api_prices(request, pk):
    route = get_object_or_404(Route, pk=pk)
    records = route.price_records.order_by('scraped_at')
    data = {
        'labels': [r.scraped_at.strftime('%d/%m %H:%M') for r in records],
        'prices': [float(r.amount) for r in records],
        'currency': records.first().currency if records.exists() else '?',
    }
    return JsonResponse(data)


def log_stream(request):
    """
    Server-Sent Events endpoint.
    Only streams log lines produced AFTER the client connects.
    """
    def event_generator():
        ev = scraper_service.register_sse_client()
        # Start from the end of the current log — don't replay history
        last_sent = len(scraper_service.get_log_snapshot())
        try:
            while True:
                ev.wait(timeout=25)
                ev.clear()
                current = scraper_service.get_log_snapshot()
                for line in current[last_sent:]:
                    yield f"data: {line}\n\n"
                last_sent = len(current)
                yield ": heartbeat\n\n"
        except GeneratorExit:
            pass
        finally:
            scraper_service.unregister_sse_client(ev)

    response = StreamingHttpResponse(event_generator(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response
