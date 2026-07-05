"""Dashboard app views — public landing page + role-based dashboards."""
from django.shortcuts import render


def home(request):
    """
    Public landing page. Full hero/features/testimonials content is built
    in the Frontend Development + UI/UX Design phases — this is a working
    placeholder so the project runs end-to-end today.
    """
    office_types = [
        "Passport Office", "Transport Office", "Municipality Office", "Ward Office",
        "Inland Revenue", "Land Revenue", "Hospitals", "Public Service Commission",
    ]
    return render(request, "pages/home.html", {"offices": office_types})


def citizen_dashboard_preview(request):
    """
    Styling preview of the citizen dashboard shell for the UI/UX Design
    phase. Real data + auth-gating are wired in the Queue Management
    Engine phase.
    """
    return render(request, "dashboard/citizen_dashboard.html", {"active_nav": "overview"})
