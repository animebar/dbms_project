from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection, transaction
from django.db import connections
from datetime import datetime
from django.urls import reverse
from datetime import date

from django.core.files.storage import FileSystemStorage
from django.conf import settings
from PIL import Image
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def view_event(request, id):
    all_tags = []
    is_valid = True
    today = (date.today())
    with connection.cursor() as cursor:
        cursor.execute("SELECT tag_description from tags WHERE event_id = %s", [id])
        row = cursor.fetchall()
        for r in row:
            all_tags.append(str(r))

    for i in range(len(all_tags)):
        all_tags[i] = all_tags[i].strip('(')
        all_tags[i] = all_tags[i].strip(')')
        all_tags[i] = all_tags[i].strip(',')
        s = "'"
        all_tags[i] = all_tags[i].strip(s)
    event_ids = set()
    for t in all_tags:
        with connection.cursor() as cursor:
            cursor.execute("SELECT event_id from tags WHERE tag_description = %s", [t])
            row = cursor.fetchall()
        for r in row:
            s = str(r)
            s = s.strip('(')
            s = s.strip(')')
            s = s.strip(',')
            k = "'"
            s = s.strip(k)
            event_ids.add(s)
    if str(id) in event_ids:
        event_ids.remove(str(id))
    extra_event_descs = []
    extra_event_names = []
    extra_event_ids = []
    extra_event_urls = []
    for event_id in event_ids:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * from events WHERE event_id = %s", [event_id])
            row = cursor.fetchone()
            extra_event_ids.append(row[0])
            extra_event_descs.append(row[8])
            extra_event_names.append(row[2])
            extra_event_urls.append(row[9])
    context = {}
    in_cart = False
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM events WHERE event_id = %s", [id])
        row = cursor.fetchone()
        cursor.execute("SELECT distinct(user_id), event_id, review FROM reviews WHERE event_id = %s limit 2", [id])
        reviews = cursor.fetchall()

        if 'user_id' in request.session:
            cursor.execute("SELECT * FROM cart WHERE user_id =  %s AND event_id = %s", [request.session["user_id"], id])

            if cursor.fetchall() is not ():
                in_cart = True

        if row is None:
            messages.error(request, f'Event does not exist')
            context = {
                'message': 'Event does not exist',
                'type': 'error'
            }
            return redirect('home:EMS-home')
        processed_review = []
        if reviews is None:
            reviews_count = 0
        else:
            reviews_count = len(reviews)
            for review in reviews:
                cursor.execute("SELECT concat(first_name, ' ', last_name) FROM user WHERE user_id = %s", [review[0]])
                name = cursor.fetchone()[0]
                comment = review[2]
                cursor.execute("SELECT profile_pic_path FROM user WHERE user_id = %s", [review[0]])
                review_user_path = cursor.fetchone()[0]
                p = str(BASE_DIR) + review_user_path
                img = Image.open(p)
                if img.height != 107 or img.width != 107:
                    new_img = (107, 107)
                    img.thumbnail(new_img)
                    img.save(p)
                processed_review.append((name, comment, review_user_path))
    event_name = row[2]
    host_id = row[1]
    description = row[8]
    cost = row[10]
    max_capacity = row[7]
    event_date = row[3]
    if event_date < today:
        is_valid = False
    log_in = False
    event_main_image_path = row[9]
    p = str(BASE_DIR) + event_main_image_path
    img = Image.open(p)
    if img.height != 400 or img.width != 400:
        new_img = (400, 400)
        img.thumbnail(new_img)
        img.save(p)

    if 'user_id' in request.session:
        log_in = True

    extra_events = []
    for i in range(len(extra_event_names)):
        temp = [extra_event_names[i], extra_event_descs[i], extra_event_ids[i], extra_event_urls[i]]
        extra_events.append(temp)

    context = {
        'in_cart': in_cart,
        'log_in': log_in,
        'event_name': event_name,
        'host_id': host_id,
        'description': description,
        'cost': cost,
        'max_capacity': max_capacity,
        'event_date': event_date,
        'id': id,
        'reviews_count': reviews_count,
        'reviews': processed_review,
        'all_tags': all_tags,
        'extra_event': extra_events,
        'event_main_image_path': event_main_image_path,
        'is_valid': is_valid,
    }
    return render(request, 'events/event.html', context)


