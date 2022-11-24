from django.urls import path
from . import views


urlpatterns = [
    path("finalizar_pedido/", views.finalizar_pedido, name='finalizar_pedido'),
    path("validaCupom/", views.validaCupom, name='validaCupom'),
    path('form-payment/', views.form_payment, name='form-payment'),
    path('create-payment-intent/', views.create_payment_intent, name="create-payment-intent"),
    path('clear_carrinho/', views.clear_carrinho, name='clear_carrinho')


]