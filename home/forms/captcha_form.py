from captcha.fields import CaptchaField
from django import forms


class CaptchaForm(forms.Form):
    captcha = CaptchaField()
