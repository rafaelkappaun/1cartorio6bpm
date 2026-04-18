from datetime import datetime, date
import json
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Sum, Count, Q, Max, Prefetch
from django.db.models.functions import ExtractMonth, ExtractYear, Coalesce, TruncMonth
from django.db.models.fields import DecimalField
from django.core.paginator import Paginator
from django.conf import settings
from django.http import HttpResponse
from .models import (
    DROGAS_CHOICES, GRADUACAO_CHOICES, VARA_CHOICES, CATEGORIA_CHOICES, STATUS_CUSTODIA_CHOICES,
    Ocorrencia, Material, Noticiado, LoteIncineracao, RegistroHistorico, CaixaIncineracao
)
from . import documentos_services


def _aplicar_filtros_material(qs, filtros):
    if filtros.get('categoria'):
        qs = qs.filter(categoria=filtros['categoria'])
    if filtros.get('substancia'):
        qs = qs.filter(substancia=filtros['substancia'])
    if filtros.get('status'):
        qs = qs.filter(status=filtros['status'])
    if filtros.get('vara'):
        qs = qs.filter(noticiado__ocorrencia__vara=filtros['vara'])
    if filtros.get('natureza_penal'):
        qs = qs.filter(noticiado__ocorrencia__natureza_penal__icontains=filtros['natureza_penal'])
    if filtros.get('unidade_origem'):
        qs = qs.filter(noticiado__ocorrencia__unidade_origem=filtros['unidade_origem'])
    if filtros.get('ano'):
        qs = qs.filter(noticiado__ocorrencia__data_registro_bou__year=filtros['ano'])
    if filtros.get('semestre'):
        sem = int(filtros['semestre'])
        if sem == 1:
            qs = qs.filter(noticiado__ocorrencia__data_registro_bou__month__range=(1, 6))
        else:
            qs = qs.filter(noticiado__ocorrencia__data_registro_bou__month__range=(7, 12))
    if filtros.get('data_inicio'):
        qs = qs.filter(data_criacao__date__gte=filtros['data_inicio'])
    if filtros.get('data_fim'):
        qs = qs.filter(data_criacao__date__lte=filtros['data_fim'])
    return qs


