import os
from django.utils.translation import gettext

from django.core.mail import send_mail, BadHeaderError
from django.http import HttpResponseBadRequest
from django.shortcuts import render, redirect

from home.forms.captcha_form import CaptchaForm
from home.services.page_url_service import quote_path, unquote_path


def contact(request, message=None, email=None, name_text=None, message_text=None):
    if request.method == "GET":
        form = CaptchaForm()
        return render(request, 'pages/contact.html',
                      {'message': message, 'form': form,
                       'name_text': unquote_path(name_text or ''),
                       'email': email or '',
                       'message_text': unquote_path(message_text or ''),
                       'meta_title': gettext('contactPageTitle'),
                       })
    else:
        name = request.POST.get('name')
        from_email = request.POST.get('email')
        message = request.POST.get('message')

        if not name or not from_email or not message:
            return HttpResponseBadRequest("Missing required fields")

        form = CaptchaForm(request.POST)
        if not form.is_valid():
            print(form.errors)
            name_text = quote_path(name)
            message_text = quote_path(message)
            return redirect("contact_failure", message='failure',
                            name_text=name_text, email=from_email, message_text=message_text)

        email_body = f"{from_email}\n{name}\n\n{message}"
        subject = f'New message from {name} on confessio'
        try:
            send_mail(subject,
                      email_body,
                      None,  # Default to DEFAULT_FROM_EMAIL
                      [os.environ.get('CONTACT_EMAIL')])
        except BadHeaderError as e:
            print(e)
            name_text = quote_path(name)
            message_text = quote_path(message)
            return redirect("contact_failure", message='failure',
                            name_text=name_text, email=from_email, message_text=message_text)
        return redirect("contact_success", message='success')
