from django.db import models

# Create your models here.
 class employees(models.Model):
 	fristname=models.charField(max_length=10)
 	lastname=models.charField(max_length=10)
 	emp_id=models.IntergerField()

 	def __str__(self):
 		return self.fristname,  