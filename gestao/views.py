from datetime import datetime
from datetime import date
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Sum, Count, Q, Max
from django.db.models.functions import ExtractMonth, ExtractYear
from django.core.paginator import Paginator

from .models import (
    DROGAS_CHOICES, GRADUACAO_CHOICES, VARA_CHOICES, 
    Ocorrencia, Material, Noticiado, LoteIncineracao, RegistroHistorico
)

# --- FUNÇÃO AUXILIAR DE FORMATAÇÃO (Para evitar o erro de toneladas) ---
def formatar_peso_br(valor_gramas):
    """ Converte gramas para KG se passar de 1000, com vírgula brasileira """
    if not valor_gramas:
        return "0,000 g"
    if valor_gramas >= 1000:
        kg = valor_gramas / 1000
        return f"{kg:.3f} kg".replace('.', ',')
    return f"{valor_gramas:.3f} g".replace('.', ',')

# --- 1. CADASTRO DE ENTRADA ---

@login_required
@transaction.atomic
def registrar(request):
    if request.method == "POST":
        try:
            bou = request.POST.get('bou', '').strip()
            processo = request.POST.get('processo', '').strip()

            if Ocorrencia.objects.filter(bou=bou).exists():
                messages.error(request, f"O BOU {bou} já está cadastrado!")
                return redirect('cadastro_entrada')

            ocorrencia = Ocorrencia.objects.create(
                bou=bou,
                data_registro=request.POST.get('data_registro'),
                vara=request.POST.get('vara'),
                processo=processo if processo else None,
                policial_nome=request.POST.get('policial_nome', '').upper(),
                policial_graduacao=request.POST.get('policial_graduacao'),
                rg_policial=request.POST.get('rg_policial'),
                unidade_origem=request.POST.get('unidade_origem'),
                unidade_especifica=request.POST.get('unidade_especifica'), 
                cartorario=request.user
            )

            nomes = request.POST.getlist('nome_noticiado[]')
            substancias = request.POST.getlist('substancia[]')
            pesos = request.POST.getlist('peso_estimado[]')
            lacres = request.POST.getlist('lacre[]')

            for i in range(len(nomes)):
                if nomes[i].strip():
                    noticiado = Noticiado.objects.create(
                        ocorrencia=ocorrencia,
                        nome=nomes[i].strip().upper()
                    )
                    peso_limpo = float(pesos[i].replace(',', '.')) if pesos[i] else 0
                    Material.objects.create(
                        noticiado=noticiado,
                        substancia=substancias[i],
                        peso_estimado=peso_limpo,
                        numero_lacre=lacres[i].strip() if i < len(lacres) else None,
                        status='AGUARDANDO_CONFERENCIA'
                    )

            messages.success(request, f"BOU {bou} registrado com sucesso!")
            return redirect(reverse('cadastro_entrada') + f'?sucesso_id={ocorrencia.id}')
        except Exception as e:
            messages.error(request, f"Erro operacional no cadastro: {e}")
            return redirect('cadastro_entrada')
    return redirect('cadastro_entrada')

# --- 2. MOVIMENTAÇÃO ---

@login_required
@transaction.atomic
def confirmar_conferencia(request, id):
    if request.method == "POST":
        material = get_object_or_404(Material, id=id)
        peso_txt = request.POST.get('peso_real', '0').replace(',', '.')
        material.peso_real = float(peso_txt)
        material.status = 'NO_COFRE'
        material.conferido_por = request.user
        material.data_conferencia_fisica = timezone.now()
        material.save()
        
        RegistroHistorico.objects.create(
            material=material, usuario=request.user, status_novo='NO_COFRE',
            observacao=f"Pesagem Oficial: {material.peso_real}g. Conferido por {request.user.get_full_name()}."
        )
        messages.success(request, f"BOU {material.noticiado.ocorrencia.bou} conferido.")
    return redirect('conferencia_lista')

