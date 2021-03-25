from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection, transaction
from django.db import connections
from datetime import datetime


def view_events(request,id):
	context = {}
	with connection.cursor() as cursor:
			cursor.execute("SELECT * from events WHERE event_id = %s", [id])
			row = cursor.fetchone()
			if row is None:
				messages.error(request, f'Event doesnot exist')
				context = {
					'message': 'Event doesnot exist',
					'type': 'error'
				}
				return render(request, 'home/home.html', context)
	event_name = row[2]
	host_id = row[1]
	description = row[10] 
	context = {
		'event_name': event_name
	}
	return render(request, 'events/event.html', context)
# Create your views here.
