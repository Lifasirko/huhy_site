# huhy_site/base/admin.py

import csv
import io

from django.contrib import admin, messages
from django.http import HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import (
    Banner,
    RPG,
    AboutUs,
    Event,
    ContactFormSubmission,
    Footer,
    Form,
    CustomUser,
    Postcard,
)

# -------------------------
# Custom User Admin
# -------------------------
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'phone')

admin.site.register(CustomUser, CustomUserAdmin)

# -------------------------
# Other Models Admin
# -------------------------
# admin.site.register(Form)  # Після імпорту буде замінено
admin.site.register(Banner)
admin.site.register(RPG)
admin.site.register(AboutUs)
admin.site.register(Event)
admin.site.register(ContactFormSubmission)
admin.site.register(Footer)

# -------------------------
# Import-Export Resources
# -------------------------
class PostcardResource(resources.ModelResource):
    class Meta:
        model = Postcard
        fields = (
            'id',
            'title',
            'name',
            'content',
        )
        export_order = (
            'id',
            'title',
            'name',
            'content',
        )
        import_id_fields = ('id',)
        skip_unchanged = True
        report_skipped = True

class FormResource(resources.ModelResource):
    class Meta:
        model = Form
        fields = (
            'id',
            'name',
            'phone',
            'email',
            'form_name',
        )
        export_order = (
            'id',
            'name',
            'phone',
            'email',
            'form_name',
        )
        import_id_fields = ('id',)
        skip_unchanged = True
        report_skipped = True

# -------------------------
# Postcard Admin
# -------------------------
@admin.register(Postcard)
class PostcardAdmin(ImportExportModelAdmin):
    resource_class = PostcardResource
    list_display = ("title", "name", 'qr_code_link',)
    search_fields = ("title", "name")
    readonly_fields = ('qr_code_link',)  # Робимо поле тільки для читання
    change_list_template = "admin/postcard_change_list.html"  # Зберігаємо ваш кастомний шаблон

    # Додаємо кастомні URL-и
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:postcard_id>/download_qr/', self.admin_site.admin_view(self.download_qr_code),
                 name='postcard_qr_code_download'),
            # Не додаємо кастомний import, оскільки django-import-export додає свій власний
        ]
        return custom_urls + urls

    # Кастомний метод для завантаження QR-коду
    def download_qr_code(self, request, postcard_id):
        postcard = self.get_object(request, postcard_id)
        svg_data = postcard.generate_qr_code_svg()

        response = HttpResponse(svg_data, content_type="image/svg+xml")
        response['Content-Disposition'] = f'attachment; filename="postcard_{postcard_id}_qr.svg"'
        return response

    download_qr_code.short_description = "Завантажити QR-код"

    # Відображення кнопки для завантаження QR-коду
    def qr_code_link(self, obj):
        if obj.id:
            url = reverse('admin:postcard_qr_code_download', args=[obj.id])
            return format_html(
                '<a href="{}" download class="button">Скачати QR-код</a>',
                url
            )
        return "QR-код недоступний"

    qr_code_link.short_description = "Завантажити QR-код"

# -------------------------
# Form Admin
# -------------------------
@admin.register(Form)
class FormAdmin(ImportExportModelAdmin):
    resource_class = FormResource
    list_display = ('form_name', 'name', 'email', 'phone')
    search_fields = ('form_name', 'name', 'email', 'phone')
    list_filter = ('form_name',)

    # Якщо ви маєте додаткові поля або налаштування, додайте їх тут

    def get_queryset(self, request):
        """
        Оптимізує запити до бази даних, якщо необхідно.
        """
        return super().get_queryset(request)
