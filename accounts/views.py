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
from .models import ServiceRequest, ChatMessage
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
    from .models import Review
    
    provider = get_object_or_404(ProviderProfile, pk=pk)
    
    # Buscar todas as avaliações feitas por clientes sobre este prestador
    reviews = Review.objects.filter(
        service_request__provider=provider,
        client_rating__isnull=False
    ).select_related('service_request', 'service_request__client').order_by('-client_reviewed_at')
    
    # Calcular média de avaliações
    total_reviews = reviews.count()
    if total_reviews > 0:
        avg_rating = sum(r.client_rating for r in reviews) / total_reviews
    else:
        avg_rating = None
    
    context = {
        "provider": provider,
        "reviews": reviews,
        "total_reviews": total_reviews,
        "avg_rating": avg_rating,
    }
    return render(request, "accounts/provider_detail.html", context)


def client_detail(request, username):
    """Página pública com os detalhes de um cliente."""
    from .models import Review
    from django.contrib.auth.models import User
    
    client_user = get_object_or_404(User, username=username)
    
    # Verificar se o usuário tem perfil de cliente
    if not hasattr(client_user, 'client_profile'):
        messages.error(request, 'Este usuário não é um cliente.')
        return redirect('home')
    
    client_profile = client_user.client_profile
    
    # Buscar todas as avaliações feitas por prestadores sobre este cliente
    reviews = Review.objects.filter(
        service_request__client=client_user,
        provider_rating__isnull=False
    ).select_related('service_request', 'service_request__provider').order_by('-provider_reviewed_at')
    
    # Calcular média de avaliações
    total_reviews = reviews.count()
    if total_reviews > 0:
        avg_rating = sum(r.provider_rating for r in reviews) / total_reviews
    else:
        avg_rating = None
    
    context = {
        "client": client_user,
        "client_profile": client_profile,
        "reviews": reviews,
        "total_reviews": total_reviews,
        "avg_rating": avg_rating,
    }
    return render(request, "accounts/client_detail.html", context)


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
    active_requests = ServiceRequest.objects.filter(
        provider=provider
    ).exclude(status=ServiceRequest.STATUS_COMPLETED).order_by('-created_at')
    
    completed_requests = ServiceRequest.objects.filter(
        provider=provider,
        status=ServiceRequest.STATUS_COMPLETED
    ).order_by('-updated_at')
    
    return render(request, 'accounts/request_list.html', {
        'active_requests': active_requests,
        'completed_requests': completed_requests,
        'view_type': 'provider'
    })


@login_required
def client_requests(request):
    # Lista de solicitações enviadas pelo cliente logado
    active_requests = ServiceRequest.objects.filter(
        client=request.user
    ).exclude(status=ServiceRequest.STATUS_COMPLETED).order_by('-created_at')
    
    completed_requests = ServiceRequest.objects.filter(
        client=request.user,
        status=ServiceRequest.STATUS_COMPLETED
    ).order_by('-updated_at')
    
    return render(request, 'accounts/request_list.html', {
        'active_requests': active_requests,
        'completed_requests': completed_requests,
        'view_type': 'client'
    })


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


@login_required
def chat_view(request, pk):
    sr = get_object_or_404(ServiceRequest, pk=pk)

    # Verificar se é o prestador ou cliente
    is_provider = hasattr(request.user, 'provider_profile') and request.user.provider_profile == sr.provider
    is_client = request.user == sr.client

    if not (is_provider or is_client):
        messages.error(request, 'Você não tem permissão para acessar este chat.')
        return redirect('home')

    # Apenas permitir chat se a solicitação foi aceita (ou já concluída, mas ainda pode ver)
    if sr.status not in [ServiceRequest.STATUS_ACCEPTED, ServiceRequest.STATUS_COMPLETED]:
        messages.warning(request, 'O chat está disponível apenas para solicitações aceitas.')
        return redirect('request_detail', pk=pk)

    # Marcar mensagens como lidas para o usuário atual
    ChatMessage.objects.filter(service_request=sr).exclude(sender=request.user).update(is_read=True)

    # Processar envio de mensagem
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            ChatMessage.objects.create(
                service_request=sr,
                sender=request.user,
                content=content
            )
            return redirect('chat_view', pk=pk)

    messages_qs = sr.messages.all()
    
    context = {
        'service_request': sr,
        'messages': messages_qs,
        'is_provider': is_provider,
        'is_client': is_client,
    }
    return render(request, 'accounts/chat.html', context)


