from django.shortcuts import render

def home(request):
    """
    Root landing page for PrintFlow.
    Acts as a dashboard entry point.
    """
    return render(request, "home.html")
