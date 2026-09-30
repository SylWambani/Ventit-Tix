from django.urls import path
from . import views

urlpatterns = [
    path("start/", views.start_payment, name="start-payment"),
    path("callback/", views.callback, name="mpesa-callback"),
    path("status/<int:pk>/", views.payment_status, name="payment-status"),
]