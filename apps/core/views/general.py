from django.shortcuts import render, redirect
from django.utils import timezone, translation
from django.core.mail import send_mail, BadHeaderError
from apps.core.models import Notice, Statistic, Service
from django.core.exceptions import SuspiciousOperation
from apps.core.backends import validate_recaptcha
import logging
import json


logger = logging.getLogger('sso')


# /main/
def main(request):
    current_time = timezone.now()
    services = Service.objects.filter(is_shown=True, icon__isnull=False)
    notice = Notice.objects.filter(valid_from__lte=current_time,
                                   valid_to__gt=current_time).first()

    return render(request, 'main.html', {'services': services, 'notice': notice})


# /lang/
def lang(request, code):
    if code not in ['en', 'ko']:
        return redirect('/')

    translation.activate(code)
    request.session[translation.LANGUAGE_SESSION_KEY] = code
    return redirect(request.META.get('HTTP_REFERER', '/'))


# /credits/
def credits(request):
    return render(request, 'credits.html')


# /terms/
def terms(request):
    return render(request, 'terms.html')


# /privacy/
def privacy(request):
    return render(request, 'privacy.html')


# /stats/
def stats(request):
    level = 0
    if request.user.is_authenticated():
        if request.user.is_staff:
            level = 2
        elif request.user.profile.sparcs_id:
            level = 1

    raw_stats = Statistic.objects.order_by('-time')
    if len(raw_stats) == 0:
        raw_stat = {}
    else:
        time = raw_stats[0].time
        raw_stat = json.loads(raw_stats[0].data)

    stat = []
    for name, value in raw_stat.iteritems():
        if name != 'all':
            service = Service.objects.get(name=name)
            if level < 1 and not service.is_shown:
                continue

        s = {}
        s['name'] = name
        s['alias'] = service.alias if name != 'all' else 'all'
        s.update(value)

        if name == 'all':
            stat.insert(0, s)
        else:
            stat.append(s)

    return render(request, 'stats.html', {'level': level, 'time': time, 'stat': stat})


# /help/
def help(request):
    return render(request, 'help.html')

# /contact/
def contact(request):
    name = ''
    email = ''
    subject = ''
    message = ''
    if request.method == 'POST':
        name = request.POST.get('name','')
        email = request.POST.get('email','')
        subject = request.POST.get('subject','')
        message = request.POST.get('message','')
        recipients = ['gogi@sparcs.org']

        result = validate_recaptcha(request.POST.get('g-recaptcha-response',''))

        if not result:
            return redirect('/')

        if name and email and message:
            try:
                contents = 'name :' + name + '\n' + 'message\n' + message
                send_mail(subject, contents, email, recipients)
            except ValueError:
                raise SuspiciousOperation()
            return redirect('/contact/thanks/')
    return render(request, 'contact.html',
            {'name': name, 'email': email, 'subject': subject, 'message':message})

