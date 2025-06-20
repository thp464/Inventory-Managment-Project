from django.shortcuts import render, redirect
from django.views.generic import TemplateView, View
from django.contrib.auth import authenticate, login
from .forms import UserRegistrationForm
from .models import InventoryItem

# Create your views here.
class Index(TemplateView):
    template_name = 'inventory/index.html'

class Dashboard(View):
	def get(self, request):
		items = InventoryItem.objects.filter(user=self.request.user.id).order_by('id')
		return render(request, 'inventory/dashboard.html', {'items': items})

class SignUpView(View):
	def get(self, request):
		form = UserRegistrationForm()
		return render(request, 'inventory/signup.html', {'form': form})

	def post(self, request):
		form = UserRegistrationForm(request.POST)

		if form.is_valid():
			form.save()
			user = authenticate(
				username=form.cleaned_data['username'],
				password=form.cleaned_data['password1']
			)

			login(request, user)
			return redirect('index')

		return render(request, 'inventory/signup.html', {'form': form})