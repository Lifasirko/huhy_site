from aiogram import types
from django.core.mail import send_mail
from django.shortcuts import render, redirect

from base.forms import ContactForm
from telegram_bot.loader import dp
from telegram_bot.utils.notify_admins import new_order_notify


def home(request):
    return render(request, 'home.html')


async def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Зберігаємо дані в базу даних
            contact = form.save()

            # Відправка повідомлення в Telegram
            message = types.Message()
            await new_order_notify(dp, message, form = form)

            # Відправка на електронну пошту
            send_email(contact)

            # Перенаправлення на сторінку успіху або відображення повідомлення
            return redirect('success')
    else:
        form = ContactForm()

    return render(request, 'contact.html', {'form': form})


def send_email(contact):
    subject = 'Нова форма з сайту'
    message = f"Назва форми: {contact.form_name}\nІм'я: {contact.name}\nТелефон: {contact.phone}\nПошта: {contact.email}"
    email_from = 'your_email@gmail.com'
    recipient_list = ['recipient_email@gmail.com']
    send_mail(subject, message, email_from, recipient_list)