@login_required
@transaction.atomic
def confirmar_autorizacao(request, id):
    if request.method == "POST":
        material = get_object_or_404(Material, id=id)
        material.status = 'AUTORIZADO'
        material.autorizado_por = request.user
        material.data_autorizacao = timezone.now()
        material.save()
        RegistroHistorico.objects.create(
            material=material, usuario=request.user, status_novo='AUTORIZADO',
            observacao=f"Autorização Judicial confirmada por {request.user.get_full_name()}."
        )
        messages.success(request, f"BOU {material.noticiado.ocorrencia.bou} autorizado!")
    return redirect('custodia_lista')

# --- 3. DASHBOARD (Onde corrigimos a exibição) ---

@login_required
def painel_principal(request):
    hoje = datetime.now()
    ano_selecionado = int(request.GET.get('ano', hoje.year))
    periodo_request = request.GET.get('periodo', 'ano')
    mes_request = request.GET.get('mes', 'todos')
    
    filtros = Q(noticiado__ocorrencia__data_registro__year=ano_selecionado)

    if mes_request != 'todos' and mes_request.isdigit():
        filtros &= Q(noticiado__ocorrencia__data_registro__month=int(mes_request))
        periodo_ativo = mes_request
    elif periodo_request == 's1':
        filtros &= Q(noticiado__ocorrencia__data_registro__month__range=(1, 6))
        periodo_ativo = 's1'
    elif periodo_request == 's2':
        filtros &= Q(noticiado__ocorrencia__data_registro__month__range=(7, 12))
        periodo_ativo = 's2'
    else:
        periodo_ativo = 'ano'

    materiais_filtrados = Material.objects.select_related('noticiado__ocorrencia').filter(filtros)
    
    dados_periodo = materiais_filtrados.aggregate(
        no_cofre=Sum('peso_real', filter=Q(status='NO_COFRE') | Q(status='AUTORIZADO')),
        incinerado=Sum('peso_real', filter=Q(status='INCINERADO')),
        pendente=Sum('peso_real', filter=Q(status='AUTORIZADO')),
        aguardando_conf=Sum('peso_estimado', filter=Q(status='AGUARDANDO_CONFERENCIA')),
        total_processos=Count('noticiado__ocorrencia', distinct=True)
    )

    substancias_dict = dict(DROGAS_CHOICES)
    
    # Gráficos
    resumo_drogas = materiais_filtrados.values('substancia').annotate(t=Sum('peso_real')).order_by('-t')
    labels_drogas = [substancias_dict.get(x['substancia'], x['substancia']) for x in resumo_drogas]
    pesos_drogas = [float(x['t'] or 0) for x in resumo_drogas]

    resumo_unidades = materiais_filtrados.values('noticiado__ocorrencia__unidade_origem').annotate(t=Sum('peso_real')).order_by('-t')
    labels_unid = [u['noticiado__ocorrencia__unidade_origem'] or "S/ UNIDADE" for u in resumo_unidades]
    dados_unid = [float(u['t'] or 0) for u in resumo_unidades]

    # Evolução Mensal
    tipos_drogas_ano = materiais_filtrados.values_list('substancia', flat=True).distinct()
    datasets_evolucao = []
    cores = ['#1a3a2a', '#c5a059', '#2c3e50', '#e74c3c', '#3498db', '#f1c40f', '#8e44ad']

    for i, droga_cod in enumerate(tipos_drogas_ano):
        valores_mensais = []
        for mes_idx in range(1, 13):
            v = Material.objects.filter(
                noticiado__ocorrencia__data_registro__year=ano_selecionado,
                noticiado__ocorrencia__data_registro__month=mes_idx,
                substancia=droga_cod
            ).aggregate(s=Sum('peso_real'))['s'] or 0
            valores_mensais.append(float(v))
        
        datasets_evolucao.append({
            'label': substancias_dict.get(droga_cod, droga_cod),
            'data': valores_mensais,
            'borderColor': cores[i % len(cores)],
            'backgroundColor': 'transparent', 'tension': 0.3, 'pointRadius': 4
        })

    # Ranking (Tabela) formatado
    ranking_qs = materiais_filtrados.values(
        'noticiado__ocorrencia__policial_nome', 'substancia'
    ).annotate(qtd=Count('id'), peso=Sum('peso_real')).order_by('-peso')

    ranking_list = []
    for p in ranking_qs:
        ranking_list.append({
            'nome_policial': p['noticiado__ocorrencia__policial_nome'] or "NÃO INFORMADO",
            'nome_droga': substancias_dict.get(p['substancia'], p['substancia']),
            'qtd': p['qtd'],
            'peso_formatado': formatar_peso_br(p['peso']) # Formata aqui para o HTML
        })

    paginator = Paginator(ranking_list, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'ano_atual': ano_selecionado,
        'periodo_atual': periodo_ativo,
        'mes_selecionado': mes_request,
        'anos_disponiveis': range(2023, hoje.year + 1),
        'meses_lista': [(1,'Jan'),(2,'Fev'),(3,'Mar'),(4,'Abr'),(5,'Mai'),(6,'Jun'),(7,'Jul'),(8,'Ago'),(9,'Set'),(10,'Out'),(11,'Nov'),(12,'Dez')],
        
        # Labels já formatadas para os CARDS
        'no_cofre_label': formatar_peso_br(dados_periodo['no_cofre']),
        'incinerado_label': formatar_peso_br(dados_periodo['incinerado']),
        'pendente_label': formatar_peso_br(dados_periodo['pendente']),
        'aguardando_conf_label': formatar_peso_br(dados_periodo['aguardando_conf']),
        'total_processos': dados_periodo['total_processos'] or 0,
        
        'labels_json': json.dumps(labels_drogas),
        'pesos_json': json.dumps(pesos_drogas),
        'unidades_labels_json': json.dumps(labels_unid),
        'unidades_dados_json': json.dumps(dados_unid),
        'datasets_evolucao_json': json.dumps(datasets_evolucao),
        'page_obj': page_obj,
    }
    return render(request, 'gestao/painel.html', context)

