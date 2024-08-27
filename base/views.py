from aiogram import types
from asgiref.sync import sync_to_async
from django.core.mail import send_mail
from django.shortcuts import render, redirect


from base.forms import ContactForm
from telegram_bot.loader import dp, bot
from telegram_bot.utils.notify_admins import new_order_notify, new_order_notify_sync


async def home(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = await sync_to_async(form.save)()
            print("Форма успішно збережена в базу даних.")
            new_order_notify_sync(bot, form=form)
            # await new_order_notify(bot, form=form)
            print("Повідомлення відправлено в Telegram.")
            # send_email(contact)
            # print("Повідомлення відправлено на пошту.")
            return await sync_to_async(redirect)('home')
        else:
            print("Форма не пройшла валідацію.")
    else:
        form = ContactForm()

    return await sync_to_async(render)(request, 'home.html', {'form': form})


def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save()
            print("Форма успішно збережена в базу даних.")
            # await new_order_notify(dp, form=form)
            print("Повідомлення відправлено в Telegram.")
            send_email(contact)
            print("Повідомлення відправлено на пошту.")
            return redirect('success')
        else:
            print("Форма не пройшла валідацію.")
    else:
        form = ContactForm()

    return render(request, 'contact.html', {'form': form})


def send_email(contact):
    subject = 'Нова форма з сайту'
    message = f"Назва форми: {contact.form_name}\nІм'я: {contact.name}\nТелефон: {contact.phone}\nПошта: {contact.email}"
    email_from = 'your_email@gmail.com'
    recipient_list = ['recipient_email@gmail.com']
    send_mail(subject, message, email_from, recipient_list)
