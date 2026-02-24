from django.contrib import messages
from django.utils import timezone 
from django.shortcuts import get_object_or_404, render, redirect
from django.db.models import Sum, FloatField
from django.db.models.functions import Cast, Coalesce
from .models import Material, Ocorrencia, Noticiado, RegistroHistorico, LoteIncineracao, DROGAS_CHOICES 
from django.contrib.auth.decorators import login_required
from django.forms import inlineformset_factory
from django.db import transaction
import json


# --- PAINEL PRINCIPAL ---


# Esta linha cria a "fábrica" de formulários vinculados
# Ela diz: "Quero um formulário para Material, que pertence a um Noticiado"
MaterialFormSet = inlineformset_factory(
    Noticiado, 
    Material, 
    fields=('substancia', 'peso_estimado', 'unidade', 'status'), 
    extra=1,  # Quantos campos vazios extras mostrar
    can_delete=True
)

@login_required
def painel_principal(request):
    busca = request.GET.get('busca_bou', '').strip()
    
    # 1. Filtra ocorrências
    ocorrencias = Ocorrencia.objects.all().order_by('-data_entrada')
    if busca:
        ocorrencias = ocorrencias.filter(bou__icontains=busca)

    # 2. Filtra materiais vinculados (otimizado com select_related)
    materiais = Material.objects.filter(noticiado__ocorrencia__in=ocorrencias) \
                                       .select_related('noticiado__ocorrencia')

    # 3. Lógica do Gráfico: Soma os pesos por substância (status ativos)
    # Aqui incluímos tudo que ainda não foi incinerado
    dados_grafico = materiais.filter(status__in=['PENDENTE', 'NO_COFRE', 'PRONTO_QUEIMA']) \
                         .values('substancia') \
                         .annotate(total=Sum(Coalesce('peso_estimado', 0.0)))

    # Mapeamento para nomes legíveis (se desejar usar o nome do CHOICES no gráfico)
    drogas_map = dict(DROGAS_CHOICES)
# Certifique-se de que são listas:      
    lista_labels = [drogas_map.get(d['substancia'], d['substancia']) for d in dados_grafico]
    lista_valores = [float(d['total']) for d in dados_grafico]

    # 4. Contexto do Template
    contexto = {
        'labels_json': json.dumps(lista_labels),
        'valores_json': json.dumps(lista_valores),
        'busca_termo': busca,
        'pendentes': materiais.filter(status='PENDENTE').order_by('-noticiado__ocorrencia__data_entrada'),
        'no_cofre': materiais.filter(status='NO_COFRE').order_by('caixa', 'noticiado__ocorrencia__bou'),
        'todos_lotes': LoteIncineracao.objects.filter(status='ABERTO'), # Só lotes abertos!,
        'prontos': materiais.filter(status='PRONTO_QUEIMA').order_by('lote', 'noticiado__ocorrencia__bou'),
        'incinerados': materiais.filter(status='INCINERADO').order_by('noticiado__ocorrencia__vara', '-data_incineracao'),
        'drogas_lista': DROGAS_CHOICES,
    }
    
    return render(request, 'gestao/painel.html', contexto)

