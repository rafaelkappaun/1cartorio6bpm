from django.urls import path
from django.contrib.auth import views as auth_views
from gestao import views

urlpatterns = [
    # Autenticação
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Painel e páginas principais
    path('painel/', views.painel_principal, name='painel'),
    path('', views.painel_principal, name='home'),
    
    # Fluxo Operacional
    path('cadastro/', views.cadastro_entrada, name='cadastro_entrada'),
    path('cadastro/adicionar/<int:ocorrencia_id>/', views.cadastro_entrada, name='cadastro_adicionar'),
    path('registrar/', views.registrar, name='registrar'),
    path('conferencia/', views.conferencia_lista, name='conferencia_lista'),
    path('conferir/<int:id>/', views.confirmar_conferencia, name='confirmar_conferencia'),
    
    # APIs
    path('api/verificar_ocorrencia/', views.api_verificar_ocorrencia, name='api_verificar_ocorrencia'),
    path('api/dados_autocomplete/', views.api_dados_autocomplete, name='api_dados_autocomplete'),
    path('api/receber_projudi/', views.api_receber_projudi, name='api_receber_projudi'),
    path('api/ler_tc/', views.api_ler_tc, name='api_ler_tc'),
    
    # Armazenamento e Custódia
    path('custodia/', views.custodia_lista, name='custodia_lista'),
    path('autorizar/<int:id>/', views.confirmar_autorizacao, name='confirmar_autorizacao'),
    
    # Ciclo de Queima (Lotes)
    path('lotes/montagem/', views.lotes_montagem, name='lotes_montagem'),
    path('lotes/criar/', views.fechar_lote_manual, name='fechar_lote_manual'),
    path('lotes/lista/', views.lotes_incineracao, name='lotes_incineracao'),
    path('lotes/finalizar/', views.finalizar_lote_com_eprotocolo, name='finalizar_lote_com_eprotocolo'),
    
    # Caixas de Incineração
    path('caixas/', views.caixas_incineracao, name='caixas_incineracao'),
    path('caixas/criar/', views.criar_caixa, name='criar_caixa'),
    path('caixas/adicionar-lote/<int:caixa_id>/<int:lote_id>/', views.adicionar_lote_caixa, name='adicionar_lote_caixa'),
    path('caixas/remover-lote/<int:lote_id>/', views.remover_lote_caixa, name='remover_lote_caixa'),
    path('caixas/mover-lote/', views.mover_lote_entre_caixas, name='mover_lote_entre_caixas'),
    path('caixas/concluir/<int:caixa_id>/', views.concluir_caixa, name='concluir_caixa'),
    path('caixas/certidao/<int:caixa_id>/', views.imprimir_certidao_caixa, name='imprimir_certidao_caixa'),
    path('caixas/espelho/<int:caixa_id>/', views.imprimir_espelho_caixa, name='imprimir_espelho_caixa'),
    
    # Impressão e Documentos
    path('recibo/<int:id>/', views.gerar_recibo, name='gerar_recibo'),
    path('capa-lote/<int:id>/', views.imprimir_capa_lote, name='imprimir_capa_lote'),
    path('certidao-lote/<int:id>/', views.imprimir_certidao_lote, name='imprimir_certidao_lote'),
    path('lotes/certidao-coletiva/', views.relatorio_forum_view, name='certidao_coletiva_lotes'),
    
    # Relatórios e Auditoria
    path('relatorio/gerencial/', views.relatorio_gerencial, name='relatorio_gerencial'),
    path('relatorio/incineracao/', views.relatorio_incineracao, name='relatorio_incineracao'),
    path('inventario/', views.relatorio_inventario_geral, name='relatorio_inventario'),
    path('oficio/gerar/', views.gerar_oficio_remessa_view, name='gerar_oficio_remessa'),
]
