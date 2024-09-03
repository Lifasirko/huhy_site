from django.contrib import admin

from .models import Banner, RPG, AboutUs, Event, ContactFormSubmission, Footer, Form, CustomUser


class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email')


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Form)
admin.site.register(Banner)
admin.site.register(RPG)
admin.site.register(AboutUs)
admin.site.register(Event)
admin.site.register(ContactFormSubmission)
admin.site.register(Footer)
