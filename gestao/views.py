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
from django.db.models import Prefetch

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

            # Criação da Ocorrência
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

            # Captura as listas dos itens dinâmicos
            nomes = request.POST.getlist('nome_noticiado[]')
            substancias = request.POST.getlist('substancia[]')
            unidades = request.POST.getlist('unidade[]') # <-- CAPTURA UNIDADE (G ou UN)
            pesos = request.POST.getlist('peso_estimado[]')
            lacres = request.POST.getlist('lacre[]')

            for i in range(len(nomes)):
                if nomes[i].strip():
                    noticiado = Noticiado.objects.create(
                        ocorrencia=ocorrencia,
                        nome=nomes[i].strip().upper()
                    )
                    
                    peso_limpo = float(pesos[i].replace(',', '.')) if i < len(pesos) and pesos[i] else 0
                    
                    Material.objects.create(
                        noticiado=noticiado,
                        substancia=substancias[i],
                        unidade=unidades[i] if i < len(unidades) else 'G', # <-- SALVA G OU UN
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
        
        # Aqui usamos o método que você criou no Model!
        RegistroHistorico.objects.create(
            material=material, 
            usuario=request.user, 
            status_novo='NO_COFRE',
            observacao=f"Pesagem Oficial: {material.peso_formatado()}. Conferido por {request.user.get_full_name()}."
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


def painel_principal(request):
    hoje = datetime.now()
    
    # 1. CAPTURA DOS FILTROS DA URL
    ano_selecionado = int(request.GET.get('ano', hoje.year))
    substancia_filtro = request.GET.get('substancia', 'todas')
    periodo_selecionado = request.GET.get('periodo', 'ano')

    # 2. DEFINIÇÃO DO INTERVALO DE MESES (Filtro de Semestre)
    if periodo_selecionado == 's1':
        mes_inicio, mes_fim = 1, 6
    elif periodo_selecionado == 's2':
        mes_inicio, mes_fim = 7, 12
    else:
        mes_inicio, mes_fim = 1, 12

    # --- SEÇÃO A: ESTOQUE ATUAL (CARDS DE INVENTÁRIO REAL) ---
    filtros_estoque = Q()
    if substancia_filtro != 'todas':
        filtros_estoque &= Q(substancia=substancia_filtro)
    
    # Saldo Oficial (Somente o que já foi conferido)
    saldo_oficial = Material.objects.filter(
        filtros_estoque, 
        status='NO_COFRE'
    ).aggregate(total=Sum('peso_real'))['total'] or 0

    # Pendente de Conferência (O que entrou mas ainda não foi conferido)
    saldo_pendente = Material.objects.filter(
        filtros_estoque, 
        status='AGUARDANDO_CONFERENCIA'
    ).aggregate(total=Sum('peso_estimado'))['total'] or 0


    # --- SEÇÃO B: PRODUÇÃO DO PERÍODO (GRÁFICOS E CARDS DE FLUXO) ---
    filtros_periodo = Q(noticiado__ocorrencia__data_registro__year=ano_selecionado)
    filtros_periodo &= Q(noticiado__ocorrencia__data_registro__month__range=(mes_inicio, mes_fim))
    
    if substancia_filtro != 'todas':
        filtros_periodo &= Q(substancia=substancia_filtro)

    materiais_periodo = Material.objects.filter(filtros_periodo)

    # 1. EVOLUÇÃO MENSAL (GRÁFICO DE LINHA)
    datasets_evolucao = []
    drogas_grafico = [substancia_filtro] if substancia_filtro != 'todas' else ['MACONHA', 'COCAINA', 'CRACK']
    cores = {'MACONHA': '#1a3a2a', 'COCAINA': '#3498db', 'CRACK': '#e74c3c'}

    for droga in drogas_grafico:
        dados_meses = []
        for mes in range(1, 13):
            if mes < mes_inicio or mes > mes_fim:
                dados_meses.append(0)
            else:
                soma = materiais_periodo.filter(
                    substancia=droga, 
                    noticiado__ocorrencia__data_registro__month=mes
                ).aggregate(total=Sum('peso_real'))['total'] or 0
                dados_meses.append(float(soma))
        
        datasets_evolucao.append({
            'label': dict(DROGAS_CHOICES).get(droga, droga),
            'data': dados_meses,
            'borderColor': cores.get(droga, '#333'),
            'backgroundColor': cores.get(droga, '#333'),
            'tension': 0.3,
            'fill': False
        })

    # 2. SEPARAÇÃO PARA OS GRÁFICOS DE PIZZA (PESO vs UNIDADE)
    # Materiais por PESO (Grama/Quilo)
    resumo_peso = materiais_periodo.filter(unidade='G').values('substancia').annotate(
        total=Sum('peso_real')
    ).order_by('-total')
    
    labels_peso = [dict(DROGAS_CHOICES).get(x['substancia'], x['substancia']) for x in resumo_peso]
    valores_peso = [float(x['total'] or 0) for x in resumo_peso]

    # Materiais por UNIDADE (Pé de maconha, comprimidos, etc)
    # CORREÇÃO AQUI: Usei 'resumo_unidade' consistentemente agora
    resumo_unidade = materiais_periodo.filter(unidade='UN').values('substancia').annotate(
        total=Sum('peso_real')
    ).order_by('-total')
    
    labels_unid_pizza = [dict(DROGAS_CHOICES).get(x['substancia'], x['substancia']) for x in resumo_unidade]
    valores_unid_pizza = [float(x['total'] or 0) for x in resumo_unidade]

    # 3. PRODUTIVIDADE UNIDADE PM (BARRAS)
    resumo_pm = materiais_periodo.values('noticiado__ocorrencia__unidade_origem').annotate(
        total=Sum('peso_real')
    ).order_by('-total')
    
    labels_pm = [x['noticiado__ocorrencia__unidade_origem'] or "OUTROS" for x in resumo_pm]
    valores_pm = [float(x['total'] or 0) for x in resumo_pm]

    # 4. CARDS DE RESULTADO DO PERÍODO
    incinerado_periodo = materiais_periodo.filter(status='INCINERADO').aggregate(total=Sum('peso_real'))['total'] or 0
    total_bous = materiais_periodo.aggregate(total=Count('noticiado__ocorrencia', distinct=True))['total'] or 0

    # 5. MONTAGEM DO CONTEXTO
    context = {
        'ano_atual': ano_selecionado,
        'substancia_selecionada': substancia_filtro,
        'periodo_selecionado': periodo_selecionado,
        'DROGAS_CHOICES': DROGAS_CHOICES,
        'anos_disponiveis': range(2023, hoje.year + 1),
        
        'no_cofre_label': formatar_peso_br(saldo_oficial),
        'pendente_conferencia_label': formatar_peso_br(saldo_pendente),
        'incinerado_label': formatar_peso_br(incinerado_periodo),
        'total_processos': total_bous,
        
        'datasets_evolucao_json': json.dumps(datasets_evolucao),
        'labels_peso_json': json.dumps(labels_peso),
        'valores_peso_json': json.dumps(valores_peso),
        'labels_unid_pizza_json': json.dumps(labels_unid_pizza),
        'valores_unid_pizza_json': json.dumps(valores_unid_pizza),
        'unidades_labels_json': json.dumps(labels_pm),
        'unidades_dados_json': json.dumps(valores_pm),
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
    lote = get_object_or_404(LoteIncineracao, id=id)
    vara_filtrada = request.GET.get('vara')

    # Buscamos os materiais
    materiais_qs = Material.objects.filter(lote=lote).select_related(
        'noticiado__ocorrencia', 'lote'
    )

    # Se filtrou por vara, aplicamos o filtro ANTES de qualquer outra coisa
    if vara_filtrada and vara_filtrada != "":
        materiais_qs = materiais_qs.filter(noticiado__ocorrencia__vara__iexact=vara_filtrada)

    # ORDENAÇÃO É CRUCIAL: Primeiro por vara, depois por nome
    materiais = materiais_qs.order_by('noticiado__ocorrencia__vara', 'noticiado__nome')

    context = {
        'itens': materiais,
        'lote': lote,
        'vara_selecionada': vara_filtrada,
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


 # Importação importante!

@login_required
def lotes_incineracao(request):
    hoje = date.today()
    ano_atual = hoje.year
    semestre_atual = 1 if hoje.month <= 6 else 2

    ano_sel = request.GET.get('ano')
    semestre_sel = request.GET.get('semestre')
    vara_sel = request.GET.get('vara')

    ano_sel_int = int(ano_sel) if (ano_sel and ano_sel.isdigit()) else ano_atual
    sem_sel_int = int(semestre_sel) if (semestre_sel and semestre_sel.isdigit()) else semestre_atual

    # --- ABA 1: PENDENTES ---
    lotes_pendentes = LoteIncineracao.objects.exclude(status='INCINERADO')

    # --- ABA 2: CONCLUÍDOS ---
    mes_inicio = 1 if sem_sel_int == 1 else 7
    mes_fim = 6 if sem_sel_int == 1 else 12

    lotes_concluidos = LoteIncineracao.objects.filter(
        status='INCINERADO',
        data_incineracao__year=ano_sel_int,
        data_incineracao__month__gte=mes_inicio,
        data_incineracao__month__lte=mes_fim
    )

    # --- A MÁGICA DO FILTRO ESPECÍFICO ---
    if vara_sel and vara_sel != "":
        # 1. Filtramos os lotes que possuem PELO MENOS UM material daquela vara
        lotes_concluidos = lotes_concluidos.filter(
            materiais__noticiado__ocorrencia__vara__iexact=vara_sel
        ).distinct()

        # 2. Aqui está o segredo: Dizemos ao Django para carregar APENAS os materiais 
        # daquela vara específica quando ele for desenhar o lote no HTML
        materiais_filtrados = Material.objects.filter(noticiado__ocorrencia__vara__iexact=vara_sel)
        lotes_concluidos = lotes_concluidos.prefetch_related(
            Prefetch('materiais', queryset=materiais_filtrados)
        )
        
        # Fazemos o mesmo para os pendentes se você quiser filtrar a vara lá também
        lotes_pendentes = lotes_pendentes.filter(
            materiais__noticiado__ocorrencia__vara__iexact=vara_sel
        ).distinct().prefetch_related(
            Prefetch('materiais', queryset=materiais_filtrados)
        )
    else:
        # Se não houver vara selecionada, trazemos tudo normalmente
        lotes_concluidos = lotes_concluidos.prefetch_related('materiais')
        lotes_pendentes = lotes_pendentes.prefetch_related('materiais')

    # Lista de varas para o select
    varas_raw = Material.objects.values_list('noticiado__ocorrencia__vara', flat=True).distinct()
    varas_limpas = sorted(list(set([v.upper() for v in varas_raw if v])))

    # Anos Infinitos
    primeiro_lote = LoteIncineracao.objects.order_by('data_criacao').first()
    ano_inicio = primeiro_lote.data_criacao.year if primeiro_lote else 2024
    anos_disponiveis = sorted(list(range(ano_inicio, ano_atual + 1)), reverse=True)

    context = {
        'lotes_pendentes': lotes_pendentes.order_by('-data_criacao'),
        'lotes_concluidos': lotes_concluidos.order_by('-data_incineracao'),
        'varas_reais': varas_limpas,
        'anos_disponiveis': anos_disponiveis,
        'filtros': {'ano': ano_sel_int, 'semestre': sem_sel_int, 'vara': vara_sel}
    }
    return render(request, 'gestao/lotes_semestrais.html', context)


@login_required
def cadastro_entrada(request):
    # Passamos as listas para o template carregar os selects
    context = {
        'DROGAS_CHOICES': DROGAS_CHOICES, 
        'VARA_CHOICES': VARA_CHOICES, 
        'GRADUACAO_CHOICES': GRADUACAO_CHOICES
    }
    return render(request, 'gestao/cadastro_entrada.html', context)
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