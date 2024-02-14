from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model) :
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    area = models.TextField()
    point_cc = models.DecimalField(max_digits=100, decimal_places=8, blank=True, null=True)
    point_cw = models.DecimalField(max_digits=100, decimal_places=8, blank=True, null=True)
    point_ct = models.DecimalField(max_digits=100, decimal_places=8, blank=True, null=True)
    point_ac = models.DecimalField(max_digits=100, decimal_places=8, blank=True, null=True)
    point_as = models.DecimalField(max_digits=100, decimal_places=8, blank=True, null=True)
    total = models.DecimalField(max_digits=100, decimal_places=8, blank=True, null=True)


class Notice(models.Model) :
    title = models.TextField()
    content = models.TextField()
    date = models.DateTimeField(auto_now_add=True)


class Manual(models.Model) :
    area = models.TextField()
    upload_date = models.DateTimeField(auto_now_add=True)
    manual = models.FileField(upload_to="manuals/")
    uploader = models.TextField()


class Suggestion(models.Model) :
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(default='')
    file = models.FileField(upload_to='suggestion/', null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)


class Common_Career(models.Model) :
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    career_year = models.IntegerField(blank=True, null=True)
    career_month = models.IntegerField(blank=True, null=True)
    career_memo = models.TextField(blank=True, null=True)

class Common_WorkPerformance(models.Model) :
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    wp_late_1 = models.IntegerField(blank=True, null=True)
    wp_late_2 = models.IntegerField(blank=True, null=True)
    wp_late_3 = models.IntegerField(blank=True, null=True)
    wp_late_4 = models.IntegerField(blank=True, null=True)
    wp_late_5 = models.IntegerField(blank=True, null=True)
    wp_memo = models.TextField(blank=True, null=True)

class Common_Training(models.Model) :
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    grade1teacher_result = models.IntegerField(default=0)
    grade1teacher_memo = models.TextField(blank=True, null=True)
    training_first = models.IntegerField(default=0)
    training_second = models.IntegerField(default=0)
    training_memo = models.TextField(blank=True, null=True)
    research_contest_point = models.IntegerField(default=0)
    degree_point = models.IntegerField(default=0)
    research_memo = models.TextField(blank=True, null=True)





class Area_Common(models.Model) :
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    area = models.TextField()
    research_school_year = models.IntegerField(default=0)
    research_school_month = models.IntegerField(default=0)
    research_school_memo = models.TextField(default='')
    foreign_school_year = models.IntegerField(default=0)
    foreign_school_month = models.IntegerField(default=0)
    foreign_school_memo = models.TextField(default='')
    lecture1_point = models.IntegerField(default=0)
    lecture2_point = models.IntegerField(default=0)
    lecture3_point = models.IntegerField(default=0)
    lecture4_point = models.IntegerField(default=0)
    lecture5_point = models.IntegerField(default=0)
    lecture6_point = models.IntegerField(default=0)
    lecture7_point = models.IntegerField(default=0)
    lecture8_point = models.IntegerField(default=0)
    lecture9_point = models.IntegerField(default=0)
    lecture10_point = models.IntegerField(default=0)
    lecture_memo = models.TextField(default='')
    violence_count = models.IntegerField(default=0)
    violence_memo = models.TextField(default='')



class area_area(models.Model) :
    user = models.ForeignKey(User, on_delete=models.CASCADE)



