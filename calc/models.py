from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model) :
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    area = models.TextField()
    point_cc = models.DecimalField(max_digits=10, decimal_places=8, blank=True, null=True)
    point_cw = models.DecimalField(max_digits=10, decimal_places=8, blank=True, null=True)
    point_ct = models.DecimalField(max_digits=10, decimal_places=8, blank=True, null=True)
    point_ac = models.DecimalField(max_digits=10, decimal_places=8, blank=True, null=True)
    point_as = models.DecimalField(max_digits=10, decimal_places=8, blank=True, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=8, blank=True, null=True)


class Manual(models.Model) :
    area = models.TextField()
    upload_date = models.DateTimeField(auto_now_add=True)
    manual = models.FileField(upload_to="manuals/")
    uploader = models.TextField()


class Common_Career(models.Model) :
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    career_year = models.IntegerField(blank=True, null=True)
    career_month = models.IntegerField(blank=True, null=True)

class Common_WorkPerformance(models.Model) :
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    workperformance = models.TextField()

class Common_Training(models.Model) :
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    candidate = models.DecimalField(max_digits=10, decimal_places=8)
    qualification = models.DecimalField(max_digits=10, decimal_places=8)
    training = models.DecimalField(max_digits=10, decimal_places=8)
    competition_memo = models.TextField()
    competition_point = models.DecimalField(max_digits=10, decimal_places=8)


class Area_Common(models.Model) :
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    area = models.TextField()
    research_school_career = models.IntegerField()
    overseas_citizen_institution = models.IntegerField()
    training_year = models.IntegerField()
    school_violence = models.IntegerField()



