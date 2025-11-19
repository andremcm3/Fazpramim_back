from django.shortcuts import render
from django.db.models import Q
from accounts.models import ProviderProfile
from django.http import HttpResponse


def home(request):
    return render(request, "fazpramim/home.html")


def search_view(request):
    query = request.GET.get("q", "").strip()
    results = []

    if query:
        # Buscar prestadores cujo nome ou qualificação técnica contenham a query (case-insensitive)
        results = ProviderProfile.objects.filter(
            Q(full_name__icontains=query) | Q(technical_qualification__icontains=query)
        )
    context = {"results": results, "query": query}

    # Se for requisição AJAX, retorna somente o fragmento de resultados
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'fazpramim/_search_results.html', context)

    return render(request, "fazpramim/search.html", context)
