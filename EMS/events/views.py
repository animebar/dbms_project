from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection, transaction
from django.db import connections
from datetime import datetime

from django.urls import reverse


def view_events(request, id):
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
    description = row[10]
    cost = row[12]
    max_capacity = row[9]
    event_day = row[6]
    context = {
        'event_name': event_name,
        'host_id': host_id,
        'description': description,
        'cost': cost,
        'max_capacity': max_capacity,
        'event_day': event_day
    }
    return render(request, 'events/event.html', context)
# Create your views here.
