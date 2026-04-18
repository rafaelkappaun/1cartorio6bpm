from django.db import models
from django.contrib.auth.models import User
from .constants import (
    DROGAS_CHOICES, UNIDADES_MEDIDA_CHOICES, VARA_CHOICES,
    GRADUACAO_CHOICES, UNIDADES_PM_CHOICES, CATEGORIA_CHOICES,
    STATUS_CUSTODIA_CHOICES
)

# --- MODELOS ---

class AuditoriaModel(models.Model):
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='%(class)s_criado')
    data_criacao = models.DateTimeField(auto_now_add=True, db_index=True)
    ultima_alteracao = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class LoteIncineracao(AuditoriaModel):
    identificador = models.CharField(max_length=50, unique=True, verbose_name="Código do Lote")
    data_incineracao = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default='ABERTO', choices=[('ABERTO', 'Aberto'), ('INCINERADO', 'Incinerado')])
    eprotocolo_geral = models.CharField(max_length=50, blank=True, null=True, verbose_name="eProtocolo do Comando")
    caixa = models.ForeignKey('CaixaIncineracao', on_delete=models.SET_NULL, null=True, blank=True, related_name='lotes')

    class Meta:
        verbose_name = "Lote de Incineração"
        verbose_name_plural = "Lotes de Incineração"

    def __str__(self):
        return f"Lote {self.identificador} - {self.status}"

    @property
    def processos_count(self):
        return self.materiais.values('noticiado__ocorrencia__bou').distinct().count()

    @property
    def processos_list(self):
        return list(self.materiais.values_list('noticiado__ocorrencia__bou', flat=True).distinct())

    @property
    def peso_total(self):
        from django.db.models import Sum
        result = self.materiais.aggregate(
            total_real=Sum('peso_real'),
            total_estimado=Sum('peso_estimado')
        )
        return float((result['total_real'] or 0) + (result['total_estimado'] or 0))


class CaixaIncineracao(AuditoriaModel):
    identificador = models.CharField(max_length=50, unique=True, verbose_name="Código da Caixa")
    data_incineracao = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default='ABERTO', choices=[('ABERTO', 'Aberta'), ('INCINERADO', 'Incinerada')])
    eprotocolo_geral = models.CharField(max_length=50, blank=True, null=True, verbose_name="eProtocolo do Comando")
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")

    class Meta:
        verbose_name = "Caixa de Incineração"
        verbose_name_plural = "Caixas de Incineração"
        ordering = ['-data_criacao']

    def __str__(self):
        return f"Caixa {self.identificador} - {self.status}"

    @property
    def lotes_count(self):
        return self.lotes.count()

    @property
    def processos_count(self):
        from django.db.models import Count
        result = self.lotes.aggregate(
            total=Count('materiais__noticiado__ocorrencia__bou', distinct=True)
        )
        return result['total'] or 0

    @property
    def peso_total(self):
        from django.db.models import Sum
        from django.db.models.functions import Coalesce
        from django.db.models.fields import DecimalField
        result = self.lotes.aggregate(
            total=Sum(
                Coalesce(
                    'materiais__peso_real', 'materiais__peso_estimado',
                    output_field=DecimalField()
                )
            )
        )
        return float(result['total'] or 0)

    @property
    def materiais_count(self):
        from django.db.models import Count
        result = self.lotes.aggregate(total=Count('materiais'))
        return result['total'] or 0


class Ocorrencia(AuditoriaModel):
    bou = models.CharField(max_length=20, unique=True, verbose_name="BOU")
    vara = models.CharField(max_length=20, choices=VARA_CHOICES, db_index=True)
    processo = models.CharField(max_length=30, null=True, blank=True, verbose_name="PROJUDI")
    
    policial_nome = models.CharField(max_length=100, blank=True, null=True)
    policial_graduacao = models.CharField(max_length=10, choices=GRADUACAO_CHOICES, blank=True, null=True)
    rg_policial = models.CharField(max_length=20, blank=True, null=True)
    
    unidade_origem = models.CharField(max_length=20, choices=UNIDADES_PM_CHOICES, default='RPA')
    unidade_especifica = models.CharField(max_length=100, blank=True, null=True)
    
    natureza_penal = models.CharField(max_length=255, blank=True, null=True, verbose_name="Tipos Penais / Natureza", db_index=True)
    data_registro_bou = models.DateField(null=True, blank=True, verbose_name="Data do Fato (BOU)", db_index=True)
    observacao = models.TextField(blank=True, null=True, verbose_name="Observações de Conferência / Erros BOU")

    def save(self, *args, **kwargs):
        if self.policial_nome: 
            self.policial_nome = self.policial_nome.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"BOU {self.bou}"


class Noticiado(AuditoriaModel):
    ocorrencia = models.ForeignKey(Ocorrencia, on_delete=models.CASCADE, related_name='noticiados')
    nome = models.CharField(max_length=200)
    depositario_fiel = models.BooleanField(default=False, verbose_name="Depositário Fiel", blank=True)
    observacao = models.TextField(blank=True, null=True, verbose_name="Observação")

    def save(self, *args, **kwargs):
        self.nome = self.nome.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nome} (BOU: {self.ocorrencia.bou})"