def host_event(request):
    context = {}
    if 'user_id' in request.session:
        if request.method == 'POST':
            doc = request.FILES
            uploaded_image_url = "/media/default_event.jpeg"
            if 'event_img' in request.FILES:
                doc_name = doc['event_img']
            else:
                doc_name = False
            if doc_name:
                image = request.FILES['event_img']
                fs = FileSystemStorage()
                image_name = fs.save(image.name, image)
                uploaded_image_url = fs.url(image_name)
            p = str(BASE_DIR) + uploaded_image_url
            img = Image.open(p)
            if img.height != 400 or img.width != 720:
                new_img = (720, 400)
                img.thumbnail(new_img)
                img.save(p)
            host_id = request.session['user_id']
            event_name = request.POST["event_name"]
            time_stamp = request.POST["event_date"]
            start_time = request.POST["event_start_time"]
            end_time = request.POST["event_end_time"]
            venue_info = request.POST["event_venue"]  # string

            if start_time > end_time:
                messages.error(request, f'Start time should be lesser than end time')
                return redirect('home:EMS-home')


            today = date.today()
            print(time_stamp, today)
            if time_stamp < str(today):
                messages.error(request, f'Event Date should be greater than equal to Current Date')
                return  redirect('home:EMS-home')

            all_tags = request.POST["event_tags"]
            tags = all_tags.split()

            venue_name = ""
            venue_street = ""
            i = 0
            for i in range(len(venue_info)):
                if venue_info[i] == ",":
                    j = i + 2
                    while venue_info[j] != ',':
                        venue_street += venue_info[j]
                        j += 1
                    break
                venue_name += venue_info[i]

            res = [int(i) for i in venue_info.split() if i.isdigit()]

            with connection.cursor() as cursor:
                cursor.execute("SELECT venue_id FROM venue WHERE venue_name = %s and street = %s",
                               [venue_name, venue_street])

                row = cursor.fetchone()
                venue_id = row[0]

            capacity = request.POST["event_number_guests"]

            if int(capacity) > res[0]:
                messages.error(request, f'Number of Guest is Greater than Hall Capacity')
                return redirect('events:host_event')

            description = request.POST['event_description']
            cost = request.POST['event_cost']
            cursor = connections['default'].cursor()

            cursor.execute(
                "INSERT INTO events(event_image_path,host_id, event_name, time_stamp,start_time, end_time,venue_id,max_capacity,description,cost)  VALUES (%s,%s, %s, %s,%s,%s,%s,%s,%s,%s)",
                [uploaded_image_url, host_id, event_name, time_stamp, start_time, end_time, venue_id, capacity,
                 description, cost])
            with connection.cursor() as cursor:
                cursor.execute("SELECT event_id FROM events WHERE host_id = %s order by event_id desc",
                               [host_id])
                row = cursor.fetchone()
                event_id = row[0]
            for tag in tags:
                cursor = connections['default'].cursor()
                cursor.execute("INSERT INTO tags(event_id, tag_description)  VALUES (%s, %s)",
                               [event_id, tag])
            messages.success(request, f'Your event has been successfully created')
            return redirect('home:EMS-home')

        else:
            cursor = connections['default'].cursor()
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM user WHERE user_id = %s", [request.session['user_id']])
                row = cursor.fetchone()
                user_image_path = row[1]
                first_name = row[3]
                cursor.execute("SELECT venue_name FROM venue ")
                row = cursor.fetchall()
                venue_names = []
                for r in row:
                    venue_names.append(str(r))
                for i in range(len(venue_names)):
                    venue_names[i] = venue_names[i].strip('(')
                    venue_names[i] = venue_names[i].strip(')')
                    venue_names[i] = venue_names[i].strip(',')
                    s = "'"

                    venue_names[i] = venue_names[i].strip(s) + ","

                cursor.execute("SELECT street FROM venue ")
                row = cursor.fetchall()
                venue_street = []
                for r in row:
                    venue_street.append(str(r))
                for i in range(len(venue_street)):
                    venue_street[i] = venue_street[i].strip('(')
                    venue_street[i] = venue_street[i].strip(')')
                    venue_street[i] = venue_street[i].strip(',')
                    s = "'"

                    venue_street[i] = venue_street[i].strip(s) + ","

                cursor.execute("SELECT capacity FROM venue ")
                row = cursor.fetchall()
                venue_capacity = []
                for r in row:
                    venue_capacity.append(str(r))
                for i in range(len(venue_capacity)):
                    venue_capacity[i] = venue_capacity[i].strip('(')
                    venue_capacity[i] = venue_capacity[i].strip(')')
                    venue_capacity[i] = venue_capacity[i].strip(',')
                    s = "'"
                    venue_capacity[i] = venue_capacity[i].strip(s)
                venue_details = []
                for i in range(len(venue_names)):
                    temp = [venue_names[i], venue_street[i], venue_capacity[i]]
                    venue_details.append(temp)
                context = {
                    'first_name': first_name,
                    'venue_details': venue_details,
                    'user_image_path': user_image_path
                }
            return render(request, 'events/host_event.html', context)
    return redirect('user:sign-in')