def _resumir_material(qs):
    cat_map = dict([
        ('ENTORPECENTE', 'Entorpecentes'), ('DINHEIRO', 'Dinheiro/Valores'),
        ('SOM', 'Aparelho de Som'), ('FACA', 'Arma Branca'),
        ('SIMULACRO', 'Simulacro'), ('OUTROS', 'Outros'),
    ])
    status_map = dict([
        ('RECEBIDO', 'Recebido'), ('ARMAZENADO', 'Armazenado'),
        ('AUTORIZADO', 'Autorizado'), ('AGUARDANDO_INCINERACAO', 'Aguardando Incineração'),
        ('INCINERADO', 'Incinerado'), ('ENTREGUE_AO_JUDICIARIO', 'Entregue ao Judiciário'),
    ])
    
    total_materiais = qs.count()
    total_noticiados = qs.values('noticiado').distinct().count()
    Bous = qs.values('noticiado__ocorrencia__bou').distinct().count()
    peso_total = float(
        qs.filter(categoria='ENTORPECENTE')
        .aggregate(total=Sum(Coalesce('peso_real', 'peso_estimado', output_field=DecimalField())))['total'] or 0
    )
    
    por_categoria = list(
        qs.values('categoria')
        .annotate(total=Count('id'), peso=Sum(Coalesce('peso_real', 'peso_estimado', output_field=DecimalField())))
        .order_by('-total')
    )
    for item in por_categoria:
        item['label'] = cat_map.get(item['categoria'], item['categoria'])
        item['peso'] = float(item['peso'] or 0)
    
    por_substancia = list(
        qs.filter(categoria='ENTORPECENTE')
        .values('substancia')
        .annotate(total=Count('id'), peso=Sum(Coalesce('peso_real', 'peso_estimado', output_field=DecimalField())))
        .order_by('-total')
    )
    subst_map = dict(DROGAS_CHOICES)
    for item in por_substancia:
        item['label'] = subst_map.get(item['substancia'], item['substancia'] or 'Não especificada')
        item['peso'] = float(item['peso'] or 0)
    
    por_status = list(qs.values('status').annotate(total=Count('id')).order_by('-total'))
    for item in por_status:
        item['label'] = status_map.get(item['status'], item['status'])
    
    por_natureza = list(
        qs.filter(noticiado__ocorrencia__natureza_penal__isnull=False)
        .exclude(noticiado__ocorrencia__natureza_penal='')
        .values('noticiado__ocorrencia__natureza_penal')
        .annotate(total=Count('id'))
        .order_by('-total')[:15]
    )
    for item in por_natureza:
        item['natureza'] = item.pop('noticiado__ocorrencia__natureza_penal')
    
    por_unidade = list(
        qs.values('noticiado__ocorrencia__unidade_origem')
        .annotate(total=Count('id'), Bous=Count('noticiado__ocorrencia__bou', distinct=True))
        .order_by('-total')[:10]
    )
    for item in por_unidade:
        item['unidade'] = item.pop('noticiado__ocorrencia__unidade_origem')
    
    por_mes = list(
        qs.annotate(mes=TruncMonth('noticiado__ocorrencia__data_registro_bou'))
        .values('mes')
        .annotate(total=Count('id'))
        .order_by('mes')
    )
    for item in por_mes:
        if item['mes']:
            item['mes_label'] = item['mes'].strftime('%B/%Y').title()
            item['mes'] = item['mes'].isoformat()
    
    return {
        'total_materiais': total_materiais,
        'total_noticiados': total_noticiados,
        'total_bous': Bous,
        'peso_total_gramas': peso_total,
    }, por_categoria, por_substancia, por_status, por_natureza, por_unidade, por_mes

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

            # Criação da Ocorrência
            ocorrencia = Ocorrencia.objects.create(
                bou=bou,
                data_registro_bou=request.POST.get('data_registro'),
                vara=request.POST.get('vara'),
                processo=processo if processo else None,
                policial_nome=request.POST.get('policial_nome', '').upper(),
                policial_graduacao=request.POST.get('policial_graduacao'),
                rg_policial=request.POST.get('rg_policial'),
                unidade_origem=request.POST.get('unidade_origem'),
                criado_por=request.user
            )

            # Captura listas do POST
            nomes = request.POST.getlist('nome_noticiado[]')
            categorias = request.POST.getlist('categoria[]')
            substancias = request.POST.getlist('substancia[]')
            unidades = request.POST.getlist('unidade[]')
            pesos = request.POST.getlist('peso_estimado[]')
            valores = request.POST.getlist('valor_monetario[]')
            descricoes = request.POST.getlist('descricao_geral[]')
            lacres = request.POST.getlist('lacre[]')

            for i in range(len(nomes)):
                if nomes[i].strip():
                    noticiado = Noticiado.objects.create(
                        ocorrencia=ocorrencia,
                        nome=nomes[i].strip().upper()
                    )
                    
                    categoria = categorias[i] if i < len(categorias) else 'ENTORPECENTE'
                    
                    # Limpeza de valores numéricos
                    peso_limpo = float(pesos[i].replace(',', '.')) if i < len(pesos) and pesos[i] else 0
                    valor_limpo = float(valores[i].replace(',', '.')) if i < len(valores) and valores[i] else 0
                    
                    # Determinar status inicial baseado na categoria
                    status_inicial = 'RECEBIDO'
                    if categoria != 'ENTORPECENTE':
                        status_inicial = 'AGUARDANDO_OFICIO'
                    if categoria == 'DINHEIRO':
                        status_inicial = 'AGUARDANDO_GUIA'

                    Material.objects.create(
                        noticiado=noticiado,
                        categoria=categoria,
                        substancia=substancias[i] if i < len(substancias) and categoria == 'ENTORPECENTE' else None,
                        unidade=unidades[i] if i < len(unidades) and categoria == 'ENTORPECENTE' else None,
                        peso_estimado=peso_limpo if categoria == 'ENTORPECENTE' else None,
                        valor_monetario=valor_limpo if categoria == 'DINHEIRO' else None,
                        descricao_geral=descricoes[i] if i < len(descricoes) and categoria not in ['ENTORPECENTE', 'DINHEIRO'] else None,
                        numero_lacre=lacres[i].strip() if i < len(lacres) else None,
                        status=status_inicial
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
        
        # O peso real agora assume o peso estimado na conferência simples
        material.peso_real = material.peso_estimado
        material.status = 'ARMAZENADO'
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
    
    saldo_oficial = float(Material.objects.filter(
        q_estoque,
        status__in=['ARMAZENADO', 'AUTORIZADO']
    ).aggregate(total=Sum('peso_real'))['total'] or 0)

    saldo_pendente = float(Material.objects.filter(
        q_estoque,
        status='RECEBIDO'
    ).aggregate(total=Sum('peso_estimado'))['total'] or 0)

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
        'incinerado_label': formatar_peso_br(float(materiais_periodo.filter(status='INCINERADO').aggregate(total=Sum('peso_real'))['total'] or 0)),
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


# --- 3.5. RELATÓRIO GERENCIAL ---
@login_required
def relatorio_gerencial(request):
    filtros = {}
    params = request.GET
    
    for key in ['categoria', 'substancia', 'status', 'vara', 'natureza_penal', 
                 'data_inicio', 'data_fim', 'ano', 'semestre', 'unidade_origem']:
        val = params.get(key)
        if val:
            filtros[key] = val
    
    qs = Material.objects.all().select_related('noticiado__ocorrencia')
    qs = _aplicar_filtros_material(qs, filtros)
    
    resumo, por_categoria, por_substancia, por_status, por_natureza, por_unidade, por_mes = _resumir_material(qs)
    
    context = {
        'filtros': filtros,
        'resumo': resumo,
        'por_categoria': por_categoria,
        'por_substancia': por_substancia,
        'por_status': por_status,
        'por_natureza': por_natureza,
        'por_unidade': por_unidade,
        'por_mes': por_mes,
        'max_categoria': max([c['total'] for c in por_categoria], default=1),
        'max_status': max([s['total'] for s in por_status], default=1),
        'max_mes': max([m['total'] for m in por_mes], default=1),
        'DROGAS_CHOICES': DROGAS_CHOICES,
        'CATEGORIA_CHOICES': [
            ('ENTORPECENTE', 'Entorpecentes'), ('DINHEIRO', 'Dinheiro/Valores'),
            ('SOM', 'Aparelho de Som'), ('FACA', 'Arma Branca'),
            ('SIMULACRO', 'Simulacro'), ('OUTROS', 'Outros'),
        ],
        'VARA_CHOICES': VARA_CHOICES,
        'anos_disponiveis': range(datetime.now().year - 3, datetime.now().year + 1),
    }
    return render(request, 'gestao/relatorio_gerencial.html', context)

@login_required
def gerar_oficio_remessa_view(request):
    if request.method == "POST":
        ids = request.POST.getlist('itens_selecionados')
        if not ids:
            messages.warning(request, "Selecione ao menos um item para o Ofício.")
            return redirect('custodia_lista')
        
        materiais = Material.objects.filter(id__in=ids).select_related('noticiado__ocorrencia')
        if not materiais.exists():
            messages.error(request, "Materiais não encontrados.")
            return redirect('custodia_lista')
            
        try:
            path = documentos_services.gerar_oficio_materiais_gerais(materiais, request.user)
            # Retorna o arquivo gerado
            full_path = os.path.join(settings.MEDIA_ROOT, path)
            with open(full_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/pdf')
                response['Content-Disposition'] = f'inline; filename="{os.path.basename(path)}"'
                return response
        except Exception as e:
            messages.error(request, f"Erro ao gerar Ofício: {e}")
            return redirect('custodia_lista')
    return redirect('custodia_lista')


# --- 3.6. RELATÓRIO DE INCINERAÇÃO ---
@login_required
def relatorio_incineracao(request):
    filtros = {}
    params = request.GET
    
    for key in ['categoria', 'substancia', 'vara', 'natureza_penal', 
                 'data_inicio', 'data_fim', 'ano', 'semestre', 'unidade_origem']:
        val = params.get(key)
        if val:
            filtros[key] = val
    
    qs = Material.objects.filter(status='INCINERADO').select_related('noticiado__ocorrencia')
    
    if filtros.get('categoria'):
        qs = qs.filter(categoria=filtros['categoria'])
    if filtros.get('substancia'):
        qs = qs.filter(substancia=filtros['substancia'])
    if filtros.get('vara'):
        qs = qs.filter(noticiado__ocorrencia__vara=filtros['vara'])
    if filtros.get('natureza_penal'):
        qs = qs.filter(noticiado__ocorrencia__natureza_penal__icontains=filtros['natureza_penal'])
    if filtros.get('unidade_origem'):
        qs = qs.filter(noticiado__ocorrencia__unidade_origem=filtros['unidade_origem'])
    if filtros.get('ano'):
        qs = qs.filter(data_criacao__year=filtros['ano'])
    if filtros.get('semestre'):
        sem = int(filtros['semestre'])
        if sem == 1:
            qs = qs.filter(data_criacao__month__range=(1, 6))
        else:
            qs = qs.filter(data_criacao__month__range=(7, 12))
    if filtros.get('data_inicio'):
        qs = qs.filter(data_criacao__date__gte=filtros['data_inicio'])
    if filtros.get('data_fim'):
        qs = qs.filter(data_criacao__date__lte=filtros['data_fim'])
    
    resumo, _, por_substancia, _, por_natureza, _, _ = _resumir_material(qs)
    
    por_vara = list(
        qs.values('noticiado__ocorrencia__vara')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    vara_map = dict(VARA_CHOICES)
    for item in por_vara:
        item['label'] = vara_map.get(item['noticiado__ocorrencia__vara'], item['noticiado__ocorrencia__vara'] or 'Não definida')
    
    filtros_labels = {}
    label_map = {
        'categoria': dict(CATEGORIA_CHOICES),
        'substancia': dict(DROGAS_CHOICES),
        'vara': dict(VARA_CHOICES),
        'ano': lambda v: f'Ano {v}',
        'semestre': lambda v: f'{v}º Semestre',
        'data_inicio': lambda v: f'De {v}',
        'data_fim': lambda v: f'Até {v}',
    }
    for key, value in filtros.items():
        if key in label_map:
            mapper = label_map[key]
            filtros_labels[key] = mapper(value) if callable(mapper) else mapper.get(value, value)
        else:
            filtros_labels[key] = value
    
    context = {
        'filtros': filtros_labels,
        'resumo': resumo,
        'por_substancia': por_substancia,
        'por_vara': por_vara,
        'por_natureza': por_natureza,
        'VARA_CHOICES': VARA_CHOICES,
        'anos_disponiveis': range(datetime.now().year - 3, datetime.now().year + 1),
    }
    return render(request, 'gestao/relatorio_incinceracao.html', context)


# --- 4. LISTAGENS ---

@login_required
def custodia_lista(request):
    busca = request.GET.get('busca_bou', '').strip()
    # Mostra tudo que está fisicamente no cofre: 
    # Aguardando Projudi (ARMAZENADO), Autorizados (AUTORIZADO) e os que já estão em lotes (AGUARDANDO_INCINERACAO)
    itens = Material.objects.filter(
        status__in=['ARMAZENADO', 'AUTORIZADO', 'AGUARDANDO_INCINERACAO']
    ).select_related('noticiado__ocorrencia')
    
    if busca:
        itens = itens.filter(
            Q(noticiado__ocorrencia__bou__icontains=busca) | 
            Q(noticiado__nome__icontains=busca) |
            Q(numero_lacre__icontains=busca)
        )
    return render(request, 'gestao/custodia_lista.html', {'itens': itens.order_by('status', '-data_criacao')})

@login_required
def conferencia_lista(request):
    # Agora apenas entorpecentes passam pela "conferência/pesagem" no cofre central
    # Demais materiais (som, etc) podem ir direto ou ter fluxo simplificado
    pendentes = Material.objects.filter(status='RECEBIDO', categoria='ENTORPECENTE').select_related('noticiado__ocorrencia')
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
        'GRADUACAO_CHOICES': GRADUACAO_CHOICES,
        'ano_atual': timezone.now().year
    }
    return render(request, 'gestao/cadastro_entrada.html', context)

@login_required
def lotes_montagem(request):
    materiais_autorizados = Material.objects.filter(
        status='AUTORIZADO', 
        lote__isnull=True,
        categoria='ENTORPECENTE'
    ).select_related('noticiado__ocorrencia').order_by('noticiado__ocorrencia__data_registro_bou')

    processos_agrupados = {}
    for mat in materiais_autorizados:
        oc = mat.noticiado.ocorrencia
        proc_key = oc.processo or oc.bou
        if proc_key not in processos_agrupados:
            processos_agrupados[proc_key] = {
                'bou': oc.bou,
                'vara': oc.vara,
                'vara_display': oc.get_vara_display(),
                'data': oc.data_registro_bou,
                'materiais': [],
                'processo': oc.processo,
            }
        processos_agrupados[proc_key]['materiais'].append(mat)

    fila_conferidos = Material.objects.filter(
        status__in=['ARMAZENADO'], 
        lote__isnull=True,
        categoria='ENTORPECENTE',
        noticiado__ocorrencia__vara__isnull=False
    ).select_related('noticiado__ocorrencia')

    total_processos = len(processos_agrupados)
    total_itens = materiais_autorizados.count()
    
    lotes_abertos = LoteIncineracao.objects.filter(status='ABERTO')
    lotes_abertos_list = []
    for lote in lotes_abertos:
        mats = list(lote.materiais.filter(categoria='ENTORPECENTE').select_related('noticiado__ocorrencia'))
        lote.materiais_count = len(mats)
        lote.processos_set = set()
        for m in mats:
            if m.noticiado and m.noticiado.ocorrencia:
                proc = m.noticiado.ocorrencia.processo or m.noticiado.ocorrencia.bou
                lote.processos_set.add(proc)
        lote._processos_count = len(lote.processos_set)
        if mats:
            lotes_abertos_list.append(lote)
    
    lotes_incinerados = LoteIncineracao.objects.filter(status='INCINERADO').order_by('-data_incineracao')[:10]

    context = {
        'processos_agrupados': processos_agrupados,
        'materiais_autorizados': materiais_autorizados,
        'fila_conferidos': fila_conferidos,
        'total_processos': total_processos,
        'total_itens': total_itens,
        'lotes_abertos': lotes_abertos_list,
        'lotes_incinerados': lotes_incinerados,
    }
    return render(request, 'gestao/lotes_montagem.html', context)

@login_required
@transaction.atomic
def fechar_lote_manual(request):
    if request.method == "POST":
        processo_keys = request.POST.getlist('processos_selecionados')
        limite_por_lote = int(request.POST.get('limite_lote', 20))
        
        if not processo_keys:
            messages.warning(request, "Selecione ao menos um processo para criar o lote.")
            return redirect('lotes_montagem')
        
        if limite_por_lote < 15 or limite_por_lote > 20:
            messages.warning(request, "O limite deve ser entre 15 e 20 materiais por lote.")
            return redirect('lotes_montagem')
        
        try:
            ano_atual = timezone.now().year
            count_lotes = LoteIncineracao.objects.filter(data_criacao__year=ano_atual).count()
            
            lotes_criados = 0
            processos_adicionados = 0
            materiais_adicionados = 0
            
            # Buscar todos os materiais dos processos selecionados, ordenados por data
            materiais_selecionados = Material.objects.filter(
                status='AUTORIZADO',
                lote__isnull=True
            ).select_related('noticiado__ocorrencia').filter(
                Q(noticiado__ocorrencia__processo__in=processo_keys) |
                Q(noticiado__ocorrencia__bou__in=processo_keys)
            ).order_by('noticiado__ocorrencia__data_registro_bou', 'noticiado__ocorrencia__bou')
            
            # Agrupar materiais por processo (manter processos juntos)
            processos_dict = {}
            for mat in materiais_selecionados:
                oc = mat.noticiado.ocorrencia
                proc_key = oc.processo or oc.bou
                if proc_key not in processos_dict:
                    processos_dict[proc_key] = []
                processos_dict[proc_key].append(mat)
            
            # Lista de processos na ordem correta
            processos_ordenados = list(processos_dict.keys())
            
            # Criar lotes com distribuição inteligente
            lote_atual = None
            espacos_restantes = 0
            
            for proc_key in processos_ordenados:
                materiais_processo = processos_dict[proc_key]
                qtd_processo = len(materiais_processo)
                
                # Se o processo é maior que o limite, não cabe em nenhum lote
                # Coloca em lote próprio
                if qtd_processo > limite_por_lote:
                    # Se tinha lote atual com algo, finaliza ele
                    if lote_atual:
                        lotes_criados += 1
                    
                    # Cria lote especial para processo grande
                    count_lotes += 1
                    identificador = f"LOTE-{ano_atual}-{count_lotes:03d}"
                    lote_atual = LoteIncineracao.objects.create(
                        identificador=identificador,
                        status='ABERTO',
                        criado_por=request.user
                    )
                    
                    for mat in materiais_processo:
                        mat.lote = lote_atual
                        mat.status = 'AGUARDANDO_INCINERACAO'
                        mat.save(update_fields=['lote', 'status'])
                        RegistroHistorico.objects.create(
                            material=mat,
                            criado_por=request.user,
                            status_na_epoca='AGUARDANDO_INCINERACAO',
                            observacao=f"Material adicionado ao Lote {identificador}"
                        )
                        materiais_adicionados += 1
                    processos_adicionados += 1
                    lotes_criados += 1
                    lote_atual = None
                    espacos_restantes = 0
                
                # Se não cabe no lote atual, criar novo lote
                elif qtd_processo > espacos_restantes:
                    if lote_atual:
                        lotes_criados += 1
                    
                    count_lotes += 1
                    identificador = f"LOTE-{ano_atual}-{count_lotes:03d}"
                    lote_atual = LoteIncineracao.objects.create(
                        identificador=identificador,
                        status='ABERTO',
                        criado_por=request.user
                    )
                    espacos_restantes = limite_por_lote
                
                # Adicionar processo ao lote atual
                for mat in materiais_processo:
                    mat.lote = lote_atual
                    mat.status = 'AGUARDANDO_INCINERACAO'
                    mat.save(update_fields=['lote', 'status'])
                    RegistroHistorico.objects.create(
                        material=mat,
                        criado_por=request.user,
                        status_na_epoca='AGUARDANDO_INCINERACAO',
                        observacao=f"Material adicionado ao Lote {identificador}"
                    )
                    materiais_adicionados += 1
                    espacos_restantes -= 1
                processos_adicionados += 1
            
            # Contar último lote se existir
            if lote_atual:
                lotes_criados += 1
            
            messages.success(request, f"{lotes_criados} lote(s) criado(s) com {processos_adicionados} processo(s) e {materiais_adicionados} material(is)!")
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

    lotes_pendentes = LoteIncineracao.objects.exclude(status='INCINERADO').prefetch_related(
        'materiais__noticiado__ocorrencia'
    )

    mes_inicio = 1 if sem_sel_int == 1 else 7
    mes_fim = 6 if sem_sel_int == 1 else 12

    lotes_concluidos = LoteIncineracao.objects.filter(
        status='INCINERADO',
        data_incineracao__year=ano_sel_int,
        data_incineracao__month__gte=mes_inicio,
        data_incineracao__month__lte=mes_fim
    ).prefetch_related('materiais__noticiado__ocorrencia')

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


# --- 5B. CAIXAS DE INCINERAÇÃO ---

@login_required
def caixas_incineracao(request):
    """ Listagem de caixas de incineração """
    caixas_abertas = CaixaIncineracao.objects.filter(status='ABERTO').prefetch_related('lotes')
    caixas_concluidas = CaixaIncineracao.objects.filter(status='INCINERADO').order_by('-data_incineracao')[:20]
    
    lotes_sem_caixa = LoteIncineracao.objects.filter(status='ABERTO', caixa__isnull=True).order_by('-data_criacao')
    
    context = {
        'caixas_abertas': caixas_abertas,
        'caixas_concluidas': caixas_concluidas,
        'lotes_sem_caixa': lotes_sem_caixa,
    }
    return render(request, 'gestao/caixas_incineracao.html', context)


@login_required
@transaction.atomic
def criar_caixa(request):
    """ Cria uma nova caixa de incineração """
    if request.method == "POST":
        try:
            ano_atual = timezone.now().year
            count_caixas = CaixaIncineracao.objects.filter(data_criacao__year=ano_atual).count()
            count_caixas += 1
            identificador = f"CAIXA-{ano_atual}-{count_caixas:03d}"
            
            lote_ids = request.POST.getlist('lotes_selecionados')
            
            caixa = CaixaIncineracao.objects.create(
                identificador=identificador,
                status='ABERTO',
                criado_por=request.user
            )
            
            for lote_id in lote_ids:
                lote = LoteIncineracao.objects.get(id=lote_id)
                lote.caixa = caixa
                lote.save(update_fields=['caixa'])
            
            messages.success(request, f"Caixa {identificador} criada com {len(lote_ids)} lote(s)!")
        except Exception as e:
            messages.error(request, f"Erro ao criar caixa: {e}")
    
    return redirect('caixas_incineracao')


@login_required
@transaction.atomic
def adicionar_lote_caixa(request, caixa_id, lote_id):
    """ Adiciona um lote a uma caixa """
    if request.method == "POST":
        try:
            caixa = CaixaIncineracao.objects.get(id=caixa_id)
            lote = LoteIncineracao.objects.get(id=lote_id)
            
            lote.caixa = caixa
            lote.save(update_fields=['caixa'])
            
            messages.success(request, f"Lote {lote.identificador} adicionado à {caixa.identificador}!")
        except Exception as e:
            messages.error(request, f"Erro: {e}")
    
    return redirect('caixas_incineracao')


@login_required
@transaction.atomic
def remover_lote_caixa(request, lote_id):
    """ Remove um lote de uma caixa (volta para sem caixa) """
    if request.method == "POST":
        try:
            lote = LoteIncineracao.objects.get(id=lote_id)
            lote.caixa = None
            lote.save(update_fields=['caixa'])
            
            messages.success(request, f"Lote {lote.identificador} removido da caixa!")
        except Exception as e:
            messages.error(request, f"Erro: {e}")
    
    return redirect('caixas_incineracao')


@login_required
@transaction.atomic
def mover_lote_entre_caixas(request):
    """ Move um lote de uma caixa para outra """
    if request.method == "POST":
        try:
            lote_id = request.POST.get('lote_id')
            caixa_destino_id = request.POST.get('caixa_destino_id')
            
            lote = LoteIncineracao.objects.get(id=lote_id)
            
            if caixa_destino_id:
                caixa_destino = CaixaIncineracao.objects.get(id=caixa_destino_id)
                lote.caixa = caixa_destino
            else:
                lote.caixa = None
            
            lote.save(update_fields=['caixa'])
            
            destino_nome = caixa_destino.identificador if caixa_destino_id else "sem caixa"
            messages.success(request, f"Lote {lote.identificador} movido para {destino_nome}!")
        except Exception as e:
            messages.error(request, f"Erro: {e}")
    
    return redirect('caixas_incineracao')


@login_required
@transaction.atomic
def concluir_caixa(request, caixa_id):
    """ Marca a caixa como incinerada e todos os lotes dentro dela """
    if request.method == "POST":
        try:
            caixa = CaixaIncineracao.objects.get(id=caixa_id)
            
            if caixa.status == 'INCINERADO':
                messages.warning(request, "Esta caixa já foi incinerada!")
                return redirect('caixas_incineracao')
            
            lotes = caixa.lotes.all()
            count = 0
            
            for lote in lotes:
                if lote.status != 'INCINERADO':
                    lote.status = 'INCINERADO'
                    lote.data_incineracao = timezone.now()
                    lote.save(update_fields=['status', 'data_incineracao'])
                    
                    for mat in lote.materiais.all():
                        mat.status = 'INCINERADO'
                        mat.save(update_fields=['status'])
                        
                        RegistroHistorico.objects.create(
                            material=mat,
                            criado_por=request.user,
                            status_na_epoca='INCINERADO',
                            observacao=f"Material incinerado via caixa {caixa.identificador}"
                        )
                    count += 1
            
            caixa.status = 'INCINERADO'
            caixa.data_incineracao = timezone.now()
            caixa.save(update_fields=['status', 'data_incineracao'])
            
            messages.success(request, f"Caixa {caixa.identificador} incinerada com {count} lote(s)!")
        except Exception as e:
            messages.error(request, f"Erro ao concluir caixa: {e}")
    
    return redirect('caixas_incineracao')


@login_required
def imprimir_certidao_caixa(request, caixa_id):
    """ Gera certidão de incineração para todos os lotes da caixa """
    caixa = get_object_or_404(CaixaIncineracao, id=caixa_id)
    lotes = caixa.lotes.all().prefetch_related('materiais__noticiado__ocorrencia')
    
    return render(request, 'gestao/certidao_caixa.html', {
        'caixa': caixa,
        'lotes': lotes,
        'data_impressao': timezone.now(),
    })


@login_required
def imprimir_espelho_caixa(request, caixa_id):
    """ Gera espelho (lista detalhada) de todos os lotes da caixa para certidão de incineração """
    caixa = get_object_or_404(CaixaIncineracao, id=caixa_id)

    lotes_list = []
    all_materiais = []

    for lote in caixa.lotes.all():
        mats = lista = list(lote.materiais.select_related('noticiado__ocorrencia'))
        peso_lote = sum(float(m.peso_real or m.peso_estimado or 0) for m in mats)

        lotes_list.append({
            'lote': lote,
            'materiais_count': len(mats),
            'peso': peso_lote,
        })

        for mat in mats:
            all_materiais.append({
                'material': mat,
                'lote_identificador': lote.identificador,
                'noticiado_nome': mat.noticiado.nome if mat.noticiado else '',
                'processo': mat.noticiado.ocorrencia.processo if mat.noticiado and mat.noticiado.ocorrencia else '',
                'bou': mat.noticiado.ocorrencia.bou if mat.noticiado and mat.noticiado.ocorrencia else '',
            })

    all_materiais.sort(key=lambda x: (
        x['noticiado_nome'].upper(),
        x['processo'] or x['bou'],
        x['lote_identificador']
    ))

    por_vara = {}
    for item in all_materiais:
        mat = item['material']
        if mat.noticiado and mat.noticiado.ocorrencia:
            vn = mat.noticiado.ocorrencia.get_vara_display()
            por_vara.setdefault(vn, []).append(item)

    processos_unicos = set()
    for item in all_materiais:
        proc = item['processo'] or item['bou']
        if proc:
            processos_unicos.add(proc)

    total_peso = sum(float(item['material'].peso_real or item['material'].peso_estimado or 0) for item in all_materiais)

    return render(request, 'gestao/espelho_caixa.html', {
        'caixa': caixa,
        'lotes_list': lotes_list,
        'materiais': all_materiais,
        'por_vara': por_vara,
        'processos_unicos_count': len(processos_unicos),
        'total_peso': total_peso,
        'total_itens': len(all_materiais),
        'data_impressao': timezone.now(),
    })

    all_materiais.sort(key=lambda x: (
        x['noticiado_nome'].upper(),
        x['processo'] or x['bou'],
        x['lote_identificador']
    ))

    por_vara = {}
    for item in all_materiais:
        mat = item['material']
        if mat.noticiado and mat.noticiado.ocorrencia:
            vn = mat.noticiado.ocorrencia.get_vara_display()
            por_vara.setdefault(vn, []).append(item)

    processos_unicos = set()
    for item in all_materiais:
        proc = item['processo'] or item['bou']
        if proc:
            processos_unicos.add(proc)

    total_peso = sum(float(item['material'].peso_real or item['material'].peso_estimado or 0) for item in all_materiais)

    return render(request, 'gestao/espelho_caixa.html', {
        'caixa': caixa,
        'lotes': lotes,
        'materiais': all_materiais,
        'por_vara': por_vara,
        'processos_unicos_count': len(processos_unicos),
        'total_peso': total_peso,
        'total_itens': len(all_materiais),
        'data_impressao': timezone.now(),
    })


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
    """ Visão geral de tudo com rastro de quem manipulou e filtros avançados """
    params = request.GET
    filtros = Q()
    ano_atual = datetime.now().year

    # 1. Filtros de Período - Padrão: Ano Atual
    ano = params.get('ano') or str(ano_atual)
    semestre = params.get('semestre')
    data_inicio = params.get('data_inicio')
    data_fim = params.get('data_fim')

    if ano:
        filtros &= Q(noticiado__ocorrencia__data_registro_bou__year=ano)
    if semestre:
        s = int(semestre)
        if s == 1:
            filtros &= Q(noticiado__ocorrencia__data_registro_bou__month__range=(1, 6))
        else:
            filtros &= Q(noticiado__ocorrencia__data_registro_bou__month__range=(7, 12))
    if data_inicio:
        filtros &= Q(noticiado__ocorrencia__data_registro_bou__gte=data_inicio)
    if data_fim:
        filtros &= Q(noticiado__ocorrencia__data_registro_bou__lte=data_fim)

    # 2. Filtros de Status e Origem
    status = params.get('status')
    vara = params.get('vara')
    if status:
        filtros &= Q(status=status)
    if vara:
        filtros &= Q(noticiado__ocorrencia__vara=vara)

    # 3. Filtros de Material
    categoria = params.get('categoria')
    substancia = params.get('substancia')
    if categoria:
        filtros &= Q(categoria=categoria)
    if substancia:
        filtros &= Q(substancia=substancia)

    # Query Principal
    materiais_qs = Material.objects.filter(filtros).select_related(
        'noticiado__ocorrencia', 
        'noticiado__ocorrencia__criado_por',
        'lote'
    ).prefetch_related(
        Prefetch('historico', queryset=RegistroHistorico.objects.select_related('criado_por'))
    ).order_by('-noticiado__ocorrencia__data_registro_bou')

    # Cálculos Extras para Resumo
    resumo = {
        'total_itens': materiais_qs.count(),
        'total_noticiados': materiais_qs.values('noticiado').distinct().count(),
        'peso_total': materiais_qs.filter(categoria='ENTORPECENTE').aggregate(total=Sum('peso_real'))['total'] or 0
    }
    
    # Contagem de noticiados por substância no período filtrado
    noticiados_por_droga = list(
        materiais_qs.filter(categoria='ENTORPECENTE')
        .values('substancia')
        .annotate(qtd=Count('noticiado', distinct=True))
        .order_by('-qtd')
    )
    for nd in noticiados_por_droga:
        nd['label'] = dict(DROGAS_CHOICES).get(nd['substancia'], nd['substancia'])

    # Paginação - 50 resultados por página
    paginator = Paginator(materiais_qs, 50)
    pagina = int(request.GET.get('page', 1))
    todos_materiais = paginator.get_page(pagina)

    context = {
        'todos_materiais': todos_materiais,
        'resumo': resumo,
        'noticiados_por_droga': noticiados_por_droga,
        'DROGAS_CHOICES': DROGAS_CHOICES,
        'CATEGORIA_CHOICES': CATEGORIA_CHOICES,
        'VARA_CHOICES': VARA_CHOICES,
        'STATUS_CHOICES': STATUS_CUSTODIA_CHOICES,
        'anos_disponiveis': range(datetime.now().year - 4, datetime.now().year + 1),
    }
    
    return render(request, 'relatorios/inventario_geral.html', context)

# --- 7. RELATÓRIOS ESPECÍFICOS (VARA CRIMINAL) ---

@login_required
def relatorio_forum_view(request):
    vara_query = request.GET.get('vara')
    semestre_get = request.GET.get('semestre')
    ano_get = request.GET.get('ano')
    
    agora = datetime.now()
    ano = int(ano_get) if (ano_get and ano_get.isdigit()) else agora.year
    semestre = semestre_get if semestre_get else ('1' if agora.month <= 6 else '2')
    
    # Mapeamento de Varas
    mapeamento_vara = {'1': 'VARA_01', '2': 'VARA_02', '3': 'VARA_03'}
    vara_db = mapeamento_vara.get(vara_query, vara_query)
    
    # Query Base
    qs = Material.objects.select_related('noticiado__ocorrencia', 'lote')
    
    # Lógica de seleção: se viermos da tela de montagem (sem vara_query), 
    # buscamos os itens que estão nos lotes ABERTOS.
    if not vara_query:
        if LoteIncineracao.objects.filter(status='ABERTO').exists():
            qs = qs.filter(status='AGUARDANDO_INCINERACAO', lote__status='ABERTO')
        else:
            qs = qs.filter(status='INCINERADO', lote__data_incineracao__year=ano)
            if semestre == '1':
                qs = qs.filter(lote__data_incineracao__month__lte=6)
            else:
                qs = qs.filter(lote__data_incineracao__month__gt=6)
    else:
        # Busca por Vara específica (Geralmente Histórico)
        qs = qs.filter(status='INCINERADO', noticiado__ocorrencia__vara=vara_db, lote__data_incineracao__year=ano)
        if semestre == '1':
            qs = qs.filter(lote__data_incineracao__month__lte=6)
        else:
            qs = qs.filter(lote__data_incineracao__month__gt=6)
            
    itens = qs.order_by('noticiado__ocorrencia__vara', 'noticiado__nome')
    
    # Agrupamento para Resumo Consolidado
    resumo_pesos = list(itens.values('substancia').annotate(
        total_peso=Sum(Coalesce('peso_real', 'peso_estimado', output_field=DecimalField()))
    ).order_by('substancia'))
    
    # Formatação para o Template
    subst_dict = dict(DROGAS_CHOICES)
    for r in resumo_pesos:
        r['substancia'] = subst_dict.get(r['substancia'], r['substancia'])
        r['total_peso'] = float(r['total_peso'] or 0) / 1000  # Convertendo para KG
    
    context = {
        'itens': itens,
        'resumo_pesos': resumo_pesos,
        'vara_nome': dict(VARA_CHOICES).get(vara_db, "Geral / Todas as Varas"),
        'semestre': semestre,
        'ano': ano,
        'numero_oficio': f"{semestre}/{ano}-{vara_query or 'COLETIVO'}",
        'usuario_nome': request.user.get_full_name() or request.user.username,
        'usuario_id': request.user.username
    }

    return render(request, 'gestao/relatorio_forum.html', context)

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