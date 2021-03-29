from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection, transaction
from django.db import connections
from datetime import datetime
import datetime
# Create your views here.
from django.http import HttpResponse


def index(request):
    return HttpResponse("Hello, world. You're at the user index.")


def signup(request):
    context = {}
    if request.method == 'POST':
        first_name = request.POST["first_name"]
        last_name = request.POST["last_name"]
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
        cursor = connections['default'].cursor()
        cursor.execute("INSERT INTO user(first_name, last_name, email,password, DoB)  VALUES (%s, %s, %s,%s,%s)",
                       [first_name, last_name, email, password, date_of_birth])
        return redirect('user:sign-in')
    else:
        return render(request, 'user/signup.html')


def signin(request):
    context = {}
    if 'user_id' in request.session:
        return redirect('home:EMS-home')
    elif request.method == 'POST':
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
    context = {}
    if 'user_id' in request.session:
        if request.method == 'POST':
            first_name = request.POST["first_name"]
            last_name = request.POST["last_name"]
            email = request.POST["email"]
            about = request.POST["about"]
            state = request.POST["state"]
            street = request.POST["street"]
            postal_address = request.POST["zip"]
            cursor = connections['default'].cursor()
            cursor.execute(
                "UPDATE user SET first_name = %s, last_name = %s, email = %s, about = %s, state = %s, zip = %s, street = %s",
                [first_name, last_name, email, about, state, postal_address, street])

        with connection.cursor() as cursor:
            cursor.execute("SELECT * from user WHERE user_id = %s", [request.session['user_id']])
            row = cursor.fetchone()
            cursor.execute("SELECT year(DOB) from user WHERE user_id = %s", [request.session['user_id']])
            y = cursor.fetchone()
            cursor.execute("SELECT account_number, IFSC from account_details WHERE user_id = %s",
                           [request.session['user_id']])
            raw_account_details = cursor.fetchall()
        age = datetime.datetime.now().year - y[0]
        account_details = []  #

        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM transactions WHERE user_id = %s", [request.session['user_id']])
            row_t = cursor.fetchall()

        transactions = len(row_t)

        for raw_account in raw_account_details:
            account_details.append(raw_account)
        context = {
            'log_in': True,
            'first_name': row[3],
            'last_name': row[4],
            'wallet_amount': row[8],
            'profile_pic': row[1],
            'email': row[10],
            'about': row[11],
            'DoB': row[9],
            'street': row[5],
            'state': row[6],
            'zip': row[7],
            'wallet_amount': row[8],
            'age': age,
            'account_details': account_details,
            'transactions': transactions,
        }
        return render(request, 'user/user_profile.html', context)
    return redirect('user:sign-in')


def view_profile(request, id):
    log_in = False
    if 'user_id' in request.session:
        log_in = True

    with connection.cursor() as cursor:
        cursor.execute("SELECT * from user WHERE user_id = %s", [id])
        row = cursor.fetchone()
        cursor.execute("SELECT year(DOB) from user WHERE user_id = %s", [id])
        y = cursor.fetchone()
    age = datetime.datetime.now().year - y[0]
    context = {
        'log_in': log_in,
        'first_name': row[3],
        'last_name': row[4],
        'profile_pic': row[1],
        'email': row[10],
        'about': row[11],
        'street': row[5],
        'state': row[6],
        'zip': row[7],
        'age': age
    }
    return render(request, 'user/view_profile.html', context)


def add_money(request):
    if 'user_id' not in request.session:
        messages.error(request, f'Need to Log in First')
        return redirect('user:sign-in')
    if request.method == "POST":
        amount = request.POST["amount"]
        cursor = connections['default'].cursor()
        cursor.execute("UPDATE user SET wallet_amount = wallet_amount + %s WHERE user_id = %s",
                       [amount, request.session["user_id"]])
    return redirect('user:profile')


def view_transactions(request):
    if 'user_id' not in request.session:
        messages.error(request, f'Please login to view your transactions')
        return redirect('user:sign-in')

    user_id = request.session['user_id']
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM transactions WHERE user_id = %s", [user_id])
        row = cursor.fetchall()

    transactions_ = []
    for i in range(len(row)):
        event_id = row[i][1]
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM events WHERE event_id = %s", [event_id])
            row_i = cursor.fetchone()
            event_i = [event_id, row_i[2], row_i[8], row_i[3], row[i][2]]
            transactions_.append(event_i)

    context = {
        'log_in': True,
        'transactions': transactions_,
    }
    return render(request, 'user/transactions.html', context)


def cart_info(request):
    if 'user_id' not in request.session:
        messages.error(request, f'Sign in to view your cart')
        return redirect('user:sign-in')
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM cart WHERE user_id = %s", [request.session["user_id"]])
        cart_details = cursor.fetchall()

        processed_cart = []
        total_cost = 0
        total_count = 0
        for cart in cart_details:
            cursor.execute("SELECT event_name, cost, description FROM events WHERE event_id=%s", [cart[1]])
            event = cursor.fetchone()
            processed_cart.append(
                (event[0], event[1], cart[2], event[1] * cart[2], event[2][:10], cart[1]))  # name, cost, seat_count, total_per_event, description[:10],
            print((event[0], event[1], cart[2], event[1] * cart[2], event[2][:10], cart[1]))
            total_cost = total_cost + event[1] * cart[2]
        context = {
            'cart_details': processed_cart,
            'total_cost': total_cost,
            'total_count': len(processed_cart)
        }
    return render(request, 'user/cart.html', context)
