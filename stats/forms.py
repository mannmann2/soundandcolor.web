from django import forms
from .models import *

# from django.contrib.auth.forms import

class LoginForm(forms.Form):
    username = forms.CharField(max_length=20)
    password = forms.CharField(widget=forms.PasswordInput())
