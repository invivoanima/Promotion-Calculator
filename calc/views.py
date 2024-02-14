from django.shortcuts import render, redirect
from django.template import TemplateDoesNotExist
from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib import messages
from .models import *
import re

def welcome(request) :
    return render(request, 'calc/index.html')

def main(request) :
    notice = Notice.objects.all().order_by('-date')

    if request.user.is_authenticated :
        area = Profile.objects.get(user__username=request.user.username)
        datas = {
            'area': area,
            'notice' : notice,
        }
        return render(request, "calc/main.html", datas)
    else :
        datas = {
            'notice' : notice,
        }
        return render(request, "calc/main.html")
    

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

def area_change(request) :
    if request.user.is_authenticated:
        area = Profile.objects.get(user__username=request.user.username)

        if request.method == "POST" :
            area.area = request.POST['area_change']
            area.save()
            redirect("calc:area_change")
        
        datas = {
            'area' : area,
        }
        return render(request, "calc/area_change.html", datas)
    
    else :
        return render(request, "calc/area_change.html")
    
def error(request):
    area = Profile.objects.get(user__username=request.user.username)
    datas ={
        'area' : area
    }
    return render(request, "calc/error.html", datas)


def suggestion(request) :
    if request.user.is_authenticated:
        area = Profile.objects.get(user__username=request.user.username)

        if request.method == "POST" :
            user = User.objects.get(username = request.user.username)
            content = request.POST['content']

            if 'imgfile' in request.FILES :
                savedata = Suggestion(user=user, content=content, file=request.FILES.get('imgfile'))
                savedata.save()
                messages.success(request, "성공")
            else :
                savedata = Suggestion(user=user, content=content)
                savedata.save()
                messages.success(request, "성공")

        datas ={
            'area' : area
        }
        return render(request, 'calc/suggestion.html', datas)

    

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
        return render(request, "calc/common/common.html")

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
            if request.POST["career_memo"] != '' :
                editdata.career_memo = request.POST["career_memo"]
            editdata.save()
            totaldata = Profile.objects.get(user__username = request.user.username)
            totaldata.point_cc = float(request.POST['hidden_total'])
            totaldata.save()
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
    
    else: 
        return render(request, "calc/common/common_career.html")

def common_workperformance(request) :
    if request.user.is_authenticated :

        if request.method == "POST" :
            editdata = Common_WorkPerformance.objects.get(user__username = request.user.username)
            if request.POST['wp_late_1'] != '' :
                editdata.wp_late_1 = request.POST['wp_late_1']
            else :
                editdata.wp_late_1 = 0
            if request.POST['wp_late_2'] != '' :
                editdata.wp_late_2 = request.POST['wp_late_2']
            else :
                editdata.wp_late_2 = 0
            if request.POST['wp_late_3'] != '' :
                editdata.wp_late_3 = request.POST['wp_late_3']
            else :
                editdata.wp_late_3 = 0
            if request.POST['wp_late_4'] != '' :
                editdata.wp_late_4 = request.POST['wp_late_4']
            else :
                editdata.wp_late_4 = 0
            if request.POST['wp_late_5'] != '' :
                editdata.wp_late_5 = request.POST['wp_late_5']
            else :
                editdata.wp_late_5 = 0
            editdata.wp_memo = request.POST['wp_memo']
            editdata.save()
            totaldata = Profile.objects.get(user__username = request.user.username)
            totaldata.point_cw = float(request.POST['hidden_total'])
            totaldata.save()
            return redirect("calc:cw")

        area = Profile.objects.get(user__username=request.user.username)
        try :
            point = Common_WorkPerformance.objects.get(user__username=request.user.username)
        except :
            user = User.objects.get(username=request.user.username)
            Common_WorkPerformance.objects.create(user=user)
            point = Common_WorkPerformance.objects.get(user__username=request.user.username)
        datas = {
            'area' : area,
            'point' : point,
        }
        return render(request, "calc/common/common_wp.html", datas)
    
    else:
        return render(request, "calc/common/common_wp.html")

