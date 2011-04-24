# Create your views here.
import datetime
import random
import hashlib

from django.template.loader import get_template
from django.template import Context, RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib import auth
from django.shortcuts import render_to_response, get_object_or_404
from django.core.mail import send_mail
from django.core.context_processors import csrf

from latex.models import UserProfile
from latex.forms import *

def home(request):
	site_template  = get_template('template.html')
	html = site_template.render(Context({}))
	return HttpResponse(html)


#User Registration

def register_user(request):
	if request.POST:
		new_data = request.POST.copy()
		form = RegistrationForm(new_data)
		
		valid_user = True
		
		for i in new_data.values():
			if i == "":
				return HttpResponse("Do not leave as blank")
				
		try:
			User.objects.get(username=str(form.data['user']))
			return HttpResponse("Username already taken.")
		except User.DoesNotExist:
			valid_user = False
			
		if form.is_valid() == False:
			return HttpResponse("Invalid Email ID")
			
		if valid_user==False and form.data['password1']==form.data['password2']:
			if len(form.data['password1']) < 6:
				return HttpResponse("Passwords should be atleast <br /> 6 characters in length")
			new_user = form.save()
			salt = hashlib.new('sha', str(random.random())).hexdigest()[:5]
			activation_key = hashlib.new('sha', salt+new_user.username).hexdigest()
			key_expires = datetime.datetime.today()+datetime.timedelta(2)
			new_profile = UserProfile(user=new_user, activation_key=activation_key, key_expires=key_expires, is_active=True)
			new_profile.save()
			
			return HttpResponse('User added successfully')
		else:
			return HttpResponse('Re-enter passwords again.')
			
	else:
		form = RegistrationForm()
		return render_to_response('register.html', {'form':form,}, context_instance=RequestContext(request))


#User login
def user_login(request):
	if request.GET:
		new_data = request.GET.copy()
		if new_data.has_key('logout'):
			auth.logout(request)
			return HttpResponse('True')
			
		user = str(new_data['username'])
		password = str(new_data['password'])
		user_session = auth.authenticate(username=user, password=password)
		
		if user_session:
			auth.login(request, user_session)
			return HttpResponse('True')
		else:
			return HttpResponse('False')

#Confirmation
def user_confirm(request, name, key):
	
	u = User.objects.get(username=name)
	if u.is_active:
		return render_response(request, 'user/confirm.html', {'actived':True})
	elif u.get_profile().activation_key == key:
		if u.get_profile().key_expires < datetime.datetime.today():
			u.delete()
			return render_response(request, 'user/confirm.html', {'key_expired':True})
		else:
			u.is_active = True
			u.save()
			return render_response(request, 'user/confirm.html', {'ok':True})


def lost_password(request):
	if request.method == 'POST':
		form = LostPasswordForm(request.POST)
		if form.is_valid():
			# generate new key and e-mail it to user
			salt = sha.new(str(random.random())).hexdigest()[8:]
			key = sha.new(salt).hexdigest()

			u = User.objects.get(username=form.cleaned_data['username'])
			lostpwd = LostPassword(user=u)
			lostpwd.key = key
			lostpwd.key_expires = datetime.datetime.today() + datetime.timedelta(1)
			lostpwd.save()

			# mail it
			email_dict = {
                    "SITE_NAME": 'LiveLaTeX',
                    'date': datetime.datetime.now(),
                    'ip': request.META['REMOTE_ADDR'],
                    'user': form.cleaned_data['username'],
                    'link': 'http://pardusman.pardus.org.tr/%s' % key,
                    }

			email_subject = _("%(SITE_NAME)s User Password") % SITE_NAME
			email_body = loader.get_template("mails/password.html").render(Context(email_dict))
			email_to = form.cleaned_data['email']

			send_mail(email_subject, email_body, DEFAULT_FROM_EMAIL, [email_to], fail_silently=True)
			return render_response(request, 'user/lostpassword_done.html')
		else:
			return render_response(request, 'user/lostpassword.html', {'form': form})
	else:
		form = LostPasswordForm()
		return render_response(request, 'user/lostpassword.html', {'form': form})


def change_password(request):
	u = request.user
	password_changed = False

	if request.method == 'POST':
		form = ChangePasswordForm(request.POST)
		form.user = u

	if form.is_valid() and len(form.cleaned_data['password']) > 0:
		u.set_password(form.cleaned_data['password'])
		u.save()
		password_changed = True
	else:
		form = ChangePasswordForm()


	return render_response(request, 'user/password.html', {
        "form": form,
        "password_changed": password_changed,
        })

def reset_password(request, key):
	if LostPassword.objects.count() == 0:
		return render_response(request, 'user/change_password.html', {'error': True, 'invalid': True})

	lostpwd = LostPassword.objects.get(key=key)
	if lostpwd.is_expired():
		lostpwd.delete()
		return render_response(request, 'user/change_password.html', {'error': True, 'expired': True})
	else:
		if request.method == 'POST':
			form = ResetPasswordForm(request.POST)
			if form.is_valid():
				u = User.objects.get(username=lostpwd.user.username)
				u.set_password(form.cleaned_data['password'])
				u.save()
				lostpwd.delete()
				return render_response(request, 'user/change_password_done.html', {'login_url': LOGIN_URL})
			else:
				return render_response(request, 'user/change_password.html', {'form': form})
		else:
			form = ResetPasswordForm()
			return render_response(request, 'user/change_password.html', {'form': form})

