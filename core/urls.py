"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from gestao import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Administrativo e Painel Principal
    path('admin/', admin.site.urls),
    path('', views.painel_principal, name='painel'),
    
    
    # Operações de Material
    path('registrar/', views.registrar_entrada, name='registrar'),
    path('conferir/<int:id>/', views.confirmar_conferencia, name='conferir'),
    path('vincular/<int:id>/', views.vincular_oficio, name='vincular_oficio'),
    path('finalizar-lote/', views.finalizar_lote, name='finalizar_lote'),

    # Autenticação
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Relatórios
    path('relatorio/', views.relatorio_final, name='relatorio_final'),
    path('relatorio-queima/', views.relatorio_queima, name='relatorio_queima'),
    path('relatorio-forum/', views.relatorio_forum, name='relatorio_forum'),
    path('relatorio/recibo/<int:id>/', views.gerar_recibo, name='gerar_recibo'),
]