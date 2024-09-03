import requests
from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import render, redirect

from base.forms import ContactForm
from base.models import CustomUser


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