# --- REGISTRO E CONFERÊNCIA ---
@login_required
def registrar_entrada(request):
    if request.method == 'POST':
        bou_numero = request.POST.get('bou')
        
        # 1. Verificação de existência
        if Ocorrencia.objects.filter(bou=bou_numero).exists():
            messages.error(request, f"O BOU {bou_numero} já está cadastrado no sistema!")
            return redirect('painel')

        try:
            # 2. Início da transação atômica (ou salva tudo, ou nada)
            with transaction.atomic():
                ocorrencia = Ocorrencia.objects.create(
                    bou=request.POST.get('bou'),
                    processo=request.POST.get('processo', ''),
                    vara=request.POST.get('vara'),
                    policial_nome=request.POST.get('policial_nome', '').upper(),
                    policial_graduacao=request.POST.get('policial_graduacao'),
                    rg_policial = request.POST.get('rg_policial')
                    
                )

                nomes = request.POST.getlist('noticiado_nome')
                substancias = request.POST.getlist('substancia')
                pesos = request.POST.getlist('peso_estimado')
                unidades = request.POST.getlist('unidade')
                lacres = request.POST.getlist('num_lacre')

                for i, nome_noticiado in enumerate(nomes):
                    if not nome_noticiado.strip():
                        continue

                    noticiado_obj = Noticiado.objects.create(
                        ocorrencia=ocorrencia,
                        nome=nome_noticiado.upper().strip()
                    )

                    peso_raw = pesos[i] if i < len(pesos) else "0"
                    peso_formatado = float(peso_raw.replace(',', '.')) if peso_raw else 0.0
                    lacre_val = lacres[i].upper().strip() if i < len(lacres) else "N/I"
                    subst_val = substancias[i] if i < len(substancias) else 'OUTROS'
                    unid_val = unidades[i] if i < len(unidades) else 'G'

                    # Criação do material
                    material = Material.objects.create(
                        noticiado=noticiado_obj,
                        substancia=subst_val,
                        peso_estimado=peso_formatado,
                        unidade=unid_val,
                        numero_vestigio=lacre_val,
                        usuario_registro=request.user,
                        status='PENDENTE'
                    )

                    # 3. Auditoria: Registro do evento inicial
                    RegistroHistorico.objects.create(
                
                        material=material,
                        usuario=request.user,
                        status_novo='PENDENTE',
                        observacao='Registro inicial de apreensão.'
                    )

            messages.success(request, f"{ocorrencia.id}", extra_tags='abrir_recibo')
            
        except Exception as e:
            # Em caso de erro, a transação faz o rollback automático
            messages.error(request, f"Erro crítico ao registrar: {str(e)}")
            return redirect('painel')

    return redirect('painel')
    

@login_required
def confirmar_conferencia(request, id):
    if request.method == "POST":
        item = get_object_or_404(Material, id=id)
        
        # Iniciar transação para garantir integridade entre Material e Histórico
        with transaction.atomic():
            # 1. Captura de dados do formulário
            peso_real_str = request.POST.get('peso_real', '0').replace(',', '.')
            peso_real = float(peso_real_str)
            
            # Pega o ID do Lote (Caixa Mãe) e a Posição (Sacola/Sublote) do formulário
            lote_id = request.POST.get('lote_id')
            posicao_sacola = request.POST.get('posicao_sacola', '').upper()
            
            # Atualização do item
            item.peso_real = peso_real
            item.lote_id = lote_id  # Atribui o ID da ForeignKey
            item.posicao_sacola = posicao_sacola # Novo campo de organização interna
            
            # Registro do status anterior para o histórico
            status_anterior = item.status
            item.status = 'NO_COFRE'
            
            item.usuario_conferencia = request.user
            item.data_conferencia = timezone.now()
            item.save()

            # 2. Registro no Histórico de Auditoria
            # Buscamos o lote pelo ID para exibir o identificador no histórico
            lote_obj = LoteIncineracao.objects.get(id=lote_id)
            
            RegistroHistorico.objects.create(
                material=item,
                usuario=request.user,
                status_anterior=status_anterior,
                status_novo='NO_COFRE',
                observacao=(f"Conferência realizada. Peso: {peso_real} {item.get_unidade_display()}. "
                            f"Caixa: {lote_obj.identificador} | Posição: {posicao_sacola}")
            )
            
        messages.success(request, f"Conferência do vestígio {item.noticiado.ocorrencia.bou} registrada com sucesso.")
        
    return redirect('painel')

@login_required
def vincular_oficio(request, id):
    if request.method == "POST":
        item = get_object_or_404(Material, id=id)
        item.n_oficio = request.POST.get('n_oficio')
        item.status = 'PRONTO_QUEIMA'
        item.save()
    return redirect('painel')

# --- FINALIZAÇÃO E RELATÓRIOS ---
@login_required
def finalizar_lote(request):
    if request.method == "POST":
        # Recebemos o ID numérico enviado pelo formulário (ajustado no HTML)
        lote_id = request.POST.get('lote_id')
        
        if lote_id:
            # Chama a função que já contém a lógica de salvar Histórico e status
            fechar_e_incinerar_lote(lote_id, request.user)
            messages.success(request, f"Lote incinerado e registrado no histórico com sucesso!")
        else:
            messages.error(request, "Erro: Lote não identificado.")
            
    return redirect('painel')

