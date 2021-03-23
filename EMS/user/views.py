from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib import messages

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

    else:
        return render(request, 'user/signup.html')
