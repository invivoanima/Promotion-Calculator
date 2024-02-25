from django.shortcuts import render, redirect
from django.template import TemplateDoesNotExist
from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib import messages
from django.apps import apps
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

            messages.success(request, 'registersuccess')
            return render(request, 'calc/login.html')
        
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
            if request.POST["grade1teacher_result"] != '' :
                editdata.grade1teacher_result = request.POST["grade1teacher_result"]
            else :
                editdata.grade1teacher_result = 0
            editdata.grade1teacher_memo = request.POST["grade1teacher_memo"]

            if request.POST["training_first"] != '' :
                editdata.training_first = request.POST["training_first"]
            else :
                editdata.training_first = 0
            if request.POST["training_second"] != '' :
                editdata.training_second = request.POST["training_second"]
            else :
                editdata.training_second = 0
            editdata.training_memo = request.POST["training_memo"]
            if request.POST["research_contest_point"] != '' :
                editdata.research_contest_point = request.POST["research_contest_point"]
            else :
                editdata.research_contest_point = 0
            if request.POST["degree_point"] != '' :
                editdata.degree_point = request.POST["degree_point"]
            else :
                editdata.degree_point = 0
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
            if request.POST["research_school_year"] != '' :
               editdata.research_school_year = request.POST["research_school_year"]
            else :
                editdata.research_school_year = 0
            if request.POST["research_school_month"] != '' :
               editdata.research_school_month = request.POST["research_school_month"]
            else :
                editdata.research_school_month = 0
            editdata.research_school_memo = request.POST["research_school_memo"]
            if request.POST["foreign_school_year"] != '' :
                editdata.foreign_school_year = request.POST["foreign_school_year"]
            else :
                editdata.foreign_school_year = 0
            if request.POST["foreign_school_month"] != '' :
                editdata.foreign_school_month = request.POST["foreign_school_month"]
            else :
                editdata.foreign_school_month = 0
            editdata.foreign_school_memo = request.POST["foreign_school_memo"]
            if request.POST["lecture1_point"] != '' :
                editdata.lecture1_point = request.POST["lecture1_point"]
            else :
                editdata.lecture1_point = 0
            if request.POST["lecture2_point"] != '' :
                editdata.lecture2_point = request.POST["lecture2_point"]
            else :
                editdata.lecture2_point = 0
            if request.POST["lecture3_point"] != '' :
                editdata.lecture3_point = request.POST["lecture3_point"]
            else :
                editdata.lecture3_point = 0
            if request.POST["lecture4_point"] != '' :
                editdata.lecture4_point = request.POST["lecture4_point"]
            else :
                editdata.lecture4_point = 0
            if request.POST["lecture5_point"] != '' :
                editdata.lecture5_point = request.POST["lecture5_point"]
            else :
                editdata.lecture5_point = 0
            if request.POST["lecture6_point"] != '' :
                editdata.lecture6_point = request.POST["lecture6_point"]
            else :
                editdata.lecture6_point = 0
            if request.POST["lecture7_point"] != '' :
                editdata.lecture7_point = request.POST["lecture7_point"]
            else :
                editdata.lecture7_point = 0
            if request.POST["lecture8_point"] != '' :
                editdata.lecture8_point = request.POST["lecture8_point"]
            else :
                editdata.lecture8_point = 0
            if request.POST["lecture9_point"] != '' :
                editdata.lecture9_point = request.POST["lecture9_point"]
            else :
                editdata.lecture9_point = 0
            if request.POST["lecture10_point"] != '' :
                editdata.lecture10_point = request.POST["lecture10_point"]
            else :
                editdata.lecture10_point = 0
            editdata.lecture_memo = request.POST["lecture_memo"]
            if request.POST["violence_count"] != '' :
                editdata.violence_count = request.POST["violence_count"]
            else :
                editdata.violence_count = 0
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
        
        try:
            model_loaded = apps.get_model('calc', f'Area_Diff_{areaname}')      
        except LookupError :
            return redirect("calc:error")            
        except : 
            user = User.objects.get(username=request.user.username)
            model_loaded.objects.create(user=user)
            model_loaded = apps.get_model('calc', f'Area_Diff_{areaname}')  

        datas = {
                'area' : area,
            }
        
        if areaname == 'jeonnam' :
            user = User.objects.get(username=request.user.username)
            point, created = Area_Diff_Jeonnam.objects.get_or_create(user__username=request.user.username, defaults={'user':user})
            grade1data, created = Common_Training.objects.get_or_create(user__username=request.user.username, defaults={'user':user})
            datas["grade1data"] = grade1data
            datas["grade1translated"] = (100 - grade1data.grade1teacher_result)*0.025
            datas["point"] = point

            if request.method == 'POST' :
                point = model_loaded.objects.get(user__username=request.user.username)
                if request.POST["island_ga_year"] != '' :
                    point.island_ga_year = request.POST["island_ga_year"]
                else :
                    point.island_ga_year = 0
                if request.POST["island_ga_month"] != '' :
                    point.island_ga_month = request.POST["island_ga_month"]
                else :
                    point.island_ga_month = 0
                if request.POST["island_na_year"] != '' :
                    point.island_na_year = request.POST["island_na_year"]
                else :
                    point.island_na_year = 0
                if request.POST["island_na_month"] != '' :
                    point.island_na_month = request.POST["island_na_month"]
                else :
                    point.island_na_month = 0
                if request.POST["island_da_year"] != '' :
                    point.island_da_year = request.POST["island_da_year"]
                else :
                    point.island_da_year = 0
                if request.POST["island_da_month"] != '' :
                    point.island_da_month = request.POST["island_da_month"]
                else :
                    point.island_da_month = 0
                if request.POST["island_ra_year"] != '' :
                   point.island_ra_year = request.POST["island_ra_year"]
                else :
                    point.island_ra_year = 0
                if request.POST["island_ra_month"] != '' :
                    point.island_ra_month = request.POST["island_ra_month"]
                else :
                    point.island_ra_month = 0
                if request.POST["mountain_ga_year"] != '' :
                    point.mountain_ga_year = request.POST["mountain_ga_year"]
                else :
                    point.mountain_ga_year = 0
                if request.POST["mountain_ga_month"] != '' :
                    point.mountain_ga_month = request.POST["mountain_ga_month"]
                else :
                    point.mountain_ga_month = 0
                if request.POST["mountain_na_year"] != '' :
                    point.mountain_na_year = request.POST["mountain_na_year"]
                else :
                    point.mountain_na_year = 0
                if request.POST["mountain_na_month"] != '' :
                    point.mountain_na_month = request.POST["mountain_na_month"]
                else :
                    point.mountain_na_month = 0
                if request.POST["mountain_da_year"] != '' :
                    point.mountain_da_year = request.POST["mountain_da_year"]
                else :
                    point.mountain_da_year = 0
                if request.POST["mountain_da_month"] != '' :
                    point.mountain_da_month = request.POST["mountain_da_month"]
                else :
                    point.mountain_da_month = 0
                if request.POST["mountain_ra_year"] != '' :
                    point.mountain_ra_year = request.POST["mountain_ra_year"]
                else :
                    point.mountain_ra_year = 0
                if request.POST["mountain_ra_month"] != '' :
                    point.mountain_ra_month = request.POST["mountain_ra_month"]
                else :
                    point.mountain_ra_month = 0
                point.outside_school_memo = request.POST["outside_school_memo"]

                if request.POST["rural_1_year"] != '' :
                    point.rural_1_year = request.POST["rural_1_year"]
                else : 
                    point.rural_1_year = 0
                if request.POST["rural_1_month"] != '' :
                    point.rural_1_month = request.POST["rural_1_month"]
                else : 
                    point.rural_1_month = 0
                if request.POST["rural_2_year"] != '' :
                    point.rural_2_year = request.POST["rural_2_year"]
                else : 
                    point.rural_2_year = 0
                if request.POST["rural_2_month"] != '' :
                    point.rural_2_month = request.POST["rural_2_month"]
                else : 
                    point.rural_2_month = 0
                if request.POST["rural_3_year"] != '' :
                    point.rural_3_year = request.POST["rural_3_year"]
                else : 
                    point.rural_3_year = 0
                if request.POST["rural_3_month"] != '' :
                    point.rural_3_month = request.POST["rural_3_month"]
                else : 
                    point.rural_3_month = 0
                if request.POST["rural_add_month"] != '' :
                    point.rural_add_month = request.POST["rural_add_month"]
                else : 
                    point.rural_add_month = 0
                point.rural_memo = request.POST["rural_memo"]

                if request.POST["high_teacher_year"] != '' :
                    point.high_teacher_year = request.POST["high_teacher_year"]
                else :
                    point.high_teacher_year = 0
                if request.POST["high_teacher_add_year"] != '' :
                    point.high_teacher_add_year = request.POST["high_teacher_add_year"]
                else :
                    point.high_teacher_year = 0
                point.high_teacher_memo = request.POST["high_teacher_memo"]

                if request.POST["research_school_area_year"] != '' :
                    point.research_school_area_year = request.POST["research_school_area_year"]
                else: 
                    point.research_school_area_year = 0
                if request.POST["research_school_area_month"] != '' :
                    point.research_school_area_month = request.POST["research_school_area_month"]
                else : 
                    point.research_school_area_month = 0
                if request.POST["research_school_area2_year"] != '' :
                    point.research_school_area2_year = request.POST["research_school_area2_year"]
                else :
                    point.research_school_area2_year = 0
                if request.POST["research_school_area2_month"] != '' :
                    point.research_school_area2_month = request.POST["research_school_area2_month"]
                else :
                    point.research_school_area2_month = 0
                point.research_school_area_memo = request.POST["research_school_area_memo"]

                if request.POST["double_class_year"] != '' :
                    point.double_class_year = request.POST["double_class_year"]
                else :
                    point.double_class_year = 0
                if request.POST["double_class_month"] != '' :
                    point.double_class_month = request.POST["double_class_month"]
                else :
                    point.double_class_month = 0
                if request.POST["cyber_year"] != '' :
                    point.cyber_year = request.POST["cyber_year"]
                else :
                    point.cyber_year = 0
                if request.POST["cyber_month"] != '' :
                    point.cyber_month = request.POST["cyber_month"]
                else :
                    point.cyber_month = 0
                if request.POST["genius_year"] != '' :
                    point.genius_year = request.POST["genius_year"]
                else :
                    point.genius_year = 0
                if request.POST["genius_month"] != '' :
                    point.genius_month = request.POST["genius_month"]
                else :
                    point.genius_month = 0
                if request.POST["intern_month"] != '' :
                    point.intern_month = request.POST["intern_month"]
                else :
                    point.intern_month = 0
                if request.POST["intern_day"] != '' :
                    point.intern_day = request.POST["intern_day"]
                else :
                    point.intern_day = 0
                if request.POST["scout_month"] != '' :
                    point.scout_month = request.POST["scout_month"]
                else :
                    point.scout_month = 0
                if request.POST["competition_gold_point"] != '' :
                    point.competition_gold_point = request.POST["competition_gold_point"]
                else :
                    point.competition_gold_point = 0
                if request.POST["competition_silver_point"] != '' :
                    point.competition_silver_point = request.POST["competition_silver_point"]
                else :
                    point.competition_silver_point = 0
                if request.POST["competition_bronze_point"] != '' :
                    point.competition_bronze_point = request.POST["competition_bronze_point"]
                else :
                    point.competition_bronze_point = 0
                if request.POST["cert_1_point"] != '' :
                    point.cert_1_point = request.POST["cert_1_point"]
                else :
                    point.cert_1_point = 0
                if request.POST["cert_2_point"] != '' :
                    point.cert_2_point = request.POST["cert_2_point"]
                else :
                    point.cert_2_point = 0
                if request.POST["cert_3_point"] != '' :
                    point.cert_3_point = request.POST["cert_3_point"]
                else :
                    point.cert_3_point = 0
                if request.POST["edupower_count"] != '' :
                    point.edupower_count = request.POST["edupower_count"]
                else :
                    point.edupower_count = 0
                if request.POST["openclass_add_count"] != '' :
                    point.openclass_add_count = request.POST["openclass_add_count"]
                else :
                    point.openclass_add_count = 0
                if request.POST["high_teacher_add_plus_count"] != '' :
                    point.high_teacher_add_plus_count = request.POST["high_teacher_add_plus_count"]
                else :
                    point.high_teacher_add_plus_count = 0
                point.etc_memo = request.POST["etc_memo"]

                if request.POST["openclass_count"] != '' :
                    point.openclass_count = request.POST["openclass_count"]
                else :
                    point.openclass_count = 0
                point.openclass_memo = request.POST["openclass_memo"]

                if request.POST["living_solo_month"] != '' :
                    point.living_solo_month = request.POST["living_solo_month"]
                else :
                    point.living_solo_month = 0
                if request.POST["living_solo_day"] != '' :
                    point.living_solo_day = request.POST["living_solo_day"]
                else :
                    point.living_solo_day = 0
                if request.POST["living_family_month"] != '' :
                    point.living_family_month = request.POST["living_family_month"]
                else :
                    point.living_family_month = 0
                if request.POST["living_family_day"] != '' :
                    point.living_family_day = request.POST["living_family_day"]
                else :
                    point.living_family_day = 0
                point.living_memo = request.POST["living_memo"]
                point.save()

                total_editdata = Profile.objects.get(user__username=request.user.username)
                total_editdata.point_ad = float(request.POST["hidden_total"])
                total_editdata.save()

                return redirect(f'/area/{areaname}/diff/')

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