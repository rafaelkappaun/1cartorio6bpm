from datetime import datetime, date
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
from django.db.models import Prefetch
from .models import (
    DROGAS_CHOICES, GRADUACAO_CHOICES, VARA_CHOICES, 
    Ocorrencia, Material, Noticiado, LoteIncineracao, RegistroHistorico
)

# --- FUNÇÃO AUXILIAR DE FORMATAÇÃO ---
def formatar_peso_br(valor_gramas):
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

            # Criação da Ocorrência - Ajustado para data_registro_bou
            ocorrencia = Ocorrencia.objects.create(
                bou=bou,
                data_registro_bou=request.POST.get('data_registro'),
                vara=request.POST.get('vara'),
                processo=processo if processo else None,
                policial_nome=request.POST.get('policial_nome', '').upper(),
                policial_graduacao=request.POST.get('policial_graduacao'),
                rg_policial=request.POST.get('rg_policial'),
                unidade_origem=request.POST.get('unidade_origem'),
                unidade_especifica=request.POST.get('unidade_especifica'), 
                criado_por=request.user
            )

            nomes = request.POST.getlist('nome_noticiado[]')
            substancias = request.POST.getlist('substancia[]')
            unidades = request.POST.getlist('unidade[]')
            pesos = request.POST.getlist('peso_estimado[]')
            lacres = request.POST.getlist('lacre[]')

            for i in range(len(nomes)):
                if nomes[i].strip():
                    noticiado = Noticiado.objects.create(
                        ocorrencia=ocorrencia,
                        nome=nomes[i].strip().upper()
                    )
                    
                    peso_limpo = float(pesos[i].replace(',', '.')) if i < len(pesos) and pesos[i] else 0
                    
                    # Status inicial da Cadeia de Custódia: RECEBIDO
                    Material.objects.create(
                        noticiado=noticiado,
                        substancia=substancias[i],
                        unidade=unidades[i] if i < len(unidades) else 'G',
                        peso_estimado=peso_limpo,
                        numero_lacre=lacres[i].strip() if i < len(lacres) else None,
                        status='RECEBIDO' 
                    )

            messages.success(request, f"BOU {bou} registrado com sucesso!")
            return redirect(reverse('cadastro_entrada') + f'?sucesso_id={ocorrencia.id}')
        except Exception as e:
            messages.error(request, f"Erro operacional no cadastro: {e}")
            return redirect('cadastro_entrada')
    return redirect('cadastro_entrada')

# --- 2. MOVIMENTAÇÃO (AUDITORIA) ---

@login_required
@transaction.atomic
def confirmar_conferencia(request, id):
    if request.method == "POST":
        material = get_object_or_404(Material, id=id)
        peso_txt = request.POST.get('peso_real', '0').replace(',', '.')
        
        # ATUALIZAÇÃO SEGURA:
        material.peso_real = float(peso_txt)
        material.status = 'ARMAZENADO'
        # Removido: responsavel_conferencia (não existe no model)
        # Removido: data_conferencia_fisica (não existe no model)
        material.localizacao_no_cofre = request.POST.get('localizacao', 'Cofre Central')
        material.save()
        
        # O histórico agora é a única prova de QUEM fez a ação
        RegistroHistorico.objects.create(
            material=material, 
            criado_por=request.user, 
            status_na_epoca='ARMAZENADO',
            observacao=f"CONFERÊNCIA FÍSICA: Pesagem Real {material.peso_formatado()}. Local: {material.localizacao_no_cofre}"
        )
        messages.success(request, f"BOU {material.noticiado.ocorrencia.bou} armazenado com sucesso.")
    return redirect('conferencia_lista')

@login_required
@transaction.atomic
def confirmar_autorizacao(request, id):
    if request.method == "POST":
        material = get_object_or_404(Material, id=id)
        material.status = 'AUTORIZADO'
        material.save()

        # Registro de quem conferiu o Projudi
        RegistroHistorico.objects.create(
            material=material, 
            criado_por=request.user, 
            status_na_epoca='AUTORIZADO',
            observacao="CONFERÊNCIA PROJUDI: Despacho judicial verificado. Pronto para incineração."
        )
        messages.success(request, f"BOU {material.noticiado.ocorrencia.bou} autorizado para queima!")
    return redirect('custodia_lista')