def book_event(request, id):
    if 'user_id' in request.session:
        if request.method == 'POST':
            is_yes = request.POST['btn']
            if is_yes == "CONFIRM!":

                user_id = request.session['user_id']
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM user WHERE user_id = %s", [request.session['user_id']])
                    row = cursor.fetchone()
                wallet_amount = row[8]
                number_of_seats = request.POST['seats']

                time = datetime.now()

                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM events WHERE event_id = %s", [id])
                    row = cursor.fetchone()
                cost = row[10]
                seats_left = row[7]

                transaction_amount = int(number_of_seats) * cost

                if int(number_of_seats) > seats_left:
                    messages.error(
                        request, f'Not enough seats left for the event!! ')
                    return redirect('events:view_event', id)

                if wallet_amount < transaction_amount:
                    messages.error(
                        request, f'You do not have enough money. Please add credit before booking')
                    return redirect('events:view_event', id)

                else:
                    cursor = connections['default'].cursor()

                    cursor.execute("UPDATE user SET wallet_amount = wallet_amount - %s WHERE user_id = %s",
                                   [transaction_amount, user_id])
                    cursor.execute("INSERT INTO booking(user_id, event_id,number_of_seats) VALUES(%s,%s,%s)",
                                   [user_id, id, number_of_seats])
                    cursor.execute("UPDATE events SET max_capacity = max_capacity - %s WHERE event_id = %s",
                                   [number_of_seats, id])
                    cursor.execute("INSERT INTO transactions(user_id, event_id, time_of_transaction) VALUES(%s,%s,%s)",
                                   [user_id, id, time])

                    messages.success(request, f'Your ticket is Booked')

            return redirect('events:view_event', id)
        context = {
            'log_in': True,
            'id': id
        }
        return render(request, 'events/book_event.html', context)

    else:
        messages.error(request, f'Please sign in before booking')
        return redirect('events:view_event', id)


def add_venue(request):
    if 'user_id' not in request.session:
        messages.error(request, f'Need to Log in First')
        return redirect('user:sign-in')
    if request.method == "POST":
        name = request.POST["venue_name"]
        capacity = request.POST["capacity"]
        state = request.POST["state"]
        street = request.POST["street"]
        pin = request.POST["zip"]

        flag = False
        try:
            available = request.POST["available"]
            flag = True
        except:
            flag = False

        cursor = connections['default'].cursor()
        cursor.execute(
            "INSERT INTO venue (owner_id, venue_name, capacity, availability, street, state, zip) VALUE (%s, %s, %s, %s, %s, %s, %s)",
            [request.session["user_id"], name, capacity, flag, street, state, pin])
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM user WHERE user_id = %s", [request.session['user_id']])
        row = cursor.fetchone()
        user_image_path = row[1]
    context = {
        'user_image_path': user_image_path
    }

    return render(request, 'events/add_venue.html', context)