def common_training(request) :
    if request.user.is_authenticated :

        if request.method == "POST" :
            editdata = Common_Training.objects.get(user__username = request.user.username)
            editdata.grade1teacher_result = request.POST["grade1teacher_result"]
            editdata.grade1teacher_memo = request.POST["grade1teacher_memo"]
            editdata.training_first = request.POST["training_first"]
            editdata.training_second = request.POST["training_second"]
            editdata.training_memo = request.POST["training_memo"]
            editdata.research_contest_point = request.POST["research_contest_point"]
            editdata.degree_point = request.POST["degree_point"]
            editdata.research_memo = request.POST["research_memo"]
            editdata.save()
            totaldata = Profile.objects.get(user__username = request.user.username)
            totaldata.point_ct = float(request.POST['hidden_total'])
            totaldata.save()
            return redirect("calc:ct")
        
        area = Profile.objects.get(user__username=request.user.username)
        try :
            point = Common_Training.objects.get(user__username=request.user.username)
        except :
            user = User.objects.get(username=request.user.username)
            Common_Training.objects.create(user=user)
            point = Common_Training.objects.get(user__username=request.user.username)
        datas = {
            'area' : area,
            'point' : point,
        }
        return render(request, "calc/common/common_training.html", datas)
    
    else :
        return render(request, "calc/common/common_training.html")











def area(request) :
    if request.user.is_authenticated :
        area = Profile.objects.get(user__username=request.user.username)
        
        datas = {
            'area' : area,
        }
        return render(request, "calc/area/area.html", datas)
    
    return render(request, "calc/area/area.html")



def area_common(request, areaname) : 
    if request.user.is_authenticated :
        if request.method == "POST" :
            editdata = Area_Common.objects.get(user__username=request.user.username)
            editdata.area = areaname
            editdata.research_school_year = request.POST["research_school_year"]
            editdata.research_school_month = request.POST["research_school_month"]
            editdata.research_school_memo = request.POST["research_school_memo"]
            editdata.foreign_school_year = request.POST["foreign_school_year"]
            editdata.foreign_school_month = request.POST["foreign_school_month"]
            editdata.foreign_school_memo = request.POST["foreign_school_memo"]
            editdata.lecture1_point = request.POST["lecture1_point"]
            editdata.lecture2_point = request.POST["lecture2_point"]
            editdata.lecture3_point = request.POST["lecture3_point"]
            editdata.lecture4_point = request.POST["lecture4_point"]
            editdata.lecture5_point = request.POST["lecture5_point"]
            editdata.lecture6_point = request.POST["lecture6_point"]
            editdata.lecture7_point = request.POST["lecture7_point"]
            editdata.lecture8_point = request.POST["lecture8_point"]
            editdata.lecture9_point = request.POST["lecture9_point"]
            editdata.lecture10_point = request.POST["lecture10_point"]
            editdata.lecture_memo = request.POST["lecture_memo"]
            editdata.violence_count = request.POST["violence_count"]
            editdata.violence_memo = request.POST["violence_memo"]
            editdata.save()
            total_editdata = Profile.objects.get(user__username=request.user.username)
            total_editdata.point_ac = float(request.POST["hidden_total"])
            total_editdata.save()

            return redirect(f'../{total_editdata.area}/common')
        
        area = Profile.objects.get(user__username=request.user.username)
        try:
            point = Area_Common.objects.get(user__username=request.user.username)
            return render(request, f'calc/area/{areaname}/common.html', {'area' : area, 'point' : point})
        except TemplateDoesNotExist :
            return redirect("calc:error")            
        except : 
            user = User.objects.get(username=request.user.username)
            Area_Common.objects.create(user=user)
            point = Area_Common.objects.get(user__username=request.user.username)

        datas = {
            'area' : area,
            'point' : point,
        }
        return render(request, f'calc/area/{areaname}/common.html', datas)
    
    else :
        return render(request, f'calc/area/{areaname}/common.html')
    



def area_diff(request, areaname) :
    if request.user.is_authenticated :
        area = Profile.objects.get(user__username=request.user.username)
        datas = {
            'area' : area,
        }
        return render(request, f"calc/area/{areaname}/diff.html", datas)
    
    else :
        return render(request, f"calc/area/{areaname}/diff.html")
    

def area_refdata(request, areaname) :
    if request.user.is_authenticated :
        area = Profile.objects.get(user__username=request.user.username)
        datas = {
            'area' : area,
        }
        return render(request, f"calc/area/{areaname}/refdata.html", datas)