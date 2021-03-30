from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection, transaction
from django.db import connections
from datetime import datetime
from datetime import date

import datetime
from PIL import Image
import os
from pathlib import Path
from django.conf import settings
from django.core.files.storage import FileSystemStorage
# Create your views here.
from django.http import HttpResponse

BASE_DIR = Path(__file__).resolve().parent.parent

def index(request):
    return HttpResponse("Hello, world. You're at the user index.")


def signup(request):
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
        path = "/media/default.jpg"
        cursor.execute("INSERT INTO user(profile_pic_path,first_name, last_name, email,password, DoB)  VALUES (%s,%s, %s, %s,%s,%s)",
                       [path,first_name, last_name, email, password, date_of_birth])
        return redirect('user:sign-in')
    else:
        return render(request, 'user/signup.html')


def signin(request):
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
        with connection.cursor() as cursor:
            cursor.execute("SELECT * from user WHERE user_id = %s", [request.session['user_id']])
            row = cursor.fetchone()
            uploaded_image_url = row[1]
        doc = request.FILES
        if 'img' in request.FILES:
            doc_name = doc['img']
        else:
            doc_name = False
        if request.method == 'POST' and doc_name:
            image = request.FILES['img']
            fs = FileSystemStorage()
            image_name = fs.save(image.name, image)
            uploaded_image_url = fs.url(image_name)
            cursor = connections['default'].cursor()
            cursor.execute(
                "UPDATE user SET profile_pic_path=%s WHERE user_id = %s",
                [uploaded_image_url, request.session['user_id']])
        if request.method == 'POST':
            first_name = request.POST["first_name"]
            last_name = request.POST["last_name"]
            email = request.POST["email"]
            about = request.POST["about"]
            state = request.POST["state"]
            street = request.POST["street"]
            postal_address = request.POST["zip"]
            country_code = request.POST["country_code"]
            phone_number = request.POST["phone_number"]
            user_id = request.session['user_id']
            cursor = connections['default'].cursor()
            cursor.execute(
                "UPDATE user SET first_name = %s, last_name = %s, email = %s, about = %s, state = %s, zip = %s, street = %s WHERE user_id = %s",
                [first_name, last_name, email, about, state, postal_address, street, user_id])
            try:
                cursor.execute("INSERT INTO phone_number(user_id, country_code, phone_number) VALUES(%s,%s,%s)",
                               [user_id, country_code, phone_number])
            except:
                pass

        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM cart WHERE user_id = %s", [request.session['user_id']])
            row = cursor.fetchall()
            cart_count = len(row)
            cursor.execute("SELECT * FROM user WHERE user_id = %s", [request.session['user_id']])
            row = cursor.fetchone()
            cursor.execute("SELECT year(DOB) FROM user WHERE user_id = %s", [request.session['user_id']])
            y = cursor.fetchone()
            cursor.execute("SELECT account_number, IFSC FROM account_details WHERE user_id = %s",
                           [request.session['user_id']])
            raw_account_details = cursor.fetchall()
        age = datetime.datetime.now().year - y[0]
        account_details = []  #

        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM transactions WHERE user_id = %s", [request.session['user_id']])
            row_t = cursor.fetchall()

        transactions = len(row_t)

        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM phone_number WHERE user_id = %s", [request.session['user_id']])
            row_p = cursor.fetchone()

        phone_number = None
        country_code = None
        if row_p:
            phone_number = row_p[2]
            country_code = row_p[1]
        for raw_account in raw_account_details:
            account_details.append(raw_account)

        account_present = False
        if len(account_details):
            account_present = True
        p = str(BASE_DIR) + uploaded_image_url
        img = Image.open(p)
        if img.height > 300 or img.width > 300:
            new_img = (300, 300)
            img.thumbnail(new_img)
            img.save(p)
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
            'age': age,
            'account_details': account_details,
            'transactions': transactions,
            'phone_number': phone_number,
            'uploaded_image_url': uploaded_image_url,
            'account_present': account_present,
            'cart_count': cart_count,
            'country_code': country_code,
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
        'age': age,
        'uploaded_image_url':row[1]
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
    today = str(date.today())
    if 'user_id' not in request.session:
        messages.error(request, f'Sign in to view your cart')
        return redirect('user:sign-in')
    with connection.cursor() as cursor:
        cursor.execute("SELECT cart.* FROM cart, events WHERE user_id = %s AND cart.event_id = events.event_id AND events.time_stamp >= %s", [request.session["user_id"], today])
        cart_details = cursor.fetchall()
        promo_code = None
        if 'code' in request.session:
            promo_code = request.session['code']

        discount = 0

        if 'discount' in request.session:
            discount = request.session['discount']

        print('discount:' + str(discount) + '\n')
        discount = discount / 100
        processed_cart = []
        total_cost = 0
        for cart in cart_details:
            cursor.execute("SELECT event_name, cost, description FROM events WHERE event_id=%s", [cart[1]])
            event = cursor.fetchone()
            processed_cart.append(
                (event[0], event[1], cart[2], event[1] * cart[2], event[2][:10],
                 cart[1]))  # name, cost, seat_count, total_per_event, description[:10],
            print((event[0], event[1], cart[2], event[1] * cart[2], event[2][:10], cart[1]))
            total_cost = total_cost + event[1] * cart[2]

        print('total cost' + str(total_cost) + '\n')
        total_cost = (1 - discount) * total_cost

        context = {
            'log_in': True,
            'cart_details': processed_cart,
            'total_cost': total_cost,
            'total_count': len(processed_cart),
            'promo_code': promo_code,
        }
    return render(request, 'user/cart.html', context)


