import os

from django.conf import settings
from django.contrib import admin
from django.core.management import call_command
from django.http import HttpResponse
from django.urls import path

from .models import Banner, RPG, AboutUs, Event, ContactFormSubmission, Footer, Form, CustomUser, Postcard


class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email')


@admin.register(Postcard)
class PostcardAdmin(admin.ModelAdmin):
    list_display = ("title", "name", 'qr_code_link')
    search_fields = ("title",)
    readonly_fields = ('qr_code_link',)  # Робимо поле тільки для читання

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:postcard_id>/download_qr/', self.admin_site.admin_view(self.download_qr_code),
                 name='postcard_qr_code_download'),
        ]
        return custom_urls + urls

    def download_qr_code(self, request, postcard_id):
        postcard = self.get_object(request, postcard_id)
        svg_data = postcard.generate_qr_code_svg()

        response = HttpResponse(svg_data, content_type="image/svg+xml")
        response['Content-Disposition'] = f'attachment; filename="postcard_{postcard_id}_qr.svg"'
        return response


class ExportDBAdmin(admin.ModelAdmin):
    change_list_template = "admin/export_db.html"

    def export_db(self, request):
        # Створення резервної копії
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)

        file_path = os.path.join(backup_dir, 'backup.json')
        with open(file_path, 'w', encoding='utf-8') as backup_file:
            call_command('dumpdata', indent=2, stdout=backup_file)

        # Завантаження файлу
        with open(file_path, 'rb') as file:
            response = HttpResponse(file, content_type='application/json')
            response['Content-Disposition'] = f'attachment; filename="backup.json"'
            return response


@admin.register(Banner, RPG, AboutUs, Event, ContactFormSubmission, Footer, Form)
class GeneralAdmin(ExportDBAdmin):
    pass


admin.site.register(CustomUser, CustomUserAdmin)
# admin.site.register(Form)
# admin.site.register(Banner)
# admin.site.register(RPG)
# admin.site.register(AboutUs)
# admin.site.register(Event)
# admin.site.register(ContactFormSubmission)
# admin.site.register(Footer)
