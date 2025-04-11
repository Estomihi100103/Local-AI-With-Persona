from django.db import models
from django.contrib.auth.models import User
from persona.models import Persona

# Create your models here.
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    persona = models.ForeignKey(Persona, on_delete=models.SET_NULL, null=True, blank=True)
    nim = models.CharField(max_length=20, unique=True)  
    gpa = models.FloatField(null=True, blank=True)
    study_program = models.CharField(max_length=100, null=True, blank=True)
    angkatan = models.IntegerField(null=True, blank=True)
    get_course_programming = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s profile"