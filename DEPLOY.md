```
ssh root@45.91.169.29
```

cd huhy/huhy_site/


```
sudo apt update && sudo apt upgrade -y

```

```
mkdir huhy
cd huhy/

```
або інша команда, залежно від налаштувань
```
sudo supervisorctl restart huhy

```

sudo nginx -t  # Перевірка конфігурації на помилки

git branch

git pull

git checkout <branch_name>



# DEPLOY.md

Цей файл містить інструкції та команди для деплою проекту `huhysite` на сервер. Він допоможе швидко виконувати основні операції з оновлення, налаштування та обслуговування сайту.

---

## 1. Підключення до сервера

Підключіться до сервера за допомогою SSH:

```bash
ssh root@45.91.169.29
```

## 2. Навігація та підготовка середовища
Перейдіть до директорії проекту (залежно від вашої структури):
```
cd /path/to/huhy/huhy_site/
```

```
cd huhy/huhy_site/
```
## 3. Оновлення системи
Перед оновленням проекту рекомендується оновити пакети системи:
```
sudo apt update && sudo apt upgrade -y
```
## 4. Оновлення коду
Перевірте гілку, завантажте останні зміни та перемкніться на потрібну гілку:
```
git branch           # Перевірте поточну гілку
git pull             # Завантажте останні зміни з віддаленого репозиторію
git checkout <branch_name>   # Перемкніться на потрібну гілку (наприклад, master або production)
```

## 5. Зміна пароля адміністратора
Щоб змінити пароль адміністратора або інших користувачів, виконайте наступне:

Запустіть Django shell:

```
python manage.py shell
```

Виконайте наступний код у shell:

```
from django.contrib.auth import get_user_model
User = get_user_model()
# Перевірте список користувачів:
print(User.objects.values("username"))
# Змініть пароль конкретного користувача:
user = User.objects.get(username="admin")  # Вкажіть реальний username
user.set_password("новий_пароль")
user.save()
print("Пароль оновлено!")
```

Альтернативно, для всіх користувачів, де пароль не є хешованим:

```
from django.contrib.auth import get_user_model
User = get_user_model()
for user in User.objects.all():
    if not user.password.startswith("pbkdf2_sha256$"):  # Якщо пароль не хешований
        user.set_password("новий_пароль")  # Встановіть тимчасовий пароль
        user.save()
        print(f"Пароль оновлено для користувача: {user.username}")
```

Вийдіть із shell (Ctrl+D).

## 6. Перезапуск сервісів
Перезапуск процесу через Supervisor

sudo supervisorctl restart huhy

Перевірка конфігурації Nginx

sudo nginx -t

Якщо конфігурація пройшла успішно, перезапустіть Nginx:

sudo systemctl restart nginx


## 7. Статичні файли та міграції
Збір статичних файлів
Перед деплоєм переконайтеся, що всі статичні файли зібрані:


python manage.py collectstatic


Виконання міграцій
Якщо внесено зміни в моделі, виконайте:

python manage.py makemigrations
python manage.py migrate



## 8. Docker (якщо використовується)
Якщо ваш проект працює у Docker, використовуйте наступні команди:

Запуск контейнерів

docker-compose up -d
Зупинка контейнерів

docker-compose down
Перезапуск контейнерів

docker-compose restart
Вхід у контейнер

docker-compose exec web bash
Перегляд логів контейнерів

docker-compose logs
Видалення всіх контейнерів, томів та образів

docker system prune -a --volumes
## 9. Додаткові корисні команди
Оновлення залежностей (з Poetry)

poetry update
Генерація requirements.txt

poetry export -f requirements.txt --output requirements.txt --without-hashes
Резервне копіювання бази даних

pg_dump -U <user> -h <host> <database_name> > backup.sql
Відновлення бази даних

psql -U <user> -h <host> <database_name> < backup.sql
## 10. GitHub-команди
Клонування репозиторію

git clone https://github.com/yourusername/huhysite.git
Перевірка статусу репозиторію

git status
Додавання змін до коміту

git add .
Комітування змін

git commit -m "Опис змін"
Відправлення змін на сервер

git push