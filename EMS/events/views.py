from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection, transaction
from django.db import connections
from datetime import datetime

from django.urls import reverse


def view_event(request, id):
    context = {}
    with connection.cursor() as cursor:
        cursor.execute("SELECT * from events WHERE event_id = %s", [id])
        row = cursor.fetchone()
        if row is None:
            messages.error(request, f'Event does not exist')
            context = {
                'message': 'Event does not exist',
                'type': 'error'
            }
            return redirect('home:EMS-home')
    event_name = row[2]
    host_id = row[1]
    description = row[8]
    cost = row[10]
    max_capacity = row[7]
    event_date = row[3]
    context = {
        'event_name': event_name,
        'host_id': host_id,
        'description': description,
        'cost': cost,
        'max_capacity': max_capacity,
        'event_date': event_date
    }
    return render(request, 'events/event.html', context)


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

# def book_event(request,id):


# Create your views here.