# --- 3. DASHBOARD ---



def painel_principal(request):
    hoje = datetime.now()
    # 1. Captura de filtros com fallback seguro
    ano_selecionado = int(request.GET.get('ano', hoje.year))
    substancia_filtro = request.GET.get('substancia', 'todas')
    periodo_selecionado = request.GET.get('periodo', 'ano')

    mes_inicio, mes_fim = (1, 12)
    if periodo_selecionado == 's1': mes_inicio, mes_fim = 1, 6
    elif periodo_selecionado == 's2': mes_inicio, mes_fim = 7, 12

    # 2. Cálculos de Estoque Físico (Independente do período de apreensão)
    # Mostra o que TEM no cofre hoje, filtrado apenas pela substância
    q_estoque = Q()
    if substancia_filtro != 'todas':
        q_estoque &= Q(substancia=substancia_filtro)
    
    saldo_oficial = Material.objects.filter(
        q_estoque, 
        status__in=['ARMAZENADO', 'AUTORIZADO']
    ).aggregate(total=Sum('peso_real'))['total'] or 0

    saldo_pendente = Material.objects.filter(
        q_estoque, 
        status='RECEBIDO'
    ).aggregate(total=Sum('peso_estimado'))['total'] or 0

    # 3. Materiais do Período (Para Gráficos e Estatísticas)
    # Otimizado com select_related para evitar múltiplas idas ao banco
    filtros_periodo = Q(noticiado__ocorrencia__data_registro_bou__year=ano_selecionado)
    filtros_periodo &= Q(noticiado__ocorrencia__data_registro_bou__month__range=(mes_inicio, mes_fim))
    
    if substancia_filtro != 'todas':
        filtros_periodo &= Q(substancia=substancia_filtro)

    materiais_periodo = Material.objects.filter(filtros_periodo).select_related('noticiado__ocorrencia')

    # 4. Evolução Mensal Otimizada (Uma única query por droga)
    datasets_evolucao = []
    drogas_alvo = [substancia_filtro] if substancia_filtro != 'todas' else ['MACONHA', 'COCAINA', 'CRACK']
    cores = {'MACONHA': '#1a3a2a', 'COCAINA': '#3498db', 'CRACK': '#e74c3c'}

    for droga in drogas_alvo:
        # Busca a soma agrupada por mês de uma só vez
        vendas_mes = materiais_periodo.filter(substancia=droga)\
            .annotate(mes=ExtractMonth('noticiado__ocorrencia__data_registro_bou'))\
            .values('mes')\
            .annotate(total=Sum('peso_real'))\
            .order_by('mes')

        # Mapeia o resultado para a lista de 12 meses
        mapa_meses = {item['mes']: float(item['total']) for item in vendas_mes}
        dados_meses = [mapa_meses.get(m, 0.0) if mes_inicio <= m <= mes_fim else 0.0 for m in range(1, 13)]
        
        datasets_evolucao.append({
            'label': dict(DROGAS_CHOICES).get(droga, droga),
            'data': dados_meses,
            'borderColor': cores.get(droga, '#333'),
            'backgroundColor': cores.get(droga, '#333'),
            'tension': 0.3,
        })

    # 5. Agrupamentos para os Gráficos de Pizza/Barra
    def get_json_data(queryset, field, label_dict=None):
        dados = queryset.values(field).annotate(total=Sum('peso_real')).order_by('-total')
        labels = []
        for x in dados:
            val = x[field]
            labels.append(label_dict.get(val, val) if label_dict else (val or "OUTROS"))
        valores = [float(x['total'] or 0) for x in dados]
        return labels, valores

    labels_peso, valores_peso = get_json_data(materiais_periodo.filter(unidade='G'), 'substancia', dict(DROGAS_CHOICES))
    labels_unid, valores_unid = get_json_data(materiais_periodo.filter(unidade='UN'), 'substancia', dict(DROGAS_CHOICES))
    labels_pm, valores_pm = get_json_data(materiais_periodo, 'noticiado__ocorrencia__unidade_origem')

    # 6. Movimentações Recentes (Cadeia de Custódia)
    ultimos_registros = RegistroHistorico.objects.select_related('material__noticiado__ocorrencia', 'criado_por').order_by('-data_criacao')[:10]

    context = {
        'ano_atual': ano_selecionado,
        'substancia_selecionada': substancia_filtro,
        'periodo_selecionado': periodo_selecionado,
        'DROGAS_CHOICES': DROGAS_CHOICES,
        'anos_disponiveis': range(hoje.year - 3, hoje.year + 1),
        'no_cofre_label': formatar_peso_br(saldo_oficial),
        'pendente_conferencia_label': formatar_peso_br(saldo_pendente),
        'incinerado_label': formatar_peso_br(materiais_periodo.filter(status='INCINERADO').aggregate(total=Sum('peso_real'))['total'] or 0),
        'ultimos_registros': ultimos_registros,
        'datasets_evolucao_json': json.dumps(datasets_evolucao),
        'labels_peso_json': json.dumps(labels_peso),
        'valores_peso_json': json.dumps(valores_peso),
        'labels_unid_pizza_json': json.dumps(labels_unid),
        'valores_unid_pizza_json': json.dumps(valores_unid),
        'unidades_labels_json': json.dumps(labels_pm),
        'unidades_dados_json': json.dumps(valores_pm),
    }
    return render(request, 'gestao/painel.html', context)