@login_required
def relatorio_final(request):
    filtros = {
        'vara': request.GET.get('vara'),
        'substancia': request.GET.get('substancia'),
        'mes': request.GET.get('mes')
    }
    
    # 1. Base geral filtrada
    base = Material.objects.select_related('noticiado__ocorrencia', 'lote').all()
    
    if filtros['vara']: base = base.filter(noticiado__ocorrencia__vara=filtros['vara'])
    if filtros['substancia']: base = base.filter(substancia=filtros['substancia'])
    if filtros['mes']: base = base.filter(data_conferencia__month=filtros['mes'])

    # 2. Segmentação (O inventário dividido por etapas)
    contexto = {
        'pendentes': base.filter(status='PENDENTE'),
        'no_cofre': base.filter(status='NO_COFRE'),
        'prontos': base.filter(status='PRONTO_QUEIMA'),
        'incinerados': base.filter(status='INCINERADO'),
        'filtros': filtros,
        'data_hoje': timezone.now(),
        'drogas_lista': DROGAS_CHOICES
    }
    return render(request, 'gestao/relatorio.html', contexto)

@login_required
def relatorio_queima(request):
    # Filtramos apenas materiais que estão PRONTOS e cujo lote ainda esteja ABERTO (ou seja, não fechado/incinerado)
    itens = Material.objects.filter(
        status='PRONTO_QUEIMA',
        lote__status='ABERTO'  # Adicionamos este filtro de relacionamento
    ) \
    .select_related('noticiado__ocorrencia', 'lote') \
    .order_by('lote__identificador', 'noticiado__ocorrencia__bou')
        
    return render(request, 'gestao/relatorio_queima.html', {
        'itens': itens,
        'data_atual': timezone.now()
    })

@login_required
def relatorio_forum(request):
    vara_slug = request.GET.get('vara')
    # Otimize com select_related para acessar a ocorrência sem novas consultas
    itens = Material.objects.filter(status='INCINERADO').select_related('noticiado__ocorrencia')
    
    if vara_slug: 
        itens = itens.filter(noticiado__ocorrencia__vara=vara_slug)
    
    # Ordenar pelos dados da ocorrência para que o regroup funcione
    itens = itens.order_by('noticiado__ocorrencia__vara', '-data_incineracao')
    
    return render(request, 'gestao/relatorio_forum.html', {'itens': itens})

@login_required
def gerar_recibo(request, id):
    ocorrencia = Ocorrencia.objects.get(id=id)
    return render(request, 'relatorios/recibo_entrega.html', {'obj': ocorrencia})



def detalhes_material(request, id):
    item = get_object_or_404(Material, id=id)
    historico = item.historico.all().order_by('-data_evento')
    return render(request, 'gestao/detalhes.html', {'item': item, 'historico': historico})

@transaction.atomic
def fechar_e_incinerar_lote(lote_id, usuario):
    # Usar get_object_or_404 ou lidar com DoesNotExist é mais seguro
    from .models import LoteIncineracao
    lote = LoteIncineracao.objects.get(id=lote_id)
    materiais = lote.materiais.all()
    
    for item in materiais:
        status_antigo = item.status
        item.status = 'INCINERADO'
        item.data_incineracao = timezone.now() # Registrando a data no item
        item.save()
        
        RegistroHistorico.objects.create(
            material=item,
            usuario=usuario,
            status_anterior=status_antigo,
            status_novo='INCINERADO',
            observacao=f"Incineração oficial do Lote {lote.identificador}"
        )
    
    lote.status = 'INCINERADO'
    lote.data_incineracao = timezone.now()
    lote.save()

@login_required
def relatorio_incineracao_vara(request, vara_id):
    itens = Material.objects.filter(
        status='INCINERADO', 
        noticiado__ocorrencia__vara=vara_id
    ).select_related('noticiado__ocorrencia')
    
    return render(request, 'relatorios/incineracao_vara.html', {'itens': itens})

