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
from .forms import ServiceRequestForm
from .models import ClientProfile, ProviderProfile
from .models import ServiceRequest
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
try:
    # Import DRF views for API integration (used by urls)
    from .api.views import (
        CreateServiceRequestAPIView,
        ProviderRequestsListAPIView,
        ServiceRequestDetailAPIView,
    )
except Exception:
    # If DRF is not available, the import will fail but views will still work
    pass
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


@login_required
def create_request(request, pk):
    provider = get_object_or_404(ProviderProfile, pk=pk)

    # Não permitir que o próprio prestador peça serviço a si mesmo
    if hasattr(request.user, 'provider_profile') and request.user.provider_profile.pk == provider.pk:
        messages.error(request, "Você não pode solicitar um serviço para si mesmo.")
        return redirect('provider_detail', pk=pk)

    if request.method == 'POST':
        form = ServiceRequestForm(request.POST)
        if form.is_valid():
            sr = form.save(commit=False)
            sr.provider = provider
            sr.client = request.user
            sr.save()
            # AJAX request -> return JSON
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Solicitação enviada com sucesso.',
                    'request_id': sr.id,
                })

            messages.success(request, 'Solicitação enviada com sucesso.')
            return redirect('provider_detail', pk=pk)
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                # return form errors as json
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    else:
        form = ServiceRequestForm()

    return render(request, 'accounts/provider_request_form.html', {'form': form, 'provider': provider})


@login_required
def provider_requests(request):
    # Lista de solicitações para o prestador logado
    if not hasattr(request.user, 'provider_profile'):
        return redirect('my_profile')

    provider = request.user.provider_profile
    requests_qs = ServiceRequest.objects.filter(provider=provider).order_by('-created_at')
    return render(request, 'accounts/request_list.html', {'requests': requests_qs})


@login_required
def request_detail(request, pk):
    sr = get_object_or_404(ServiceRequest, pk=pk)

    # Permitir visualização se for o provider dono ou o cliente que enviou
    if not (hasattr(request.user, 'provider_profile') and request.user.provider_profile == sr.provider) and request.user != sr.client:
        return redirect('home')

    # Aceitar / rejeitar (apenas provider dono)
    if request.method == 'POST' and hasattr(request.user, 'provider_profile') and request.user.provider_profile == sr.provider:
        action = request.POST.get('action')
        if action == 'accept':
            sr.status = ServiceRequest.STATUS_ACCEPTED
            sr.save()
            messages.success(request, 'Solicitação aceita.')
        elif action == 'reject':
            sr.status = ServiceRequest.STATUS_REJECTED
            sr.save()
            messages.success(request, 'Solicitação rejeitada.')
        return redirect('request_detail', pk=pk)

    return render(request, 'accounts/request_detail.html', {'request_obj': sr})
