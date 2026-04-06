from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Count
from .models import Material, RegistroHistorico, LoteIncineracao

@receiver(post_save, sender=Material)
def registrar_mudanca_custodia(sender, instance, created, **kwargs):
    """
    Gera rastro de auditoria automático para entradas e mudanças de lote.
    """
    if created:
        RegistroHistorico.objects.create(
            material=instance,
            criado_por=instance.noticiado.ocorrencia.criado_por if instance.noticiado and instance.noticiado.ocorrencia else None,
            status_na_epoca=instance.status,
            observacao=f"Entrada de material via BOU {instance.noticiado.ocorrencia.bou if instance.noticiado else 'N/A'}."
        )
        # Verifica se deve criar lote automático
        verificar_criacao_lote_automatico(instance)
    # Update - o registro já é feito manualmente nas Views para capturar o request.user


def verificar_criacao_lote_automatico(material):
    """
    Verifica se há 20 ou mais processos autorizados para criar um lote automaticamente.
    """
    if material.categoria != 'ENTORPECENTE' or material.status != 'AUTORIZADO':
        return
    
    # Conta processos únicos com materiais autorizados que ainda não estão em lotes
    materiais_sem_lote = Material.objects.filter(
        status='AUTORIZADO',
        categoria='ENTORPECENTE',
        lote__isnull=True
    ).select_related('noticiado__ocorrencia')
    
    # Agrupa por processo/BOU
    processos = {}
    for mat in materiais_sem_lote:
        proc = mat.noticiado.ocorrencia.processo or f"BOU-{mat.noticiado.ocorrencia.bou}"
        if proc not in processos:
            processos[proc] = []
        processos[proc].append(mat)
    
    total_processos = len(processos)
    
    # Se atingir 20 processos, cria um lote automático
    if total_processos >= 20:
        criar_lote_automatico()


def criar_lote_automatico():
    """
    Cria um lote automático com materiais autorizados que ainda não estão em lotes.
    """
    from datetime import datetime
    
    materiais_sem_lote = Material.objects.filter(
        status='AUTORIZADO',
        categoria='ENTORPECENTE',
        lote__isnull=True
    ).select_related('noticiado__ocorrencia')
    
    if not materiais_sem_lote.exists():
        return
    
    # Agrupa por processo
    processos = {}
    for mat in materiais_sem_lote:
        proc = mat.noticiado.ocorrencia.processo or f"BOU-{mat.noticiado.ocorrencia.bou}"
        if proc not in processos:
            processos[proc] = []
        processos[proc].append(mat)
    
    # Pega até 20 processos
    processos_list = list(processos.keys())[:20]
    
    # Cria o lote
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    identificador = f"AUTO-{timestamp}"
    
    lote = LoteIncineracao.objects.create(
        identificador=identificador,
        status='ABERTO'
    )
    
    # Associa materiais ao lote
    for proc in processos_list:
        for mat in processos[proc]:
            mat.lote = lote
            mat.status = 'AGUARDANDO_INCINERACAO'
            mat.save(update_fields=['lote', 'status'])
            
            RegistroHistorico.objects.create(
                material=mat,
                criado_por=mat.criado_por,
                status_na_epoca='AGUARDANDO_INCINERACAO',
                observacao=f"LOTE AUTOMÁTICO gerado com {len(processos_list)} processos. Lote: {lote.identificador}"
            )
    
    print(f"[LOTE AUTO] Lote {lote.identificador} criado com {sum(len(processos[p]) for p in processos_list)} materiais de {len(processos_list)} processos.")