# --- 4. GESTÃO DE LOTES ---

@login_required
@transaction.atomic
def fechar_lote_manual(request):
    if request.method == "POST":
        ids = request.POST.getlist('itens_selecionados')
        if not ids:
            messages.warning(request, "Selecione ao menos um item.")
            return redirect('lotes_montagem')
        try:
            ano_atual = timezone.now().year
            count_lotes = LoteIncineracao.objects.filter(data_criacao__year=ano_atual).count() + 1
            identificador = f"LOTE-{ano_atual}-{count_lotes:03d}"
            novo_lote = LoteIncineracao.objects.create(identificador=identificador, status='ABERTO', responsavel=request.user)
            Material.objects.filter(id__in=ids).update(lote=novo_lote)
            messages.success(request, f"Lote {identificador} gerado!")
        except Exception as e:
            messages.error(request, f"Erro: {e}")
    return redirect('lotes_montagem')

@login_required
@transaction.atomic
def finalizar_lote_com_eprotocolo(request):
    if request.method == "POST":
        lote_id = request.POST.get('lote_id')
        eprotocolo = request.POST.get('eprotocolo_comando') or request.POST.get('eprotocolo_geral')
        lote = get_object_or_404(LoteIncineracao, id=lote_id)
        agora = timezone.now()
        lote.status = 'INCINERADO'
        lote.data_incineracao = agora
        lote.eprotocolo_geral = eprotocolo
        lote.save()
        Material.objects.filter(lote=lote).update(status='INCINERADO', data_incineracao=agora)
        messages.success(request, f"Lote {lote.identificador} finalizado!")
    return redirect('lotes_incineracao')

