import requests
from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.utils import timezone
from django.core.cache import cache

import datetime as dt
from datetime import datetime, timezone

from googleapiclient.discovery import build
from google.auth.exceptions import GoogleAuthError

from base.forms import ContactForm
from base.models import CustomUser


API_KEY = 'AIzaSyDX8Ul5yN4vCOkiwmCOCEiBaN4jpJyoH9Q'
CALENDAR_ID = '63f17c703a73e613e05b4fbd8b9c0b65a1920fbbbaad28997182aab4dfae1d1b@group.calendar.google.com'

def home(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            print("Форма успішно збережена в базу даних.")
            message = str(form.as_text())
            send_telegram_message(message)
            print("Повідомлення відправлено в Telegram.")
            return redirect('home')
        else:
            print("Форма не пройшла валідацію.")
    else:
        form = ContactForm()

    return render(request, 'home.html', {'form': form})


def send_telegram_message(message: str):
    bot_token = settings.TGBOT_TOKEN
    admin_ids = CustomUser.get_admin_ids()
    # admin_ids = settings.TELEGRAM_ADMIN_IDS
    for admin_id in admin_ids:
        try:
            # Переконайтеся, що admin_id є цілим числом
            admin_id = int(admin_id)
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {"chat_id": admin_id, "text": message}
            response = requests.post(url, data=data)
            response.raise_for_status()  # Перевірка на помилки HTTP
        except ValueError:
            print(f"Невірний ID адміністратора: {admin_id}")
        except requests.exceptions.RequestException as e:
            print(f"Error sending message to admin {admin_id}: {e}")


def send_email(contact):
    subject = 'Нова форма з сайту'
    message = (f"Назва форми: {contact.form_name}\n"
               f"Ім'я: {contact.name}\n"
               f"Телефон: {contact.phone}\n"
               f"Пошта: {contact.email}")
    email_from = 'your_email@gmail.com'
    recipient_list = ['recipient_email@gmail.com']
    send_mail(subject, message, email_from, recipient_list)
    return render(request, 'home.html')


def get_events():
    now = datetime.now(timezone.utc).isoformat()

    try:
        service = build('calendar', 'v3', developerKey=API_KEY)
        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            singleEvents=True,
            orderBy='startTime',
            timeMin=now
        ).execute()

        return events_result.get('items', [])
    except GoogleAuthError:
        print("Google API authentication error")
        return []
    except Exception as e:
        print(f"Error fetching events: {e}")
        return []


def events_api(request):
    page = int(request.GET.get('page'))
    limit = int(request.GET.get('limit'))

    all_events = get_events()

    start = (page - 1) * limit
    end = start + limit
    paginated_events = all_events[start:end]

    events_data = []
    for event in paginated_events:
        start_time = event['start'].get('dateTime', event['start'].get('date'))
        end_time = event['end'].get('dateTime', event['end'].get('date'))
        events_data.append({
            'summary': event['summary'],
            'start': start_time,
            'end': end_time,
            'description': event.get('description', ''),
        })

    return JsonResponse({
        'events': events_data,
        'has_more': end < len(all_events)
    })