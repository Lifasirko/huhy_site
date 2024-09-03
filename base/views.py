from django.shortcuts import render
from django.http import JsonResponse
import datetime as dt
from dateutil.relativedelta import relativedelta
import requests
from dateutil.parser import parse
from icalendar import Calendar
from django.utils import timezone
from django.core.cache import cache


def home(request):
    return render(request, 'home.html')


def get_events(year, month):
    cache_key = f'events_{year}_{month}'
    events = cache.get(cache_key)

    if events is None:
        start_date = timezone.make_aware(dt.datetime(year, month, 1))
        end_date = start_date + relativedelta(months=1)
        url = "https://calendar.google.com/calendar/ical/09517c8f7fc20960dcd881d87b34fe1f3e94356efa397753534c98a9178d0da2%40group.calendar.google.com/private-47207e1816ce454df55146993785d1f2/basic.ics"

        response = requests.get(url)
        
        if response.status_code == 200:
            gcal = Calendar.from_ical(response.text)
            events = []

            for component in gcal.walk():
                if component.name == "VEVENT":
                    event_start = component.get('DTSTART').dt
                    event_end = component.get('DTEND').dt
                    if event_start.tzinfo is None:
                        event_start = timezone.make_aware(event_start)
                    if event_end.tzinfo is None:
                        event_end = timezone.make_aware(event_end)

                    if start_date <= event_start < end_date:
                        events.append({
                            'start': event_start.isoformat(),
                            'end': event_end.isoformat(),
                            'summary': str(component.get('SUMMARY')),
                            'description': str(component.get('DESCRIPTION', ''))
                        })
            events.sort(key=lambda x: parse(x['start']), reverse=False)
            cache.set(cache_key, events, timeout=60*60)  # Кешуємо на 1 годину
        else:
            events = []

    return events


def get_calendar_events(request):
    now = dt.datetime.now()
    events = get_events(now.year, now.month)
    return render(request, 'base.html', {'events': events})


def get_events_ajax(request):
    year = int(request.GET.get('year'))
    month = int(request.GET.get('month'))
    events = get_events(year, month)
    return JsonResponse({'events': events})
