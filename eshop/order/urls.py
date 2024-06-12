from django.urls import path
from .views import new_order, get_orders, get_order, process_order, delete_order, create_checkout_session, stripe_webhook

urlpatterns = [
    path("orders/new/", new_order, name="new_order"),
    path("orders/", get_orders, name="orders"),
    path("orders/<str:pk>/", get_order, name="get_order"),
    path("orders/<str:pk>/process/", process_order, name="process_order"),
    path("orders/<str:pk>/delete/", delete_order, name="delete_order"),

    path("create-checkout-session/", create_checkout_session,
         name="create_checkout_session"),

    path("order/webhook/", stripe_webhook, name="stripe_webhook")
]
