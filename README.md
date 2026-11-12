# Между парами

Студенческий портал КФУ: карта заведений рядом с университетом с отзывами
и лента мемов с голосованием.

Учебный проект по дисциплине «Современные технологии разработки ПО».

## Запуск

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Сайт откроется по адресу http://127.0.0.1:8000/
