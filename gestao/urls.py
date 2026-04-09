from django.urls import path
from gestao import views

urlpatterns = [
    # Painel e páginas principais
    path('painel/', views.painel_principal, name='painel'),
    path('', views.painel_principal, name='home'),
    
    # Relatórios HTML
    path('relatorios', views.relatorio_gerencial, name='relatorios'),
    path('relatorios/', views.relatorio_gerencial, name='relatorios_slash'),
    path('relatorio/gerencial/', views.relatorio_gerencial, name='relatorio_gerencial'),
    path('relatorio/incineracao/', views.relatorio_incineracao, name='relatorio_incineracao'),
    path('relatorio/', views.relatorio_gerencial, name='relatorio_gerencial'),
]
