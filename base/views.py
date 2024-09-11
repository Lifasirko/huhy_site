from django.shortcuts import render
from django.http import JsonResponse
import datetime as dt
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.core.cache import cache
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.exceptions import GoogleAuthError

API_KEY = 'AIzaSyDX8Ul5yN4vCOkiwmCOCEiBaN4jpJyoH9Q'
CALENDAR_ID = '63f17c703a73e613e05b4fbd8b9c0b65a1920fbbbaad28997182aab4dfae1d1b@group.calendar.google.com'

def home(request):
    return render(request, 'home.html')

def get_events(year, month):
    cache_key = f'events_{year}_{month}'
    events = cache.get(cache_key)
    
    if events is None:
        start_date = timezone.make_aware(dt.datetime(year, month, 1))
        end_date = start_date + relativedelta(months=1)
        
        try:
            service = build('calendar', 'v3', developerKey=API_KEY)
            events_result = service.events().list(
                calendarId=CALENDAR_ID,
                timeMin=start_date.isoformat(),
                timeMax=end_date.isoformat(),
                maxResults=1000,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = []
            for event in events_result.get('items', []):
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                events.append({
                    'start': start,
                    'end': end,
                    'summary': event['summary'],
                    'description': event.get('description', '')
                })
            
            cache.set(cache_key, events, timeout=60*60)  # Кешуємо на 1 годину
        except GoogleAuthError:
            events = []
            print("Помилка аутентифікації Google API")
        except Exception as e:
            events = []
            print(f"Виникла помилка при отриманні подій: {e}")
    
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