@login_required
def imprimir_certidao_lote(request, id):
    # 1. Busca o lote específico
    lote = get_object_or_404(LoteIncineracao, id=id)
    
    # 2. Busca os materiais vinculados ao lote
    # O .order_by('noticiado__ocorrencia__vara') é OBRIGATÓRIO para o {% regroup %} funcionar
    # O .select_related evita que o banco seja consultado várias vezes dentro do loop
    materiais = Material.objects.filter(lote=lote).select_related(
        'noticiado__ocorrencia', 
        'lote'
    ).order_by('noticiado__ocorrencia__vara', 'noticiado__nome')

    context = {
        'itens': materiais,
        'lote': lote,
    }
    
    return render(request, 'relatorios/certidao_destruicao.html', context)

# --- 5. LISTAGENS ---

@login_required
def custodia_lista(request):
    busca = request.GET.get('busca_bou', '').strip()
    itens = Material.objects.filter(status__in=['NO_COFRE', 'AUTORIZADO'], lote__isnull=True).select_related('noticiado__ocorrencia')
    if busca:
        itens = itens.filter(noticiado__ocorrencia__bou__icontains=busca)
    return render(request, 'gestao/custodia_lista.html', {'itens': itens})

@login_required
def conferencia_lista(request):
    # Não mude nada aqui, apenas garanta que o querySet está indo puro
    pendentes = Material.objects.filter(status='AGUARDANDO_CONFERENCIA').select_related('noticiado__ocorrencia')
    return render(request, 'gestao/conferencia_lista.html', {'pendentes': pendentes})


@login_required
def lotes_montagem(request):
    fila_autorizados = Material.objects.filter(
        status='AUTORIZADO', 
        lote__isnull=True
    ).select_related('noticiado__ocorrencia')

    # Contagem para o gatilho de sugestão
    total_na_fila = fila_autorizados.count()

    lotes_existentes = LoteIncineracao.objects.annotate(
        total_processos=Count('materiais')
    ).order_by('-id')[:8]

    context = {
        'fila_autorizados': fila_autorizados,
        'total_na_fila': total_na_fila, # Passamos a contagem exata
        'lotes_existentes': lotes_existentes,
    }
    return render(request, 'gestao/lotes_montagem.html', context)

@login_required
def lotes_incineracao(request):
    # 1. Configuração de Datas (Padrão para o Histórico)
    hoje = date.today()
    ano_atual = hoje.year
    semestre_atual = 1 if hoje.month <= 6 else 2

    # Captura dos filtros da URL
    ano_sel = request.GET.get('ano', str(ano_atual))
    semestre_sel = request.GET.get('semestre', str(semestre_atual))
    vara_sel = request.GET.get('vara')

    # Conversão para inteiros
    ano_sel_int = int(ano_sel) if ano_sel.isdigit() else ano_atual
    sem_sel_int = int(semestre_sel) if semestre_sel.isdigit() else semestre_atual

    # --- ABA 1: AGUARDANDO QUEIMA (Sempre todos, sem filtro de data) ---
    lotes_pendentes = LoteIncineracao.objects.exclude(status='INCINERADO').prefetch_related('materiais')

    # --- ABA 2: JÁ INCINERADOS (Filtrados por Ano e Semestre) ---
    mes_inicio = 1 if sem_sel_int == 1 else 7
    mes_fim = 6 if sem_sel_int == 1 else 12

    lotes_concluidos = LoteIncineracao.objects.filter(
        status='INCINERADO',
        data_incineracao__year=ano_sel_int,
        data_incineracao__month__gte=mes_inicio,
        data_incineracao__month__lte=mes_fim
    ).prefetch_related('materiais')

    # --- FILTRO DE VARA (Aplica-se apenas aos incinerados, ou ambos se desejar) ---
    if vara_sel:
        # Se quiser filtrar a vara também nos pendentes, descomente a linha abaixo:
        # lotes_pendentes = lotes_pendentes.filter(materiais__noticiado__ocorrencia__vara__iexact=vara_sel).distinct()
        
        lotes_concluidos = lotes_concluidos.filter(
            materiais__noticiado__ocorrencia__vara__iexact=vara_sel
        ).distinct()

    # --- ORGANIZAÇÃO PARA O TEMPLATE ---
    varas_raw = Material.objects.values_list('noticiado__ocorrencia__vara', flat=True).distinct()
    varas_limpas = sorted(list(set([v.upper() for v in varas_raw if v])))

    context = {
        'lotes_pendentes': lotes_pendentes.order_by('-data_criacao'),
        'lotes_concluidos': lotes_concluidos.order_by('-data_incineracao'),
        'varas_reais': varas_limpas,
        'anos_disponiveis': range(2024, ano_atual + 1),
        'filtros': {
            'ano': ano_sel_int,
            'semestre': sem_sel_int,
            'vara': vara_sel
        }
    }
    return render(request, 'gestao/lotes_semestrais.html', context)