def add_discount(request, id):
    if 'user_id' not in request.session:
        messages.error(request, f'Please Login First')
        return redirect('home:EMS-home')

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT * from events WHERE event_id = %s", [id])
        row = cursor.fetchone()
    if row == None:
        messages.error(request, f'Event does not exist! ')
        return redirect('events:host_event')
    return render(request, 'events/add_offers.html')


def add_review(request, id):
    if 'user_id' in request.session:
        if request.method == "POST":
            comment = request.POST["review"]

            with connection.cursor() as cursor:
                cursor.execute("SELECT review FROM reviews WHERE user_id = %s AND event_id = %s",
                               [request.session['user_id'], id])
                row = cursor.fetchone()
            if row is None:
                cursor = connections['default'].cursor()
                cursor.execute(
                    "INSERT INTO reviews (user_id, event_id, review) VALUES (%s, %s, %s)",
                    [request.session["user_id"], id, comment])
            else:
                cursor = connections['default'].cursor()
                cursor.execute(
                    "UPDATE reviews SET review=%s where user_id = %s and event_id=%s",
                    [comment, request.session["user_id"], id])
            messages.success(request, f'Your feedback noted! Thank you for your time')
            return redirect('events:view_event', id)
        else:
            context = {}
            with connection.cursor() as cursor:
                cursor.execute("SELECT review FROM reviews WHERE user_id = %s AND event_id = %s",
                               [request.session['user_id'], id])
                row = cursor.fetchone()
                if row is None:
                    context = {
                        'id': id,
                        'comment': 'Leave Your comment Here',
                        'commented': False
                    }
                else:
                    context = {
                        'id': id,
                        'comment': row[0],
                        'commented': True
                    }
            return render(request, 'events/feedback.html', context)
    else:
        messages.error(request, f'You need to be Signed first')
        return redirect('user:sign-in')


def remove_cart(request, id):
    if 'user_id' not in request.session:
        messages.error(request, f'You Need to be signed for removing into the cart')
        return redirect('events:view_event', id)
    cursor = connections['default'].cursor()
    cursor.execute(
        "DELETE FROM cart WHERE user_id = %s AND event_id = %s",
        [request.session["user_id"], id])
    return redirect('events:view_event', id)


def del_cart(request, id):
    if 'user_id' not in request.session:
        messages.error(request, f'You Need to be signed for removing into the cart')
        return redirect('events:view_event', id)
    cursor = connections['default'].cursor()
    cursor.execute(
        "DELETE FROM cart WHERE user_id = %s AND event_id = %s",
        [request.session["user_id"], id])
    return redirect('user:cart_info')


def insert_cart(request, id):
    if 'user_id' not in request.session:
        messages.error(request, f'You Need to be signed for adding into the cart')
        return redirect('events:view_event', id)
    cursor = connections['default'].cursor()
    cursor.execute(
        "INSERT INTO cart (user_id, event_id) VALUES (%s, %s)", [request.session["user_id"], id])
    return redirect('events:view_event', id)


def increase_cart(request, id):
    print("here increase")
    if 'user_id' not in request.session:
        messages.error(request, f'You Need to be signed for removing into the cart')
        return redirect('home:EMS-home')

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM events WHERE event_id = %s",
                       [id])
        event = cursor.fetchone()

    seats_left = event[7]
    cursor = connections['default'].cursor()
    cursor.execute(
        "UPDATE cart SET seat_count= seat_count + 1  WHERE user_id=%s AND event_id=%s AND seat_count <= %s",
        [request.session["user_id"], id, seats_left])
    return redirect('user:cart_info')


def decrease_cart(request, id):
    if 'user_id' not in request.session:
        messages.error(request, f'You Need to be signed for removing into the cart')
        return redirect('home:EMS-home')
    cursor = connections['default'].cursor()
    cursor.execute(
        "UPDATE cart SET seat_count= seat_count - 1  WHERE user_id=%s AND event_id=%s AND seat_count > 0",
        [request.session["user_id"], id])
    return redirect('user:cart_info')
