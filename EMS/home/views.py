from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection, transaction
from django.db import connections
from datetime import datetime


def home(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * from events")
        row = cursor.fetchall()
        # print(row[0][0])
        event_names = []
        event_ids = []
        event_description = []
        count = 0
        for r in row:
            # print(r)
            if count==8:
                break
            event_names.append(r[2])
            event_ids.append(r[0])
            event_description.append(r[8])
            count+=1
    events = []
    for i in range(len(event_description)):
        temp = [event_names[i], event_description[i], event_ids[i]]
        events.append(temp)
    # print(events)    

    context = {'events':events}
    if 'user_id' in request.session:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * from user WHERE user_id = %s", [request.session['user_id']])
            row = cursor.fetchone()
            name = row[2]
            wallet_amount = row[6]
            

        
        context = {
            'log_in': True,
            'name': name,
            'wallet_amount': wallet_amount,
            'events':events
        }
        return render(request, 'home/home.html', context)
    else:
        return render(request, 'home/home.html',context)
