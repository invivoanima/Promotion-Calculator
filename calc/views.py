from django.shortcuts import render

def welcome(request) :
    return render(request, 'calc/index.html')

def main(request) :
    return render(request, 'calc/main.html')

def login(request) :
    return render(request, 'calc/login.html')

