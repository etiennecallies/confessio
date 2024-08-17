import os

from django.core.mail import send_mail, BadHeaderError
from django.shortcuts import render, redirect

from home.forms.captcha_form import CaptchaForm


def contact(request, message=None):
    if request.method == "GET":
        form = CaptchaForm()
        return render(request, 'pages/contact.html',
                      {'message': message, 'form': form})
    else:
        form = CaptchaForm(request.POST)
        if not form.is_valid():
            print(form.errors)
            return redirect("contact_with_message", message='failure')

        name = request.POST.get('name')
        from_email = request.POST.get('email')
        message = request.POST.get('message')
        email_body = f"{from_email}\n{name}\n\n{message}"
        subject = f'New message from {name} on confessio'
        try:
            send_mail(subject,
                      email_body,
                      None,  # Default to DEFAULT_FROM_EMAIL
                      [os.environ.get('CONTACT_EMAIL')])
        except BadHeaderError as e:
            print(e)
            return redirect("contact_with_message", message='failure')
        return redirect("contact_with_message", message='success')