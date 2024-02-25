from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model) :
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    area = models.TextField()
    point_cc = models.DecimalField(max_digits=100, decimal_places=8, default=0, blank=True, null=True)
    point_cw = models.DecimalField(max_digits=100, decimal_places=8, default=0, blank=True, null=True)
    point_ct = models.DecimalField(max_digits=100, decimal_places=8, default=0, blank=True, null=True)
    point_ac = models.DecimalField(max_digits=100, decimal_places=8, default=0, blank=True, null=True)
    point_ad = models.DecimalField(max_digits=100, decimal_places=8, default=0, blank=True, null=True)
    total = models.DecimalField(max_digits=100, decimal_places=8, default=0, blank=True, null=True)

    def __str__(self) : 
        return f'{self.user}({self.area}) - {self.point_cc}/{self.point_cw}/{self.point_ct}/{self.point_ac}/{self.point_ad} - 총 {self.total}'


class Notice(models.Model) :
    title = models.TextField()
    content = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self) : 
        return f'{self.title} - {self.date}'



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

    def __str__(self) : 
        return f'{self.user} - {self.content}, {self.date}'


class Common_Career(models.Model) :
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    career_year = models.IntegerField(default=0, blank=True, null=True)
    career_month = models.IntegerField(default=0, blank=True, null=True)
    career_memo = models.TextField(default=0, blank=True, null=True)

    def __str__(self) : 
        return f'{self.user}'

class Common_WorkPerformance(models.Model) :
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    wp_late_1 = models.IntegerField(default=0, blank=True, null=True)
    wp_late_2 = models.IntegerField(default=0, blank=True, null=True)
    wp_late_3 = models.IntegerField(default=0, blank=True, null=True)
    wp_late_4 = models.IntegerField(default=0, blank=True, null=True)
    wp_late_5 = models.IntegerField(default=0, blank=True, null=True)
    wp_memo = models.TextField(default=0, blank=True, null=True)

    def __str__(self) : 
        return f'{self.user}'

class Common_Training(models.Model) :
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    grade1teacher_result = models.IntegerField(default=0)
    grade1teacher_memo = models.TextField(default='', blank=True, null=True)
    training_first = models.IntegerField(default=0)
    training_second = models.IntegerField(default=0)
    training_memo = models.TextField(default='', blank=True, null=True)
    research_contest_point = models.IntegerField(default=0)
    degree_point = models.IntegerField(default=0)
    research_memo = models.TextField(default='', blank=True, null=True)

    def __str__(self) : 
        return f'{self.user}'





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

    def __str__(self) : 
        return f'{self.user}({self.area})'



class Area_Diff_Jeonnam(models.Model) :
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    island_ga_year = models.IntegerField(default=0)
    island_ga_month = models.IntegerField(default=0)
    island_na_year = models.IntegerField(default=0)
    island_na_month = models.IntegerField(default=0)
    island_da_year = models.IntegerField(default=0)
    island_da_month = models.IntegerField(default=0)
    island_ra_year = models.IntegerField(default=0)
    island_ra_month = models.IntegerField(default=0)
    mountain_ga_year = models.IntegerField(default=0)
    mountain_ga_month = models.IntegerField(default=0)
    mountain_na_year = models.IntegerField(default=0)
    mountain_na_month = models.IntegerField(default=0)
    mountain_da_year = models.IntegerField(default=0)
    mountain_da_month = models.IntegerField(default=0)
    mountain_ra_year = models.IntegerField(default=0)
    mountain_ra_month = models.IntegerField(default=0)
    outside_school_memo = models.TextField(default='')

    rural_1_year = models.IntegerField(default=0)
    rural_1_month = models.IntegerField(default=0)
    rural_2_year = models.IntegerField(default=0)
    rural_2_month = models.IntegerField(default=0)
    rural_3_year = models.IntegerField(default=0)
    rural_3_month = models.IntegerField(default=0)
    rural_add_month = models.IntegerField(default=0)
    rural_memo = models.TextField(default='')

    high_teacher_year = models.IntegerField(default=0)
    high_teacher_add_year = models.IntegerField(default=0)
    high_teacher_memo = models.TextField(default='')

    research_school_area_year = models.IntegerField(default=0)
    research_school_area_month = models.IntegerField(default=0)
    research_school_area2_year = models.IntegerField(default=0)
    research_school_area2_month = models.IntegerField(default=0)
    research_school_area_memo = models.TextField(default='')

    double_class_year = models.IntegerField(default=0)
    double_class_month = models.IntegerField(default=0)
    cyber_year = models.IntegerField(default=0)
    cyber_month = models.IntegerField(default=0)
    genius_year = models.IntegerField(default=0)
    genius_month = models.IntegerField(default=0)
    intern_month = models.IntegerField(default=0)
    intern_day = models.IntegerField(default=0)
    scout_month = models.IntegerField(default=0)
    competition_gold_point = models.IntegerField(default=0)
    competition_silver_point = models.IntegerField(default=0)
    competition_bronze_point = models.IntegerField(default=0)
    cert_1_point = models.IntegerField(default=0)
    cert_2_point = models.IntegerField(default=0)
    cert_3_point = models.IntegerField(default=0)
    edupower_count = models.IntegerField(default=0)
    openclass_add_count = models.IntegerField(default=0)
    high_teacher_add_plus_count = models.IntegerField(default=0)
    etc_memo = models.TextField(default='')

    openclass_count = models.IntegerField(default=0)
    openclass_memo = models.TextField(default='')

    living_solo_month = models.IntegerField(default=0)
    living_solo_day = models.IntegerField(default=0)
    living_family_month = models.IntegerField(default=0)
    living_family_day = models.IntegerField(default=0)
    living_memo = models.TextField(default='')

    def __str__(self) : 
        return f'{self.user}'

