import datetime 
import requests

from django.db import models
from django.utils import timezone

# class Question(models.Model):

# 	question_text = models.CharField(max_length=200)
# 	pub_date = models.DateTimeField('date published')

# 	def __str__(self):
# 		return self.question_text

# 	def was_published_recently(self):
# 		return self.pub_date >= timezone.now() - datetime.timedelta(days=1)

# class Choice(models.Model):

# 	question = models.ForeignKey(Question, on_delete=models.CASCADE)
# 	choice_text = models.CharField(max_length=200)
# 	votes = models.IntegerField(default=0)

# 	def __str__(self):
# 		return self.choice_text


# class Artist(models.Model):
# 	artist_name = models.CharField(max_length=200)

# 	def __str__(self):
# 		return self.artist_name


class User(models.Model):

	username=models.CharField(max_length=32, blank=True)
	email = models.EmailField(max_length=254, blank=True)
	name = models.CharField(max_length=30, blank=True)
	access_token = models.CharField(max_length = 400)
	refresh_token = models.CharField(max_length = 400)
	token = models.CharField(max_length = 400, blank=True)

	def __str__(self):
		return self.username

