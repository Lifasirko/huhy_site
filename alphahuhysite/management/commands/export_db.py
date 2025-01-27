import os
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings

class Command(BaseCommand):
    help = "Експортує базу даних у JSON-файл"

    def handle(self, *args, **kwargs):
        # Директорія для збереження резервних копій
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)

        # Створення файлу резервної копії
        file_path = os.path.join(backup_dir, 'backup.json')
        with open(file_path, 'w', encoding='utf-8') as backup_file:
            call_command('dumpdata', indent=2, stdout=backup_file)

        self.stdout.write(self.style.SUCCESS(f'База даних успішно збережена у {file_path}'))