class Material(AuditoriaModel):
    id = models.BigAutoField(primary_key=True)
    noticiado = models.ForeignKey(Noticiado, on_delete=models.CASCADE, related_name='materiais')
    categoria = models.CharField(max_length=50, choices=CATEGORIA_CHOICES, default='ENTORPECENTE', db_index=True)
    
    # Específico para Entorpecentes
    substancia = models.CharField(max_length=50, choices=DROGAS_CHOICES, blank=True, null=True, db_index=True)
    outra_substancia = models.CharField(max_length=100, blank=True, null=True)
    nome_popular = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nome Popular / Característica")
    uso_pessoal = models.BooleanField(default=False, verbose_name="Uso Pessoal?")
    peso_estimado = models.DecimalField(max_digits=12, decimal_places=3, blank=True, null=True, verbose_name="Peso Estimado")
    peso_real = models.DecimalField(max_digits=12, decimal_places=3, blank=True, null=True, verbose_name="Peso Real")
    unidade = models.CharField(max_length=3, choices=UNIDADES_MEDIDA_CHOICES, blank=True, null=True)
    lote = models.ForeignKey(LoteIncineracao, on_delete=models.SET_NULL, null=True, blank=True, related_name='materiais')
    
    # Específico para Materiais Gerais (Som, Facas, Simulacros, Outros) e Dinheiro
    descricao_geral = models.TextField(blank=True, null=True, help_text="Ex: Marca do som, modelo do simulacro, etc.")
    valor_monetario = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Valor em Dinheiro (R$)")
    
    # Comprovantes (Uploads)
    recibo_forum = models.FileField(upload_to='recibos/forum/', blank=True, null=True, verbose_name="Recibo Assinado do Fórum")
    comprovante_deposito = models.FileField(upload_to='recibos/deposito/', blank=True, null=True, verbose_name="Comprovante de Depósito PIX/TED")
    
    # Auditoria de Movimentação (Fisico)
    numero_lacre = models.CharField(max_length=50, blank=True, null=True, verbose_name="Nº Lacre (Cadeia de Custódia)", db_index=True)
    localizacao_no_cofre = models.CharField(max_length=100, blank=True, null=True, help_text="Ex: Armário 1, Prateleira B")
    status = models.CharField(max_length=50, choices=STATUS_CUSTODIA_CHOICES, default='RECEBIDO', db_index=True)
    eprotocolo_geral = models.CharField(max_length=50, blank=True, null=True, verbose_name="Nº Ofício/EProtocolo")
    observacao_material = models.TextField(blank=True, null=True, verbose_name="Observação do Item")
    
    class Meta:
        verbose_name = "Material"
        verbose_name_plural = "Materiais"

    @property
    def vara(self):
        return self.noticiado.ocorrencia.vara

    @property
    def bou(self):
        return self.noticiado.ocorrencia.bou

    @property
    def processo(self):
        return self.noticiado.ocorrencia.processo

    def save(self, *args, **kwargs):
        if self.substancia == 'COLHEITA':
            self.unidade = 'UN'
        super().save(*args, **kwargs)

    def peso_formatado(self):
        if self.categoria != 'ENTORPECENTE':
            return "-"
        valor = self.peso_real if self.peso_real is not None else self.peso_estimado
        if not valor: return "0,000"
        if self.unidade == 'UN': return f"{int(valor)} un"
        def fmt(v): return f"{v:,.3f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        if self.unidade == 'KG': return f"{fmt(valor)} kg"
        if valor >= 1000: return f"{fmt(valor / 1000)} kg"
        return f"{fmt(valor)} g"

    def descricao_amigavel(self):
        if self.categoria == 'ENTORPECENTE':
            return f"{self.get_substancia_display()} | {self.peso_formatado()}"
        elif self.categoria == 'DINHEIRO':
            return f"Dinheiro R$ {self.valor_monetario}"
        else:
            return f"{self.get_categoria_display()} - {self.descricao_geral[:30]}"

    def __str__(self):
        return f"{self.descricao_amigavel()} | Lacre: {self.numero_lacre}"


class RegistroHistorico(AuditoriaModel):
    """ Este é o coração da auditoria. Imutável. """
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='historico')
    status_na_epoca = models.CharField(max_length=50, choices=STATUS_CUSTODIA_CHOICES)
    observacao = models.TextField(blank=True, null=True, help_text="Descreva: 'Droga guardada no cofre', 'Retirada para pesagem real', etc.")

    class Meta:
        verbose_name = "Registro de Movimentação"
        ordering = ['-data_criacao']

    def __str__(self):
        return f"{self.material.numero_lacre} - {self.status_na_epoca}"


class NaturezaPenal(models.Model):
    nome = models.CharField(max_length=255, unique=True)
    tipo = models.CharField(max_length=20, choices=[('TC', 'Termo Circunstanciado'), ('IP', 'Inquérito Policial')])
    
    class Meta:
        verbose_name = "Natureza Penal"
        verbose_name_plural = "Naturezas Penais"
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.get_tipo_display()})"


class EquipePM(models.Model):
    nome = models.CharField(max_length=100)
    graduacao = models.CharField(max_length=10, choices=GRADUACAO_CHOICES)
    rg = models.CharField(max_length=20)
    unidade = models.CharField(max_length=20, choices=UNIDADES_PM_CHOICES, default='RPA')

    class Meta:
        verbose_name = "Equipe PM"
        verbose_name_plural = "Equipes PM"
        ordering = ['nome']

    def __str__(self):
        return f"{self.get_graduacao_display()} {self.nome}"

    def save(self, *args, **kwargs):
        self.nome = self.nome.upper()
        self.rg = self.rg.upper()
        super().save(*args, **kwargs)