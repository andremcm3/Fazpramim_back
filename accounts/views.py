from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from .forms import SignUpForm
from .forms import ClientSignUpForm, ProviderSignUpForm


# Create your views here.
def register(request):
	if request.method == 'POST':
		form = SignUpForm(request.POST)
		if form.is_valid():
			user = form.save()
			login(request, user)
			return redirect('home')
	else:
		form = SignUpForm()
	return render(request, 'accounts/register.html', {'form': form})


def logout_view(request):
	"""Log out the user and redirect to login page. Allows GET to support simple link-based logout."""
	logout(request)
	return redirect('login')


def register_choice(request):
	return render(request, 'accounts/register_choice.html')


def register_client(request):
	if request.method == 'POST':
		form = ClientSignUpForm(request.POST, request.FILES)
		if form.is_valid():
			user = form.save()
			login(request, user)
			return redirect('home')
	else:
		form = ClientSignUpForm()
	return render(request, 'accounts/register_client.html', {'form': form})


def register_provider(request):
	if request.method == 'POST':
		form = ProviderSignUpForm(request.POST, request.FILES)
		if form.is_valid():
			user = form.save()
			login(request, user)
			return redirect('home')
	else:
		form = ProviderSignUpForm()
	return render(request, 'accounts/register_provider.html', {'form': form})
