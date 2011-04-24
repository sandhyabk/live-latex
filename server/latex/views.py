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
	if request.POST:
		new_data = request.POST.copy()
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
	else:
		form = UserLogin()
		return render_to_response('user_login.html', {'form':form,}, context_instance=RequestContext(request))


def test(request):
	if not request.user.is_authenticated():
		return HttpResponse('Not authenticated')
	else:
		return HttpResponse('Authenticated')
