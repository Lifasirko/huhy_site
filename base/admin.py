import csv
import io

from django.contrib import admin, messages
from django.http import HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.shortcuts import render
from .models import Banner, RPG, AboutUs, Event, ContactFormSubmission, Footer, Form, CustomUser, Postcard


class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'phone')


@admin.register(Postcard)
class PostcardAdmin(admin.ModelAdmin):
    list_display = ("title", "name", 'qr_code_link',)
    search_fields = ("title", "name")
    readonly_fields = ('qr_code_link',)  # Робимо поле тільки для читання
    actions = ["export_postcards",]
    change_list_template = "admin/postcard_change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:postcard_id>/download_qr/', self.admin_site.admin_view(self.download_qr_code),
                 name='postcard_qr_code_download'),

            path('import/', self.admin_site.admin_view(self.import_postcards), name='postcard_import'),
        ]
        return custom_urls + urls

    def download_qr_code(self, request, postcard_id):
        postcard = self.get_object(request, postcard_id)
        svg_data = postcard.generate_qr_code_svg()

        response = HttpResponse(svg_data, content_type="image/svg+xml")
        response['Content-Disposition'] = f'attachment; filename="postcard_{postcard_id}_qr.svg"'
        return response

    # Експорт у CSV
    def export_postcards(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="postcards.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Title', 'Name', 'Content'])
        for postcard in queryset:
            writer.writerow([postcard.id, postcard.title, postcard.name, postcard.content])
        return response

    export_postcards.short_description = "Експортувати вибрані листівки в CSV"

    def import_postcards(self, request):
        """
        Імпортувати записи з CSV.
        """
        if request.method == "POST":
            csv_file = request.FILES.get("file")
            if not csv_file.name.endswith(".csv"):
                self.message_user(request, "Файл має бути у форматі CSV", level=messages.ERROR)
                return TemplateResponse(request, "admin/import_form.html", {})

            decoded_file = csv_file.read().decode("utf-8")
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)

            required_fields = ["Title", "Name", "Content"]
            for field in required_fields:
                if field not in reader.fieldnames:
                    self.message_user(
                        request, f"Відсутнє поле {field} у CSV-файлі", level=messages.ERROR
                    )
                    return TemplateResponse(request, "admin/import_form.html", {})

            imported_postcards = []
            for row in reader:
                try:
                    postcard = Postcard.objects.create(
                        title=row["Title"],
                        name=row["Name"],
                        content=row["Content"],
                    )
                    imported_postcards.append(postcard.id)
                except Exception as e:
                    self.message_user(
                        request, f"Помилка в рядку: {row}. {str(e)}", level=messages.ERROR
                    )
                    continue

            if imported_postcards:
                self.message_user(request, "Дані успішно імпортовані", level=messages.SUCCESS)
                # Редірект на список деталей першої імпортованої картки
                return HttpResponseRedirect(reverse('admin:base_postcard_changelist'))

        return TemplateResponse(request, "admin/import_form.html", {})


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Form)
admin.site.register(Banner)
admin.site.register(RPG)
admin.site.register(AboutUs)
admin.site.register(Event)
admin.site.register(ContactFormSubmission)
admin.site.register(Footer)
