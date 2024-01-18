from django.shortcuts import render, redirect
from django.contrib import auth
from django.contrib.auth.models import User

def welcome(request) :
    return render(request, 'calc/index.html')

def main(request) :
    return render(request, 'calc/main.html')

def login(request) :
    if request.method == "POST":
        username = request.POST["username"]
        password1 = request.POST["password1"]

        user = auth.authenticate(
            request, username=username, password=password1
        )

        if user is not None :
            auth.login(request, user)
            return redirect("calc:main")
    else :
        return render(request, 'calc/login.html')
    
    

