import os
from urllib.parse import quote, unquote

from django.core.mail import send_mail, BadHeaderError
from django.shortcuts import render, redirect

from home.forms.captcha_form import CaptchaForm


def contact(request, message=None, name=None, email=None, message_text=None):
    if request.method == "GET":
        form = CaptchaForm()
        return render(request, 'pages/contact.html',
                      {'message': message, 'form': form,
                       'name': name or '',
                       'email': email or '',
                       'message_text': unquote(message_text or '')
                       })
    else:
        name = request.POST.get('name')
        from_email = request.POST.get('email')
        message = request.POST.get('message')

        form = CaptchaForm(request.POST)
        if not form.is_valid():
            print(form.errors)
            message_text = quote(message) if message else None
            return redirect("contact_failure", message='failure',
                            name=name, email=from_email, message_text=message_text)

        email_body = f"{from_email}\n{name}\n\n{message}"
        subject = f'New message from {name} on confessio'
        try:
            send_mail(subject,
                      email_body,
                      None,  # Default to DEFAULT_FROM_EMAIL
                      [os.environ.get('CONTACT_EMAIL')])
        except BadHeaderError as e:
            print(e)
            message_text = quote(message)
            return redirect("contact_failure", message='failure',
                            name=name, email=from_email, message_text=message_text)
        return redirect("contact_success", message='success')
