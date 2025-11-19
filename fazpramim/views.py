from django.shortcuts import render

def home(request):
    return render(request, "fazpramim/home.html")

def search_view(request):
    query = request.GET.get("q", "")
    context = {"results": [], "query": query}
    return render(request, "fazpramim/search.html", context)
