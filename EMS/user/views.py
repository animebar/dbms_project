from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection, transaction
from django.db import connections
from datetime import datetime

# Create your views here.
from django.http import HttpResponse


def index(request):
    return HttpResponse("Hello, world. You're at the user index.")


def signup(request):
    context = {}
    if request.method == 'POST':
        name = request.POST["fullname"]
        email = request.POST["email"]
        password = request.POST["password"]
        confirm_password = request.POST["confirm_password"]
        date_of_birth = request.POST["dob"]
        if password != confirm_password:
            messages.error(request, f'Password do not match')
            context = {
                'message': 'password and confirm password not matching',
                'type': 'error'
            }
            return render(request, 'user/signup.html', context)
        print(name, email, password, confirm_password)
        cursor = connections['default'].cursor()
        cursor.execute("INSERT INTO user(name,email,password, DoB)  VALUES (%s, %s,%s,%s)",
                       [name, email, password, date_of_birth])
        return redirect('user:sign-in')

    else:
        return render(request, 'user/signup.html')


def signin(request):
    context = {}
    if request.method == 'POST':
        email = request.POST["email"]
        password = request.POST["password"]
        with connection.cursor() as cursor:
            cursor.execute("SELECT * from user WHERE email = %s AND password = %s", [email, password])
            row = cursor.fetchone()
            if row is None:
                messages.error(request, f'User Not found! If you are new you may register first.')
                context = {
                    'message': 'The email address or mobile number you entered is not connected to an account',
                    'type': 'error'
                }
                return render(request, 'user/signin.html', context)

            request.session['user_id'] = row[0]  # kind of log in
            return redirect('home:EMS-home')

    else:
        return render(request, 'user/signin.html')


def logout(request):
    if 'user_id' in request.session:
        del request.session['user_id']
        return redirect('home:EMS-home')
    else:
        return redirect('user:sign-in')


def profile(request):
    if 'user_id' in request.session:
        return render(request, 'user/user_profile.html')
    return redirect('user:sign-in')