# --- 4. LISTAGENS ---

@login_required
def custodia_lista(request):
    busca = request.GET.get('busca_bou', '').strip()
    # Filtra pelos novos status físicos
    itens = Material.objects.filter(status__in=['ARMAZENADO', 'AUTORIZADO'], lote__isnull=True).select_related('noticiado__ocorrencia')
    if busca:
        itens = itens.filter(noticiado__ocorrencia__bou__icontains=busca)
    return render(request, 'gestao/custodia_lista.html', {'itens': itens})

@login_required
def conferencia_lista(request):
    # Status inicial: RECEBIDO
    pendentes = Material.objects.filter(status='RECEBIDO').select_related('noticiado__ocorrencia')
    return render(request, 'gestao/conferencia_lista.html', {'pendentes': pendentes})

# --- GESTÃO DE LOTES E OUTROS ---
# (As demais funções seguem a mesma lógica de substituição de data_registro por data_registro_bou)

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
        
        # Atualiza materiais e gera histórico automático pelo signal
        Material.objects.filter(lote=lote).update(status='INCINERADO')
        
        messages.success(request, f"Lote {lote.identificador} incinerado com sucesso!")
    return redirect('lotes_incineracao')

@login_required
def cadastro_entrada(request):
    context = {
        'DROGAS_CHOICES': DROGAS_CHOICES, 
        'VARA_CHOICES': VARA_CHOICES, 
        'GRADUACAO_CHOICES': GRADUACAO_CHOICES
    }
    return render(request, 'gestao/cadastro_entrada.html', context)

# --- FUNÇÕES QUE FALTARAM (LISTAGENS E LOTES) ---

@login_required
def lotes_montagem(request):
    # Agora ele busca tanto os que você já autorizou quanto os que só foram conferidos
    fila_autorizados = Material.objects.filter(
        status__in=['ARMAZENADO', 'AUTORIZADO'], 
        lote__isnull=True
    ).select_related('noticiado__ocorrencia')

    total_na_fila = fila_autorizados.count()
    lotes_existentes = LoteIncineracao.objects.annotate(
        total_processos=Count('materiais')
    ).order_by('-id')[:8]

    context = {
        'fila_autorizados': fila_autorizados,
        'total_na_fila': total_na_fila,
        'lotes_existentes': lotes_existentes,
    }
    return render(request, 'gestao/lotes_montagem.html', context)

