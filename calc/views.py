from django.shortcuts import render, redirect
from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Profile, Common_Career
import re

def welcome(request) :
    return render(request, 'calc/index.html')

def main(request) :
    if request.user.is_authenticated :
        area = Profile.objects.get(user__username=request.user.username)
        datas = {
            'area': area,
        }
        return render(request, "calc/main.html", datas)
    else :
        return render(request, "calc/main.html", datas)
    

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
            messages.error(request, 'loginfail')
            return render(request, 'calc/login.html')


    else :
        return render(request, 'calc/login.html')
    
def register(request) :
    if request.method == 'POST' :
        user_id = request.POST["username"]
        password1 = request.POST["password1"]
        password2 = request.POST["password2"]
        area_select = request.POST["area_select"]
        
        ptn_user = r'^[a-zA-Z0-9]{6,15}$'
        total_area = ['seoul', 'busan', 'daegu', 'incheon', 'gwangju', 'daejeon', 'ulsan', 'sejong', 'gyeongi', 'gangwon', 'chungbuk', 'chungnam', 'jeonbuk', 'jeonnam', 'gyeongbuk', 'gyeongnam', 'jeju']
            
        if re.match(ptn_user, user_id) and (len(password1)>=6 and len(password1)<=20) and (len(password2)>=6 and len(password2)<=20) and (password1 == password2) and (area_select in total_area) :
            user = User.objects.create_user(
                username = user_id,
                password = password1
            )
            profile = Profile(user=user, area=area_select)
            profile.save()

            return redirect("calc:login")
        
        else :
            redirect("calc:register")




    return render(request, "calc/register.html")
    

def logout(request) : 
    auth.logout(request)
    return redirect("calc:welcome")
    





def common(request) :
    if request.user.is_authenticated :
        area = Profile.objects.get(user__username=request.user.username)
        
        datas = {
            'area' : area,
        }
        return render(request, "calc/common/common.html", datas)
    else :
        return render(request, "calc/common/common.html", datas)

def common_career(request) :
    if request.user.is_authenticated :

        if request.method == "POST" :
            editdata = Common_Career.objects.get(user__username=request.user.username)
            if request.POST["career_year"] != '' :
                editdata.career_year = request.POST["career_year"]
            else : 
                editdata.career_year = 0
            if request.POST["career_month"] != '' :
                editdata.career_month = request.POST["career_month"]
            else :
                editdata.career_month = 0
            editdata.save()
            return redirect("calc:cc")


        area = Profile.objects.get(user__username=request.user.username)
        try :
            point = Common_Career.objects.get(user__username=request.user.username)
        except :
            user = User.objects.get(username=request.user.username)
            Common_Career.objects.create(user=user)
            point = Common_Career.objects.get(user__username=request.user.username)
        datas = {
            'area': area,
            'point' : point,
        }
    return render(request, "calc/common/common_career.html", datas)

def common_workperformance(request) :
    return render(request, "calc/common/common_wp.html")

def common_training(request) :
    return render(request, "calc/common/common_training.html")