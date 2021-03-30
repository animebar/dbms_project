from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection, transaction
from django.db import connections
from datetime import datetime
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from PIL import Image
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def home(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * from events")
        row = cursor.fetchall()
        event_names = []
        event_ids = []
        event_description = []
        event_url = []
        event_slide_count = []
        count = 0
        for r in row:
            if count == 8:
                break
            event_names.append(r[2])
            event_ids.append(r[0])
            event_description.append(r[8])
            event_url.append(r[9])
            event_slide_count.append(count + 1)
            count += 1
    events = []
    for i in range(len(event_description)):
        temp = [event_names[i], event_description[i], event_ids[i], event_url[i], event_slide_count[i]]
        events.append(temp)

    context = {'events': events}
    if 'user_id' in request.session:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * from user WHERE user_id = %s", [request.session['user_id']])
            row = cursor.fetchone()
            name = row[2]
            wallet_amount = row[6]

        log_in = False
        if 'user_id' in request.session:
            log_in = True
        context = {
            'log_in': log_in,
            'name': name,
            'wallet_amount': wallet_amount,
            'events': events
        }
        return render(request, 'home/home.html', context)
    else:
        return render(request, 'home/home.html', context)


def search_results(request):
    if request.method == 'POST':
        search = request.POST['search']
        search_text = '%' + search + '%'
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM events WHERE event_name LIKE %s LIMIT 3", [search_text])
            events_ = cursor.fetchall()

        events = []
        for event in events_:
            temp = [event[0], event[2], event[8], event[3], event[10], event[9]]  # id, name, description, time, cost
            events.append(temp)
            url = event[9]
            p = str(BASE_DIR) + url
            img = Image.open(p)
            if img.height != 720 or img.width != 400:
                new_img = (720, 400)
                img.thumbnail(new_img)
                img.save(p)

        search_list = search.split(' ')
        events_tag_list = []
        for tag in search_list:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM tags WHERE tag_description LIKE %s LIMIT 3", [search_text])
                events_ = cursor.fetchall()

            for event_ in events_:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT * FROM events WHERE event_id = %s", [event_[0]])
                    event = cursor.fetchone()
                temp = [event[0], event[2], event[8], event[3], event[10],
                        event[9]]  # id, name, description, time, cost
                url = event[9]
                p = str(BASE_DIR) + url
                img = Image.open(p)
                if img.height != 720 or img.width != 400:
                    new_img = (720, 400)
                    img.thumbnail(new_img)
                    img.save(p)
                if temp in events_tag_list:
                    continue
                events_tag_list.append(temp)

        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM events WHERE description LIKE %s LIMIT 3", [search_text])
            events_ = cursor.fetchall()

        events_description_list = []
        for event in events_:
            temp = [event[0], event[2], event[8], event[3], event[10], event[9]]  # id, name, description, time, cost
            url = event[9]
            p = str(BASE_DIR) + url
            img = Image.open(p)
            if img.height != 720 or img.width != 400:
                new_img = (720, 400)
                img.thumbnail(new_img)
                img.save(p)
            events_description_list.append(temp)

        log_in = False
        if 'user_id' in request.session:
            log_in = True
        context = {
            'log_in': log_in,
            'events': events,
            'events_tag_list': events_tag_list,
            'events_description_list': events_description_list,
        }
        return render(request, 'home/search_events.html', context)