@login_required
@transaction.atomic
def fechar_lote_manual(request):
    """ Agrupa materiais selecionados em um novo Lote de Incineração """
    if request.method == "POST":
        ids = request.POST.getlist('itens_selecionados')
        if not ids:
            messages.warning(request, "Selecione ao menos um item para criar o lote.")
            return redirect('lotes_montagem')
        try:
            ano_atual = timezone.now().year
            # Conta quantos lotes já existem no ano para gerar o número sequencial
            count_lotes = LoteIncineracao.objects.filter(data_criacao__year=ano_atual).count() + 1
            identificador = f"LOTE-{ano_atual}-{count_lotes:03d}"
            
            novo_lote = LoteIncineracao.objects.create(
                identificador=identificador, 
                status='ABERTO', 
                criado_por=request.user
            )
            
            # Vincula os materiais ao lote
            Material.objects.filter(id__in=ids).update(lote=novo_lote)
            
            messages.success(request, f"Lote {identificador} gerado com sucesso!")
        except Exception as e:
            messages.error(request, f"Erro ao gerar lote: {e}")
    return redirect('lotes_montagem')

@login_required
def lotes_incineracao(request):
    """ Listagem semestral de lotes (Concluídos e Pendentes) """
    hoje = date.today()
    ano_atual = hoje.year
    semestre_atual = 1 if hoje.month <= 6 else 2

    # Captura filtros da URL
    ano_sel = request.GET.get('ano')
    semestre_sel = request.GET.get('semestre')
    vara_sel = request.GET.get('vara')

    ano_sel_int = int(ano_sel) if (ano_sel and ano_sel.isdigit()) else ano_atual
    sem_sel_int = int(semestre_sel) if (semestre_sel and semestre_sel.isdigit()) else semestre_atual

    # Lotes que ainda não foram queimados
    lotes_pendentes = LoteIncineracao.objects.exclude(status='INCINERADO').prefetch_related('materiais')

    # Lotes concluídos com filtro de data
    mes_inicio = 1 if sem_sel_int == 1 else 7
    mes_fim = 6 if sem_sel_int == 1 else 12

    lotes_concluidos = LoteIncineracao.objects.filter(
        status='INCINERADO',
        data_incineracao__year=ano_sel_int,
        data_incineracao__month__gte=mes_inicio,
        data_incineracao__month__lte=mes_fim
    ).prefetch_related('materiais')

    # Filtro opcional por Vara Criminal
    if vara_sel:
        lotes_concluidos = lotes_concluidos.filter(materiais__noticiado__ocorrencia__vara=vara_sel).distinct()
        lotes_pendentes = lotes_pendentes.filter(materiais__noticiado__ocorrencia__vara=vara_sel).distinct()

    # Para os selects do template
    anos_disponiveis = sorted(list(range(2024, ano_atual + 1)), reverse=True)

    context = {
        'lotes_pendentes': lotes_pendentes.order_by('-data_criacao'),
        'lotes_concluidos': lotes_concluidos.order_by('-data_incineracao'),
        'anos_disponiveis': anos_disponiveis,
        'filtros': {'ano': ano_sel_int, 'semestre': sem_sel_int, 'vara': vara_sel}
    }
    return render(request, 'gestao/lotes_semestrais.html', context)

# --- 6. IMPRESSÃO E RELATÓRIOS (AUDITORIA FÍSICA) ---

@login_required
def gerar_recibo(request, id):
    """ Gera o comprovante de entrega para o policial (BOU) """
    obj = get_object_or_404(Ocorrencia.objects.prefetch_related('noticiados__materiais'), id=id)
    return render(request, 'gestao/recibo_entrega.html', {
        'obj': obj, 
        'data_atual': timezone.now(), 
        'cartorario': request.user.get_full_name()
    })

@login_required
def imprimir_capa_lote(request, id):
    """ Gera o documento de face para o Lote de Incineração """
    lote_objeto = get_object_or_404(LoteIncineracao, id=id)
    materiais = Material.objects.filter(lote=lote_objeto).select_related('noticiado__ocorrencia')
    
    # Soma o peso total do lote (usando o peso real conferido)
    peso_total = materiais.aggregate(Sum('peso_real'))['peso_real__sum'] or 0
    
    return render(request, 'gestao/capa_lote_pdf.html', {
        'lote': lote_objeto, 
        'materiais': materiais, 
        'peso_total_label': formatar_peso_br(peso_total), 
        'data_impressao': timezone.now()
    })

