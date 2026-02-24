from django.db import models
from django.contrib.auth.models import User


DROGAS_CHOICES = [
    ('MACONHA', 'Maconha'),
    ('COCAINA', 'Cocaína'),
    ('CRACK', 'Crack'),
    ('PE_MACONHA', 'Pé de Maconha'),
    ('SINTETICA', 'Droga Sintética'),
    ('ECSTASY', 'Ecstasy'),
    ('SKUNK', 'Skunk'),
    ('HAXIXE', 'Haxixe'),
    ('OUTROS', 'Outros'),
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

GRADUACAO_CHOICES = [
    ('SD', 'Soldado'), ('CB', 'Cabo'), ('3SGT', '3º Sargento'),
    ('2SGT', '2º Sargento'), ('1SGT', '1º Sargento'),
    ('SUB', 'Subtenente'), ('TEN', 'Tenente'), ('CAP', 'Capitão'),
]

# 1. Classes de Apoio primeiro
class LoteIncineracao(models.Model):
    identificador = models.CharField(max_length=50, unique=True, verbose_name="Código do Lote")
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_incineracao = models.DateTimeField(null=True, blank=True)
    responsavel = models.ForeignKey(User, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, default='ABERTO')

    def save(self, *args, **kwargs):
        # Se o lote já foi incinerado, não permitir salvar alterações
        if self.pk:
            obj_antigo = LoteIncineracao.objects.get(pk=self.pk)
            if obj_antigo.status == 'INCINERADO':
                raise ValueError("Este lote já foi incinerado e não pode ser modificado.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Lote {self.identificador}"

class Ocorrencia(models.Model):
    bou = models.CharField(max_length=50, unique=True)
    vara = models.CharField(max_length=20, choices=VARA_CHOICES)
    processo = models.CharField(max_length=50)
    policial_nome = models.CharField(max_length=100, blank=True, null=True)
    policial_graduacao = models.CharField(max_length=10, choices=GRADUACAO_CHOICES, blank=True, null=True)
    rg_policial = models.CharField(max_length=20, blank=True, null=True, verbose_name="RG do Policial")
    data_entrada = models.DateTimeField(auto_now_add=True)

    

def get_nome_vara_formal(self):
        mapping = {
            'VARA_01': '1ª Vara Criminal de Cascavel',
            'VARA_02': '2ª Vara Criminal de Cascavel',
            'VARA_03': '3º Juizado Especial Criminal de Cascavel',
        }
        return mapping.get(self.vara, self.vara) # Retorna o nome ou o próprio código se não achar

def save(self, *args, **kwargs):
        if self.policial_nome: 
            self.policial_nome = self.policial_nome.upper()
        super().save(*args, **kwargs)
        

class Noticiado(models.Model):
    ocorrencia = models.ForeignKey(Ocorrencia, on_delete=models.CASCADE, related_name='noticiados')
    nome = models.CharField(max_length=200)

# 2. Material agora referencia LoteIncineracao corretamente
class Material(models.Model):
    id = models.BigAutoField(primary_key=True)
    noticiado = models.ForeignKey(Noticiado, on_delete=models.CASCADE, related_name='materiais', null=True)
    substancia = models.CharField(max_length=50, choices=DROGAS_CHOICES)
    outra_substancia = models.CharField(max_length=100, blank=True, null=True)
    peso_estimado = models.FloatField()
    peso_real = models.FloatField(blank=True, null=True)
    unidade = models.CharField(max_length=2, choices=UNIDADES_CHOICES, default='G')
    numero_vestigio = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=20, default='PENDENTE')
    caixa = models.CharField(max_length=10, blank=True, null=True)
    lote = models.ForeignKey(LoteIncineracao, on_delete=models.SET_NULL, null=True, blank=True, related_name='materiais')    
    posicao_sacola = models.CharField(max_length=20, blank=True, null=True, verbose_name="Identificação da Sacola/Sublote")
    n_oficio = models.CharField(max_length=50, blank=True, null=True)
    usuario_registro = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='registros')
    data_incineracao = models.DateTimeField(blank=True, null=True)
    
    def pode_ser_editado(self):
        return self.status != 'INCINERADO'

    def __str__(self):
        return f"{self.get_substancia_display()} | BOU: {self.noticiado.ocorrencia.bou}"
    
    def save(self, *args, **kwargs):
        # Bloqueia salvamento se estiver vinculado a um lote incinerado
        if self.lote and self.lote.status == 'INCINERADO':
            raise ValueError("Não é possível alterar material de um lote já incinerado.")
        
        if self.posicao_sacola: self.posicao_sacola = self.posicao_sacola.upper()
        super().save(*args, **kwargs)

# 3. Auditoria
class RegistroHistorico(models.Model):
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='historico')
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    status_anterior = models.CharField(max_length=20, blank=True, null=True)
    status_novo = models.CharField(max_length=20)
    data_evento = models.DateTimeField(auto_now_add=True)
    observacao = models.TextField(blank=True, null=True)