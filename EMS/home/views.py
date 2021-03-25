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
    context = {}
    if 'user_id' in request.session:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * from user WHERE user_id = %s", [request.session['user_id']])
            row = cursor.fetchone()

        context = {
            'log_in': True,
            'name': row[2],
            'wallet_amount': row[6],
        }
        return render(request, 'home/home.html', context)
    return render(request, 'home/home.html')
