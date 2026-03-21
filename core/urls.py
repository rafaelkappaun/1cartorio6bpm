from django.contrib import admin
from django.urls import path
from gestao import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # 1. Painéis e Listagens Principais
    path('', views.painel_principal, name='painel'),
    path('painel/', views.painel_principal, name='painel_principal'),
    path('custodia/', views.custodia_lista, name='custodia_lista'),
    path('conferencia/', views.conferencia_lista, name='conferencia_lista'),
    path('cadastro/', views.cadastro_entrada, name='cadastro_entrada'),

    # 2. Operações de Fluxo (Ações de Botão)
    path('registrar/', views.registrar, name='registrar'),
    path('conferir/<int:id>/', views.confirmar_conferencia, name='confirmar_conferencia'),
    path('autorizar/<int:id>/', views.confirmar_autorizacao, name='confirmar_autorizacao'),
    
    # 3. Gestão de Lotes
    path('lotes/montagem/', views.lotes_montagem, name='lotes_montagem'),
    path('lotes/fechar/', views.fechar_lote_manual, name='fechar_lote_manual'),
    path('lotes/lista/', views.lotes_incineracao, name='lotes_incineracao'),
    path('lotes/finalizar/', views.finalizar_lote_com_eprotocolo, name='finalizar_lote'),
    
    # 4. Relatórios e Impressões Oficiais
    # Centralizado aqui para evitar o erro TemplateDoesNotExist por conflito de rota
    path('lotes/imprimir-capa/<int:id>/', views.imprimir_capa_lote, name='imprimir_capa_lote'),
    path('lotes/imprimir-certidao/<int:id>/', views.imprimir_certidao_lote, name='imprimir_certidao_lote'),
    path('relatorio/recibo/<int:id>/', views.gerar_recibo, name='gerar_recibo'),
    path('relatorios/inventario/', views.relatorio_inventario_geral, name='relatorio_inventario_geral'),
    path('lotes/relatorio-forum/', views.relatorio_forum_view, name='relatorio_vara'),

    # 5. Autenticação e Sistema
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]

# Servir arquivos de mídia (brasões, fotos, etc) durante o desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)