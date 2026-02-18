from django.contrib import messages
from django.db import IntegrityError
from django.utils import timezone 
from django.shortcuts import get_object_or_404, render, redirect
from django.db.models import Sum, Q, FloatField
from django.db.models.functions import Cast, Coalesce
from .models import Material, DROGAS_CHOICES 
from django.contrib.auth.decorators import login_required
import json

@login_required
def painel_principal(request):
    # 1. Captura a busca
    busca = request.GET.get('busca_bou', '').strip()
    
    # 2. Pega todos os materiais
    materiais_todos = Material.objects.all()

    # 3. Filtra pela busca se houver
    if busca:
        base_filtrada = materiais_todos.filter(bou__icontains=busca)
    else:
        base_filtrada = materiais_todos

    # 4. DISTRIBUIÇÃO CORRETA PELAS ABAS (O segredo está aqui)
    # Somente quem é PENDENTE vai para a aba de conferência
    pendentes = base_filtrada.filter(status='PENDENTE').order_by('-data_entrada')
    
    # Somente quem está NO_COFRE vai para a aba do cofre
    no_cofre = base_filtrada.filter(status='NO_COFRE').order_by('caixa', 'bou')
    
    # Somente quem está PRONTO_QUEIMA vai para a aba de queima
    prontos = base_filtrada.filter(status='PRONTO_QUEIMA').order_by('-data_entrada')

    # 5. Lógica do Gráfico (mantém apenas o que está fisicamente no Batalhão)
    dados_grafico = Material.objects.filter(status__in=['NO_COFRE', 'PRONTO_QUEIMA']).values('substancia').annotate(
        total=Sum(Coalesce(Cast('peso_real', FloatField()), 0.0))
    )

    incinerados = base_filtrada.filter(status='INCINERADO').order_by('-data_conferencia')   

    contexto = {
        'pendentes': pendentes,
        'no_cofre': no_cofre,
        'prontos': prontos,
        'incinerados': incinerados,
        'labels_json': [d['substancia'] for d in dados_grafico],
        'valores_json': [float(d['total']) for d in dados_grafico],
        'drogas_lista': DROGAS_CHOICES,
        'busca_termo': busca,
        'total_geral': materiais_todos.count(),
    }
    return render(request, 'gestao/painel.html', contexto)

@login_required
def registrar_entrada(request):
    if request.method == "POST":
        try:
            # CORREÇÃO: Fechado o parêntese do create() antes de prosseguir
            Material.objects.create(
                bou=request.POST.get('bou'),
                noticiado=request.POST.get('noticiado'),
                processo=request.POST.get('processo'),
                numero_vestigio=request.POST.get('numero_vestigio'),
                policial_entrega=request.POST.get('policial_entrega'),
                vara=request.POST.get('vara'),
                substancia=request.POST.get('substancia'),
                peso_estimado=request.POST.get('peso_estimado'),
                unidade=request.POST.get('unidade'),
                observacao=request.POST.get('observacao'),
                status='PENDENTE',
                usuario_registro=request.user
            ) # <--- Parêntese fechado aqui
            messages.success(request, f"BOU registrado por {request.user.username}. Aguardando conferência.")
        except IntegrityError:
            messages.error(request, "Erro: Este BOU já existe no sistema.")
    return redirect('painel')

@login_required
def confirmar_conferencia(request, id):
    if request.method == "POST":
        item = get_object_or_404(Material, id=id)
        ano = timezone.now().year
        semestre = "01" if timezone.now().month <= 6 else "02"
        
        item.peso_real = request.POST.get('peso_real').replace(',', '.')
        item.caixa = request.POST.get('caixa')
        item.lote = f"{ano}/{semestre}"
        item.status = 'NO_COFRE'
        item.usuario_conferencia = request.user
        item.save()
        messages.success(request, f"Item conferido por {request.user.username} (Lote {item.lote})")
    return redirect('painel')

@login_required
def vincular_oficio(request, id):
    if request.method == "POST":
        item = get_object_or_404(Material, id=id)
        item.n_oficio = request.POST.get('n_oficio')
        item.status = 'PRONTO_QUEIMA'
        item.save()
        messages.success(request, "Item autorizado para queima!")
    return redirect('painel')

@login_required
def finalizar_lote(request):
    """ Dá baixa definitiva no lote e registra a data da incineração """
    if request.method == "POST":
        nome_lote = request.POST.get('lote')
        itens = Material.objects.filter(lote=nome_lote, status='PRONTO_QUEIMA')
        if itens.exists():
            qtd = itens.count()
            # CORREÇÃO: Atualizando data_incineracao conforme o seu Models
            itens.update(status='INCINERADO', data_incineracao=timezone.now())
            messages.success(request, f"Lote {nome_lote} finalizado! {qtd} itens incinerados.")
        else:
            messages.warning(request, "Nenhum item pendente neste lote.")
    return redirect('painel')

@login_required
def relatorio_final(request):
    """ Relatório de Gestão Interna com Filtros """
    v = request.GET.get('vara', '').strip()
    s = request.GET.get('substancia', '').strip()
    m = request.GET.get('mes', '').strip()

    itens = Material.objects.all() 
    if v: itens = itens.filter(vara=v)
    if s: itens = itens.filter(substancia=s)
    if m: itens = itens.filter(data_entrada__month=m)

    resumo = itens.values('substancia', 'unidade').annotate(
        total_massa=Sum(Coalesce(Cast('peso_real', FloatField()), 0.0))
    )
    
    # Dicionário para traduzir o nome da droga no resumo
    drogas_dict = dict(DROGAS_CHOICES)
    resumo_formatado = []
    for r in resumo:
        resumo_formatado.append({
            'substancia': drogas_dict.get(r['substancia'], r['substancia']),
            'total_massa': r['total_massa'],
            'unidade': r['unidade']
        })

    return render(request, 'gestao/relatorio.html', {
        'itens': itens.order_by('-data_entrada'),
        'resumo': resumo_formatado,
        'data_hoje': timezone.now(),
        'drogas_lista': DROGAS_CHOICES,
        'filtros': {'vara': v, 'substancia': s, 'mes': m}
    })

@login_required
def relatorio_queima(request):
    """ Relatório de INCINERAÇÃO (O Auto de Incineração) """
    # Filtra apenas o que está pronto para queima
    itens_queima = Material.objects.filter(status='PRONTO_QUEIMA').order_by('lote', 'bou')
    
    return render(request, 'gestao/relatorio_queima.html', {
        'itens': itens_queima,
        'data_atual': timezone.now(),
    })

@login_required
def relatorio_forum(request):
    """ Relatório Jurídico ordenado pela data da incineração """
    vara_slug = request.GET.get('vara')
    itens = Material.objects.filter(status='INCINERADO')

    if vara_slug:
        itens = itens.filter(vara=vara_slug)

    # Ordenando pela data de incineração mais recente para o fórum
    return render(request, 'gestao/relatorio_forum.html', {
        'itens': itens.order_by('-data_incineracao', 'processo'),
        'data_hoje': timezone.now(),
        'vara_selecionada': vara_slug,
    })

@login_required
def editar_item_rapido(request, id):
    if request.method == "POST":
        item = get_object_or_404(Material, id=id)
        item.lote = request.POST.get('lote').upper()
        if item.status == 'PENDENTE':
            item.status = 'NO_COFRE'
        item.save()
    return redirect(request.META.get('HTTP_REFERER', 'painel'))