@login_required
def cadastro_entrada(request):
    return render(request, 'gestao/cadastro_entrada.html', {'drogas_lista': DROGAS_CHOICES, 'varas_lista': VARA_CHOICES, 'graduacoes': GRADUACAO_CHOICES})

# --- 6. IMPRESSÃO ---

@login_required
def gerar_recibo(request, id):
    obj = get_object_or_404(Ocorrencia.objects.prefetch_related('noticiados__materiais'), id=id)
    return render(request, 'gestao/recibo_entrega.html', {'obj': obj, 'data_atual': timezone.now(), 'cartorario': request.user.get_full_name()})

@login_required
def imprimir_capa_lote(request, id):
    lote_objeto = get_object_or_404(LoteIncineracao, id=id)
    materiais = Material.objects.filter(lote=lote_objeto)
    peso_total = materiais.aggregate(Sum('peso_real'))['peso_real__sum'] or 0
    return render(request, 'gestao/capa_lote_pdf.html', {
        'lote': lote_objeto, 'materiais': materiais, 'peso_total_label': formatar_peso_br(peso_total), 'data_impressao': timezone.now()
    })

@login_required
def relatorio_inventario_geral(request):
    materiais_qs = Material.objects.select_related('noticiado__ocorrencia', 'lote').all().order_by('-id')
    return render(request, 'relatorios/inventario_geral.html', {'todos_materiais': materiais_qs})

@login_required
def relatorio_forum_view(request):
    vara_query = request.GET.get('vara')
    semestre = request.GET.get('semestre')
    ano = 2026
    mapeamento_vara = {'1': 'VARA_01', '2': 'VARA_02', '3': 'VARA_03'}
    vara_db = mapeamento_vara.get(vara_query)
    itens = Material.objects.filter(status='INCINERADO', lote__data_incineracao__year=ano).select_related('noticiado__ocorrencia', 'lote')
    if vara_db: itens = itens.filter(noticiado__ocorrencia__vara=vara_db)
    if semestre == '1': itens = itens.filter(lote__data_incineracao__month__lte=6)
    else: itens = itens.filter(lote__data_incineracao__month__gt=6)
    
    resumo_pesos = itens.values('substancia').annotate(total_peso=Sum('peso_real')).order_by('substancia')
    
    # Preparar resumo formatado
    resumo_formatado = []
    substancias_dict = dict(DROGAS_CHOICES)
    for r in resumo_pesos:
        resumo_formatado.append({
            'nome': substancias_dict.get(r['substancia'], r['substancia']),
            'peso': formatar_peso_br(r['total_peso'])
        })

    return render(request, 'gestao/relatorio_forum.html', {
        'itens': itens, 'vara_nome': f"{vara_query}ª Vara Criminal", 'semestre': semestre, 'ano': ano,
        'resumo_formatado': resumo_formatado, 'numero_oficio': f"{semestre}{ano}{vara_query}"
    })