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

GOOGLE_CALENDAR_API_KEY = settings.GOOGLE_CALENDAR_API_KEY
CALENDAR_ID = settings.CALENDAR_ID


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
    service = build('calendar', 'v3', developerKey=GOOGLE_CALENDAR_API_KEY)
    try:
        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            singleEvents=True,
            orderBy='startTime',
            timeMin=now
        ).execute()

        events = events_result.get('items', [])

        events_data = []
        for event in events:
            start = event.get('start', {}).get('dateTime', event.get('start', {}).get('date'))
            end = event.get('end', {}).get('dateTime', event.get('end', {}).get('date'))

            # Перевіряємо локальне зображення за ключовими словами
            image_url = get_event_image_url(event.get('summary', ''))

            # Якщо немає локального зображення, перевіряємо вкладення
            if image_url == '/static/images/calendar_pics/default_image.jpg':
                if 'attachments' in event:
                    image_url = event['attachments'][0].get('fileUrl', '/static/images/calendar_pics/slay.png')
                else:
                    image_url = '/static/images/calendar_pics/slay.png'

            events_data.append({
                'summary': event.get('summary', 'No Title'),
                'start': start,
                'end': end,
                'description': event.get('description', ''),
                'image_url': image_url,
            })

        return events_data
    except GoogleAuthError:
        print("Google API authentication error")
        return []
    except Exception as e:
        print(f"Error fetching events: {e}")
        return []


def get_event_image_url(summary):
    images = {
        'D&D': '/static/images/dd.png',
        'Vampire': '/static/images/vampire.jpg',
        'Coriolis': '/static/images/coriolis_edit.jpg',
        'Vessen': '/static/images/vessen.jpg',
        'Warhammer': '/static/images/warhammer.jpg'
    }

    for key, image_url in images.items():
        if key.lower() in summary.lower():
            return image_url

    return '/static/images/calendar_pics/slay.png'  # Стандартне зображення, якщо немає збігів


def events_api(request):
    page = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 3))

    all_events = get_events()

    start = (page - 1) * limit
    end = start + limit
    paginated_events = all_events[start:end]

    events_data = []
    for event in paginated_events:
        # Перевірка на тип даних перед використанням `.get()`
        if isinstance(event.get('start'), dict):
            start_time = event['start'].get('dateTime', event['start'].get('date'))
        else:
            start_time = event['start']  # Встановлення значення як є, якщо це не словник

        if isinstance(event.get('end'), dict):
            end_time = event['end'].get('dateTime', event['end'].get('date'))
        else:
            end_time = event['end']  # Встановлення значення як є, якщо це не словник

        events_data.append({
            'summary': event.get('summary', 'No Title'),
            'start': start_time,
            'end': end_time,
            'description': event.get('description', ''),
            'image_url': event.get('image_url', '')  # або надаємо стандартне зображення за замовчуванням
        })

    return JsonResponse({
        'events': events_data,
        'has_more': end < len(all_events)
    })  # TODO: пофіксити ширину кнопки запису на гру на телефонах
