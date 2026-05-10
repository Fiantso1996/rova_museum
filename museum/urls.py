from django.urls import path
from . import views
from . import api_views   # <-- Importation ajoutée

urlpatterns = [
    path('', views.home, name='home'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/data/', views.cart_data, name='cart_data'),
    path('checkout/', views.checkout, name='checkout'),
    path('process-payment/', views.process_payment, name='process_payment'),
    path('order/<int:order_id>/barcode/', views.download_barcode, name='download_barcode'),
    path('api/validate/', api_views.validate_ticket, name='api_validate_ticket'),
    path('scan/', views.scan_page, name='scan_page'),
    # ── Nouveaux URLs ──────────────────────────────────────────
    path('contact/', views.contact, name='contact'),
    path('equipe/', views.staff, name='staff'),
    path('evenements/', views.events, name='events'),
    path('evenements/<int:event_id>/', views.event_detail, name='event_detail'),
]