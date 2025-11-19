from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required

from .forms import (
    SignUpForm,
    ClientSignUpForm,
    ProviderSignUpForm,
    ClientProfileForm,
    ProviderProfileForm,
)
from .models import ClientProfile, ProviderProfile
from django.shortcuts import get_object_or_404


# --------- CADASTRO GENÉRICO (SE AINDA QUISER USAR) --------- #
def register(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = SignUpForm()
    return render(request, "accounts/register.html", {"form": form})


def logout_view(request):
    """Faz logout e redireciona para a página de login."""
    logout(request)
    return redirect("login")


# --------- ESCOLHA DO TIPO DE CADASTRO --------- #
def register_choice(request):
    return render(request, "accounts/register_choice.html")


# --------- CADASTRO DE CLIENTE --------- #
def register_client(request):
    if request.method == "POST":
        form = ClientSignUpForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = ClientSignUpForm()
    return render(request, "accounts/register_client.html", {"form": form})


# --------- CADASTRO DE PRESTADOR --------- #
def register_provider(request):
    if request.method == "POST":
        form = ProviderSignUpForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = ProviderSignUpForm()
    return render(request, "accounts/register_provider.html", {"form": form})


# --------- PÁGINA "MEU PERFIL" (CLIENTE OU PRESTADOR) --------- #
@login_required
def my_profile(request):
    user = request.user

    # Descobre se o usuario é cliente ou prestador
    is_client = hasattr(user, "client_profile")
    is_provider = hasattr(user, "provider_profile")

    if not is_client and not is_provider:
        # Se não tiver perfil ainda, manda escolher o tipo de cadastro
        return redirect("register_choice")

    if is_client:
        profile = user.client_profile
        FormClass = ClientProfileForm
    else:
        profile = user.provider_profile
        FormClass = ProviderProfileForm

    if request.method == "POST":
        form = FormClass(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect("my_profile")
    else:
        form = FormClass(instance=profile)

    context = {
        "form": form,
        "is_client": is_client,
        "is_provider": is_provider,
    }
    return render(request, "accounts/my_profile.html", context)


def provider_detail(request, pk):
    """Página pública com os detalhes de um prestador de serviço."""
    provider = get_object_or_404(ProviderProfile, pk=pk)
    context = {"provider": provider}
    return render(request, "accounts/provider_detail.html", context)
