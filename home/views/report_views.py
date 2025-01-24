from django.http import HttpResponseNotFound
from django.shortcuts import render

from home.models import Website


def report(request, website_uuid):
    if request.method == "GET":
        try:
            website = Website.objects.get(uuid=website_uuid)
        except Website.DoesNotExist:
            return HttpResponseNotFound(f'Website with uuid {website_uuid} not found')

        website_churches = {}
        for parish in website.parishes.all():
            for church in parish.churches.all():
                website_churches.setdefault(website.uuid, []).append(church)

        return render(request, 'pages/report.html', {
            'noindex': True,
            'website': website,
            'website_churches': website_churches,
        })
    else:
        raise NotImplementedError
        # name = request.POST.get('name')
        # from_email = request.POST.get('email')
        # message = request.POST.get('message')
        #
        # form = CaptchaForm(request.POST)
        # if not form.is_valid():
        #     print(form.errors)
        #     message_text = quote(message) if message else None
        #     return redirect("contact_failure", message='failure',
        #                     name=name, email=from_email, message_text=message_text)
        #
        # email_body = f"{from_email}\n{name}\n\n{message}"
        # subject = f'New message from {name} on confessio'
        # try:
        #     send_mail(subject,
        #               email_body,
        #               None,  # Default to DEFAULT_FROM_EMAIL
        #               [os.environ.get('CONTACT_EMAIL')])
        # except BadHeaderError as e:
        #     print(e)
        #     message_text = quote(message)
        #     return redirect("contact_failure", message='failure',
        #                     name=name, email=from_email, message_text=message_text)
        # return redirect("contact_success", message='success')