@login_required
def imprimir_certidao_lote(request, id):
    """ Certidão detalhada para o Juízo/Promotoria sobre a destruição """
    lote = get_object_or_404(LoteIncineracao, id=id)
    vara_filtrada = request.GET.get('vara')

    materiais_qs = Material.objects.filter(lote=lote).select_related(
        'noticiado__ocorrencia', 'lote'
    )

    if vara_filtrada:
        materiais_qs = materiais_qs.filter(noticiado__ocorrencia__vara__iexact=vara_filtrada)

    # Ordenação por vara e nome para facilitar a conferência do auditor
    materiais = materiais_qs.order_by('noticiado__ocorrencia__vara', 'noticiado__nome')

    context = {
        'itens': materiais,
        'lote': lote,
        'vara_selecionada': vara_filtrada,
    }
    return render(request, 'relatorios/certidao_destruicao.html', context)

@login_required
def relatorio_inventario_geral(request):
    """ Visão geral de tudo com rastro de quem manipulou """
    materiais_qs = Material.objects.select_related(
        'noticiado__ocorrencia', 
        'noticiado__ocorrencia__criado_por', # Traz quem cadastrou
        'lote'
    ).prefetch_related(
        Prefetch('historico', queryset=RegistroHistorico.objects.select_related('criado_por')) # Traz quem conferiu
    ).all().order_by('-id')
    
    return render(request, 'relatorios/inventario_geral.html', {
        'todos_materiais': materiais_qs
    })

# --- 7. RELATÓRIOS ESPECÍFICOS (VARA CRIMINAL) ---

@login_required
def relatorio_forum_view(request):
    """
    Gera o relatório de incineração consolidado por Vara, 
    geralmente usado para anexar ao Ofício de destruição.
    """
    vara_query = request.GET.get('vara')
    semestre = request.GET.get('semestre')
    ano = 2026  # Ou use datetime.now().year para ser dinâmico
    
    # Mapeia o número da vara para o Choice do Model, se necessário
    mapeamento_vara = {'1': 'VARA_01', '2': 'VARA_02', '3': 'VARA_03'}
    vara_db = mapeamento_vara.get(vara_query, vara_query)
    
    # Filtra apenas o que já foi incinerado no ano/semestre para aquela Vara
    itens = Material.objects.filter(
        status='INCINERADO', 
        lote__data_incineracao__year=ano
    ).select_related('noticiado__ocorrencia', 'lote')
    
    if vara_db:
        itens = itens.filter(noticiado__ocorrencia__vara=vara_db)
    
    if semestre == '1':
        itens = itens.filter(lote__data_incineracao__month__lte=6)
    elif semestre == '2':
        itens = itens.filter(lote__data_incineracao__month__gt=6)
    
    # Agrupa por substância para o resumo da auditoria
    resumo_pesos = itens.values('substancia').annotate(
        total_peso=Sum('peso_real')
    ).order_by('substancia')
    
    # Prepara o resumo formatado com nomes legíveis
    resumo_formatado = []
    substancias_dict = dict(DROGAS_CHOICES)
    for r in resumo_pesos:
        resumo_formatado.append({
            'nome': substancias_dict.get(r['substancia'], r['substancia']),
            'peso': formatar_peso_br(r['total_peso'])
        })

    return render(request, 'gestao/relatorio_forum.html', {
        'itens': itens,
        'vara_nome': f"{vara_query}ª Vara Criminal" if vara_query else "Todas as Varas",
        'semestre': semestre,
        'ano': ano,
        'resumo_formatado': resumo_formatado,
        'numero_oficio': f"{semestre}/{ano}-{vara_query or 'GERAL'}"
    })


@login_required
def auditoria_lista(request):
    query = request.GET.get('q')
    materiais = Material.objects.select_related('noticiado__ocorrencia').all()
    
    if query:
        materiais = materiais.filter(
            Q(noticiado__ocorrencia__bou__icontains=query) |
            Q(numero_lacre__icontains=query)
        )
    
    return render(request, 'gestao/auditoria_lista.html', {'materiais': materiais, 'query': query})

@login_required
def detalhe_auditoria(request, material_id):
    material = get_object_or_404(Material, id=material_id)
    historico = material.historico.all().order_by('-data_criacao')
    return render(request, 'gestao/detalhe_auditoria.html', {'material': material, 'historico': historico})