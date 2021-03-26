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
        'log_in': log_in,
        'event_name': event_name,
        'host_id': host_id,
        'description': description,
        'cost': cost,
        'max_capacity': max_capacity,
        'event_date': event_date,
        'id': id
    }
    return render(request, 'events/event.html', context)

def host_event(request):
    context={}
    if 'user_id' in request.session:
        if request.method == 'POST':
            host_id = request.session['user_id']
            event_name = request.POST["event_name"]
            time_stamp = request.POST["event_date"]
            start_time = request.POST["event_start_time"]
            end_time = request.POST["event_end_time"]
            venue_info = request.POST["event_venue"] #string
            venue_name = ""
            venue_street=""
            i=0
            for i in range(len(venue_info)):
                if venue_info[i]==",":
                    j=i+2
                    while venue_info[j]!=',':
                        venue_street+=venue_info[j]
                        j+=1
                    break
                venue_name+=venue_info[i]
            
            res = [int(i) for i in venue_info.split() if i.isdigit()]
            
            with connection.cursor() as cursor:
                cursor.execute("SELECT venue_id FROM venue WHERE venue_name = %s and street = %s", [venue_name, venue_street])
                row = cursor.fetchone()
                venue_id = row[0]
        
            capacity = res[0]
            description = request.POST['event_description']
            cost = request.POST['event_cost']
            cursor = connections['default'].cursor()
            cursor.execute("INSERT INTO events(host_id, event_name, time_stamp,start_time, end_time,venue_id,max_capacity,description,cost)  VALUES (%s, %s, %s,%s,%s,%s,%s,%s,%s)",
            [host_id, event_name, time_stamp, start_time, end_time,venue_id,capacity,description,cost])
            # return render(request, 'user/user_profile.html', context)
            print("event added")
            return redirect('user:profile')
        else:
            cursor = connections['default'].cursor()
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM user WHERE user_id = %s", [request.session['user_id']])
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
                    s="'"
                    venue_names[i] = venue_names[i].strip(s)+","
                cursor.execute("SELECT street FROM venue ")
                row = cursor.fetchall()
                venue_street = []
                for r in row:
                    venue_street.append(str(r))
                for i in range(len(venue_street)):
                    venue_street[i] = venue_street[i].strip('(')
                    venue_street[i] = venue_street[i].strip(')')
                    venue_street[i] = venue_street[i].strip(',')
                    s="'"
                    venue_street[i] = venue_street[i].strip(s)+","
                cursor.execute("SELECT capacity FROM venue ")
                row = cursor.fetchall()
                venue_capacity = []
                for r in row:
                    venue_capacity.append(str(r))
                for i in range(len(venue_capacity)):
                    venue_capacity[i] = venue_capacity[i].strip('(')
                    venue_capacity[i] = venue_capacity[i].strip(')')
                    venue_capacity[i] = venue_capacity[i].strip(',')
                    s="'"
                    venue_capacity[i] = venue_capacity[i].strip(s)
                venue_details= []
                for i in range(len(venue_names)):
                    temp = []
                    temp.append(venue_names[i])
                    temp.append(venue_street[i])
                    temp.append(venue_capacity[i])
                    venue_details.append(temp)
                context={
                    'first_name': first_name,
                    'venue_details': venue_details
                }
            return render(request,'events/host_event.html',context)
    return redirect('user:sign-in')


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
                
                
                
                with connection.cursor() as cursor:
                    cursor.execute("SELECT * from events WHERE event_id = %s", [id])
                    row = cursor.fetchone()
                cost = row[10]
                seats_left = row[7] 
                transaction_amount = int(number_of_seats)*cost
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