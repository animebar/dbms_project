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
    log_in = False
    if 'user_id' in request.session:
        log_in = True
    context = {
        'log_in': True,
        'event_name': event_name,
        'host_id': host_id,
        'description': description,
        'cost': cost,
        'max_capacity': max_capacity,
        'event_date': event_date,
        'id': id
    }
    return render(request, 'events/event.html', context)


def book_event(request,id):
    if 'user_id' in request.session:
        if request.method == 'POST':
            is_yes = request.POST['btn']
            print(is_yes)
            if is_yes == "CONFIRM!":
                user_id = request.session['user_id']
                with connection.cursor() as cursor:
                    cursor.execute("SELECT * from user WHERE user_id = %s", [request.session['user_id']])
                    row = cursor.fetchone()
                wallet_amount = row[8]
                number_of_seats = request.POST['seats']
                print(number_of_seats*5)
                transaction_amount = int(number_of_seats)*5
                
                with connection.cursor() as cursor:
                    cursor.execute("SELECT * from events WHERE event_id = %s", [id])
                    row = cursor.fetchone()

                seats_left = row[7] 
                if int(number_of_seats) > seats_left:
                    messages.error(request, f'Not enough seats left for the event!! ')
                    return redirect('events:view_event', id)

                if wallet_amount < transaction_amount:
                    messages.error(request, f'You donot have enough money. Please add credit before booking')
                    return redirect('events:view_event', id)
                    
                else:
                    cursor = connections['default'].cursor()
                    cursor.execute("UPDATE user SET wallet_amount = wallet_amount - %s WHERE user_id = %s" ,[transaction_amount, user_id])
                    cursor.execute("INSERT INTO booking(user_id, event_id,number_of_seats) VALUES(%s,%s,%s)", [user_id, id, number_of_seats])
                    cursor.execute("UPDATE events SET max_capacity = max_capacity - %s WHERE event_id = %s" ,[number_of_seats, id])
                    messages.success(request, f'Your ticket is Booked')


            return redirect('events:view_event', id)
        context = {
            'log_in':True,
            'id':id
        }
        return render(request, 'events/book_event.html',context)        

    else:
        messages.error(request, f'Please sign in before booking')
        return redirect('events:view_event', id)


# Create your views here.