@login_required
def complete_service(request, pk):
    """Marca o serviço como concluído pelo cliente ou prestador."""
    sr = get_object_or_404(ServiceRequest, pk=pk)

    # Verificar se é o prestador ou cliente
    is_provider = hasattr(request.user, 'provider_profile') and request.user.provider_profile == sr.provider
    is_client = request.user == sr.client

    if not (is_provider or is_client):
        messages.error(request, 'Você não tem permissão para marcar este serviço como concluído.')
        return redirect('home')

    # Só pode marcar como concluído se o serviço foi aceito
    if sr.status != ServiceRequest.STATUS_ACCEPTED:
        messages.warning(request, 'Apenas serviços aceitos podem ser marcados como concluídos.')
        return redirect('request_detail', pk=pk)

    if request.method == 'POST':
        # Marcar como concluído pelo cliente ou prestador
        if is_client:
            sr.completed_by_client = True
        elif is_provider:
            sr.completed_by_provider = True
        
        # Se ambos marcaram como concluído, mudar o status
        if sr.completed_by_client and sr.completed_by_provider:
            sr.status = ServiceRequest.STATUS_COMPLETED
            messages.success(request, 'Serviço concluído com sucesso! Ambas as partes confirmaram a conclusão.')
        else:
            if is_client:
                messages.success(request, 'Você marcou o serviço como concluído. Aguardando confirmação do prestador.')
            else:
                messages.success(request, 'Você marcou o serviço como concluído. Aguardando confirmação do cliente.')
        
        sr.save()
        return redirect('request_detail', pk=pk)

    return redirect('request_detail', pk=pk)


@login_required
def review_service(request, pk):
    """Permite ao cliente ou prestador avaliar o serviço após conclusão."""
    from .models import Review
    from django.utils import timezone
    
    sr = get_object_or_404(ServiceRequest, pk=pk)

    # Verificar se é o prestador ou cliente
    is_provider = hasattr(request.user, 'provider_profile') and request.user.provider_profile == sr.provider
    is_client = request.user == sr.client

    if not (is_provider or is_client):
        messages.error(request, 'Você não tem permissão para avaliar este serviço.')
        return redirect('home')

    # Só pode avaliar se o serviço foi concluído
    if sr.status != ServiceRequest.STATUS_COMPLETED:
        messages.warning(request, 'Apenas serviços concluídos podem ser avaliados.')
        return redirect('request_detail', pk=pk)

    # Buscar ou criar review
    review, created = Review.objects.get_or_create(service_request=sr)

    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '').strip()

        # Validar rating
        try:
            rating = int(rating)
            if rating < 0 or rating > 5:
                messages.error(request, 'A avaliação deve ser entre 0 e 5 estrelas.')
                return redirect('review_service', pk=pk)
        except (ValueError, TypeError):
            messages.error(request, 'Avaliação inválida.')
            return redirect('review_service', pk=pk)

        # Salvar avaliação do cliente
        if is_client:
            if review.client_has_reviewed:
                messages.warning(request, 'Você já avaliou este serviço.')
            else:
                review.client_rating = rating
                review.client_comment = comment
                review.client_reviewed_at = timezone.now()
                review.save()
                messages.success(request, 'Sua avaliação foi registrada com sucesso!')
        
        # Salvar avaliação do prestador
        elif is_provider:
            if review.provider_has_reviewed:
                messages.warning(request, 'Você já avaliou este cliente.')
            else:
                review.provider_rating = rating
                review.provider_comment = comment
                review.provider_reviewed_at = timezone.now()
                review.save()
                messages.success(request, 'Sua avaliação foi registrada com sucesso!')

        return redirect('request_detail', pk=pk)

    context = {
        'service_request': sr,
        'review': review,
        'is_provider': is_provider,
        'is_client': is_client,
    }
    return render(request, 'accounts/review_service.html', context)
