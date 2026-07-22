"""Queue engine API routes, mounted under /api/v1/queue/."""
from django.urls import path

from apps.queue_management import api_views

app_name = "queue_api"

urlpatterns = [
    # Token lifecycle
    path("tokens/book/", api_views.BookTokenView.as_view(), name="book"),
    path("tokens/walk-in/", api_views.WalkInTokenView.as_view(), name="walk-in"),
    path("tokens/my/", api_views.MyTokensView.as_view(), name="my-tokens"),
    path("tokens/<uuid:public_id>/", api_views.TokenDetailView.as_view(), name="detail"),
    path("tokens/<uuid:public_id>/cancel/", api_views.CancelTokenView.as_view(), name="cancel"),
    path("tokens/<uuid:public_id>/check-in/", api_views.CheckInTokenView.as_view(), name="check-in"),

    # Operator actions on a token
    path("tokens/<uuid:public_id>/complete/", api_views.CompleteTokenView.as_view(), name="complete"),
    path("tokens/<uuid:public_id>/hold/", api_views.HoldTokenView.as_view(), name="hold"),
    path("tokens/<uuid:public_id>/resume/", api_views.ResumeTokenView.as_view(), name="resume"),
    path("tokens/<uuid:public_id>/skip/", api_views.SkipTokenView.as_view(), name="skip"),
    path("tokens/<uuid:public_id>/no-show/", api_views.NoShowTokenView.as_view(), name="no-show"),
    path("tokens/<uuid:public_id>/emergency/", api_views.EmergencyTokenView.as_view(), name="emergency"),
    path("tokens/<uuid:public_id>/transfer/", api_views.TransferTokenView.as_view(), name="transfer"),

    # Public live queue (transparency — no auth required)
    path("live/", api_views.LiveQueueView.as_view(), name="live"),

    # Counters
    path("counters/", api_views.CounterListView.as_view(), name="counters"),
    path("counters/<uuid:public_id>/claim/", api_views.CounterClaimView.as_view(), name="counter-claim"),
    path("counters/<uuid:public_id>/release/", api_views.CounterReleaseView.as_view(), name="counter-release"),
    path("counters/my/queue/", api_views.MyCounterQueueView.as_view(), name="my-counter-queue"),
    path("counters/my/call-next/", api_views.CallNextView.as_view(), name="call-next"),
]
