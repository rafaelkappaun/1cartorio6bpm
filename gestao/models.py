from django.db import models
from django.contrib.auth.models import User

DROGAS_CHOICES = [
    ('MACONHA', 'Maconha'),
    ('COCAINA', 'Cocaína'),
    ('CRACK', 'Crack'),
    ('PE_MACONHA', 'Pé de Maconha'),
    ('SINTETICA', 'Droga Sintética'),
]

UNIDADES_CHOICES = [
    ('G', 'Gramas (g)'),
    ('U', 'Unidades (un)'),
]

VARA_CHOICES = [
    ('VARA_01', '1ª Vara Criminal'),
    ('VARA_02', '2ª Vara Criminal'),
    ('VARA_03', '3ª Vara Criminal'),
   
]

class Material(models.Model):
    # Identificação
    bou = models.CharField(max_length=50, unique=True, verbose_name="Nº Ocorrência")
    vara = models.CharField(max_length=100)
    substancia = models.CharField(max_length=50, choices=DROGAS_CHOICES)
    noticiado = models.CharField(max_length=255, blank=True, null=True)
    processo = models.CharField(max_length=50, blank=True, null=True, verbose_name="Número do Processo")
    numero_vestigio = models.CharField(max_length=50, blank=True, null=True, verbose_name="Nº do Vestígio (Lacre)")
    policial_entrega = models.CharField(max_length=100, blank=True, null=True, verbose_name="Policial que Entregou")
    observacao = models.TextField(blank=True, null=True, verbose_name="Descrição/Obs")
    vara = models.CharField(max_length=100, choices=VARA_CHOICES)
    
    # Quantidades
    peso_estimado = models.FloatField()
    peso_real = models.FloatField(blank=True, null=True)
    unidade = models.CharField(max_length=2, choices=UNIDADES_CHOICES, default='G')
    
    # Localização e Controle
    status = models.CharField(max_length=20, default='PENDENTE') # PENDENTE, NO_COFRE, PRONTO_QUEIMA, INCINERADO
    caixa = models.CharField(max_length=10, blank=True, null=True) # Ex: 01, 02
    lote = models.CharField(max_length=50, blank=True, null=True)  # Ex: 2026/01

    usuario_registro = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='registros'
    )
    usuario_conferencia = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='conferencias'
    )
    
    # Campo para salvar a data exata da conferência
    data_conferencia = models.DateTimeField(null=True, blank=True)
    # Documentação
    n_oficio = models.CharField(max_length=50, blank=True, null=True)
    data_entrada = models.DateTimeField(auto_now_add=True)
    data_incineracao = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        # Força campos de texto para MAIÚSCULAS
        if self.noticiado: self.noticiado = self.noticiado.upper()
        if self.policial_entrega: self.policial_entrega = self.policial_entrega.upper()
        if self.numero_vestigio: self.numero_vestigio = self.numero_vestigio.upper()
        if self.bou: self.bou = self.bou.upper()
        super(Material, self).save(*args, **kwargs)

    def __str__(self):
       
        # Exibe a unidade no nome para facilitar (ex: 2026/001 - 10 un)
        return f"{self.bou} - {self.noticiado} ({self.peso_real or self.peso_estimado} {self.get_unidade_display()}) {self.substancia}"