"""Dashboard app views — public landing page + role-based dashboards."""
from django.shortcuts import render


def home(request):
    """
    Public landing page. Full hero/features/testimonials content is built
    in the Frontend Development + UI/UX Design phases — this is a working
    placeholder so the project runs end-to-end today.
    """
    return render(request, "pages/home.html")
