import re
from datetime import datetime, timezone, timedelta

import requests
from django.conf import settings
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from google.auth.exceptions import GoogleAuthError
from googleapiclient.discovery import build

from base.forms import ContactForm
from base.models import CustomUser, Postcard
from .models import Event  # Make sure Event is your event model

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
            return redirect('thank_you')  # Перенаправлення на сторінку подяки
        else:
            print("Форма не пройшла валідацію.")
    else:
        form = ContactForm()

    return render(request, 'home.html', {'form': form})


def send_telegram_message(message: str):
    bot_token = settings.TGBOT_TOKEN
    admin_ids = CustomUser.get_admin_ids()
    admin_ids += settings.TELEGRAM_ADMIN_IDS
    for admin_id in admin_ids:
        try:
            # Переконайтеся, що admin_id є цілим числом
            if admin_id is None:
                raise ValueError("TELEGRAM_ADMIN_ID is not set in the environment.")
            admin_id = int(admin_id)

            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {"chat_id": admin_id, "text": message}
            response = requests.post(url, data=data)
            response.raise_for_status()  # Перевірка на помилки HTTP
        except ValueError:
            print(f"Невірний ID адміністратора: {admin_id}")
        except requests.exceptions.RequestException as e:
            print(f"Error sending message to admin {admin_id}: {e}")


def send_email(contact, request):
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
    date_filter = request.GET.get('date')
    master_filter = request.GET.get('master')
    system_filter = request.GET.get('system')

    all_events = get_events()

    # Фільтрація подій за обраними параметрами
    if date_filter:
        all_events = [event for event in all_events if event['start'].startswith(date_filter)]
    if master_filter:
        all_events = [event for event in all_events if master_filter in event.get('summary', '')]
    if system_filter:
        all_events = [
            event for event in all_events
            if system_filter in event.get('summary', '') #or system_filter in event.get('description', '')
        ]

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
    })


def get_unique_filters():
    now = datetime.now(timezone.utc).isoformat()
    thirty_days_later = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

    service = build('calendar', 'v3', developerKey=GOOGLE_CALENDAR_API_KEY)
    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=now,
        timeMax=thirty_days_later,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])

    # Збір унікальних значень
    masters = set()
    systems = set()
    for event in events:
        summary = event.get('summary', '')
        description = event.get('description', '')

        # Парсимо майстра
        master_match = re.search(r"[Мм]айстер\s(.+)", summary)
        if master_match:
            masters.add(master_match.group(1).strip())

        # Парсимо систему/гру в summary
        game_match_summary = re.search(r"^(.+?)(?:\s*[.-]\s*(?:Кімната\s.*\s)?)?[Мм]айстер\s(.+)$", summary)
        if game_match_summary:
            game_name = game_match_summary.group(1).strip()[:21]

            game_name = game_name.replace("Підземелля та Дракони", "Підземелля та дракони")
            game_name = game_name.replace("Підземелля і дракони", "Підземелля та дракони")
            game_name = game_name.rstrip(".")

        else:
            game_name = "Вільна кімната"

        systems.add(game_name)

        # Парсимо систему/гру в description, якщо це можливо
        # game_match_description = re.search(r"[Сс]истема\s*:\s*(.+)", description)
        # if game_match_description:
        #     game_name = game_match_description.group(1).strip()[:21]
        #     systems.add(game_name)

    # Перевірка зібраних значень для діагностики
    print("Masters collected:", masters)  # Для відладки
    print("Systems collected:", systems)  # Для відладки

    return list(masters), list(systems)


def get_filters(request):
    masters, systems = get_unique_filters()
    print("Sending filters response:", {"masters": masters, "systems": systems})  # Для відладки
    return JsonResponse({
        'masters': masters,
        'systems': systems
    })


def thank_you(request):
    return render(request, 'thankyoupage.html')


def postcard_detail(request, postcard_id):
    postcard = get_object_or_404(Postcard, id=postcard_id)
    return render(request, 'postcard_detail.html', {'postcard': postcard})