def add_account(request):
    if 'user_id' not in request.session:
        messages.error(request, f'Need to be signed for adding Bank Account')
        return redirect('home:EMS-home')
    if request.method == "POST":
        account_number = request.POST["account_number"]
        IFSC = request.POST["IFSC"]
        print(account_number, IFSC)
        cursor = connections['default'].cursor()
        cursor.execute("INSERT INTO account_details (user_id, account_number, IFSC) VALUES (%s, %s, %s)",
                       [request.session["user_id"], account_number, IFSC])
        return redirect('user:profile')
    return render(request, 'user/add_account.html')


def PromoCode(request):
    # cart_info()
    if 'user_id' not in request.session:
        messages.error(request, f'Sign in to view your cart')
        return redirect('user:sign-in')

    code = request.POST['code']
    request.session['code'] = code
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM offers WHERE promo_code = %s", [code])
        offer = cursor.fetchone()

    if offer is None:
        messages.error(request, f'invalid promo code')
        return redirect('user:cart_info')

    time = datetime.datetime.now()
    end_time = offer[4]
    start_time = offer[3]
    if time > end_time or time < start_time:
        messages.error(request, f'invalid promo code')
        return redirect('user:cart_info')

    discount = offer[2]
    request.session['discount'] = discount

    return redirect('user:cart_info')


def Checkout(request):
    if 'user_id' not in request.session:
        messages.error(request, f'Sign in to view your cart')
        return redirect('user:sign-in')
    today = str(date.today())
    with connection.cursor() as cursor:
        cursor.execute("SELECT cart.* FROM cart, events WHERE user_id = %s AND cart.event_id = events.event_id AND events.time_stamp >= %s", [request.session["user_id"], today])
        cart_details = cursor.fetchall()

    processed_cart = []
    discount = 0
    if 'discount' in request.session:
        discount = request.session['discount']
    discount = discount / 100
    total_cost = 0
    with connection.cursor() as cursor:

        for cart in cart_details:
            cursor.execute("SELECT event_name, cost, description FROM events WHERE event_id=%s", [cart[1]])
            event = cursor.fetchone()
            processed_cart.append(
                (event[0], event[1], cart[2], event[1] * cart[2], event[2][:10],
                 cart[1]))  # name, cost, seat_count, total_per_event, description[:10],
            print((event[0], event[1], cart[2], event[1] * cart[2], event[2][:10], cart[1]))
        total_cost = total_cost + event[1] * cart[2]
        total_cost = (1 - discount) * total_cost

    user_id = request.session['user_id']
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM user WHERE user_id = %s", [user_id])
        user = cursor.fetchone()
    wallet_amount = user[8]
    if wallet_amount < total_cost:
        messages.error(request, f'You do not have enough money in the wallet!')
        return redirect('user:cart_info')

    time = datetime.datetime.now()
    with connection.cursor() as cursor1:
        for event in processed_cart:
            message = 'Your request is booked for event' + event[0]

            cursor1.execute("SELECT max_capacity FROM events WHERE event_id = %s", [event[5]])
            seats_left = cursor1.fetchone()
            number_of_seats = event[2]

            if seats_left[0] < number_of_seats:
                message = 'Not enough seats left for the event' + event[0]
                messages.error(request, message)
                continue
            cursor = connections['default'].cursor()
            print('amount = %d\n', event[3])
            amt = event[3] * (1 - discount)
            cursor.execute("UPDATE user SET wallet_amount = wallet_amount - %s WHERE user_id = %s", [amt, user_id])

            cursor1.execute("SELECT * FROM booking WHERE user_id = %s and event_id = %s", [user_id, event[5]])
            row = cursor1.fetchone()
            if row is None:
                cursor.execute("INSERT INTO booking(user_id, event_id,number_of_seats) VALUES(%s,%s,%s)",
                               [user_id, event[5], number_of_seats])
            else:
                cursor.execute(
                    "UPDATE booking SET number_of_seats = number_of_seats + %s WHERE user_id = %s AND event_id = %s",
                    [number_of_seats, user_id, event[5]])

            cursor.execute("UPDATE events SET max_capacity = max_capacity - %s WHERE event_id = %s",
                           [number_of_seats, event[5]])
            cursor.execute("INSERT INTO transactions(user_id, event_id, time_of_transaction) VALUES(%s,%s,%s)",
                           [user_id, event[5], time])
            cursor.execute("DELETE FROM cart WHERE user_id = %s AND event_id = %s", [user_id, event[5]])
            messages.success(request, message)
            cursor.close()

    if 'code' in request.session:
        del request.session['code']
    if 'discount' in request.session:
        del request.session['discount']
    return redirect('user:cart_info')
