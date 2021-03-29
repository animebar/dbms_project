from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection, transaction
from django.db import connections
from datetime import datetime

from django.urls import reverse


def view_event(request, id):
    all_tags = []
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
    for event_id in event_ids:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * from events WHERE event_id = %s", [event_id])
            row = cursor.fetchone()
            extra_event_ids.append(row[0])
            extra_event_descs.append(row[8])
            extra_event_names.append(row[2])
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
                processed_review.append((name, comment))
    event_name = row[2]
    host_id = row[1]
    description = row[8]
    cost = row[10]
    max_capacity = row[7]
    event_date = row[3]
    log_in = False
    if 'user_id' in request.session:
        log_in = True

    extra_events = []
    for i in range(len(extra_event_names)):
        temp = [extra_event_names[i], extra_event_descs[i], extra_event_ids[i]]
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
        'extra_event': extra_events

    }
    return render(request, 'events/event.html', context)


def host_event(request):
    context = {}
    if 'user_id' in request.session:
        if request.method == 'POST':
            host_id = request.session['user_id']
            event_name = request.POST["event_name"]
            time_stamp = request.POST["event_date"]
            start_time = request.POST["event_start_time"]
            end_time = request.POST["event_end_time"]
            venue_info = request.POST["event_venue"]  # string

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

            capacity = res[0]
            description = request.POST['event_description']
            cost = request.POST['event_cost']
            cursor = connections['default'].cursor()

            cursor.execute(
                "INSERT INTO events(host_id, event_name, time_stamp,start_time, end_time,venue_id,max_capacity,description,cost)  VALUES (%s, %s, %s,%s,%s,%s,%s,%s,%s)",
                [host_id, event_name, time_stamp, start_time, end_time, venue_id, capacity, description, cost])
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
                    'venue_details': venue_details
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
                    cursor.execute(
                        "UPDATE user SET wallet_amount = wallet_amount - %s WHERE user_id = %s",
                        [transaction_amount, user_id])
                    cursor.execute("INSERT INTO booking(user_id, event_id,number_of_seats) VALUES(%s,%s,%s)", [
                        user_id, id, number_of_seats])
                    cursor.execute(
                        "UPDATE events SET max_capacity = max_capacity - %s WHERE event_id = %s", [number_of_seats, id])

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

    return render(request, 'events/add_venue.html')


def add_discount(request,id):
    if 'user_id' not in request.session:
        messages.error(request,f'Please Login First')
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
    cursor = connections['default'].cursor()
    cursor.execute(
        "UPDATE cart SET seat_count= seat_count + 1  WHERE user_id=%s AND event_id=%s",
        [request.session["user_id"], id])
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

    
