from django.db import models
from django.contrib.auth.models import User

# --- CHOICES ORGANIZADOS ---
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

UNIDADES_MEDIDA_CHOICES = [
    ('G', 'Gramas (g)'),
    ('KG', 'Quilos (kg)'),
    ('UN', 'Unidades (Pés/Comprimidos)'), # Mudamos de 'U' para 'UN' para bater com o HTML
]

VARA_CHOICES = [
    ('VARA_01', '1ª Vara Criminal'),
    ('VARA_02', '2ª Vara Criminal'),
    ('VARA_03', '3ª Vara Criminal'),

]

GRADUACAO_CHOICES = [
    ('SD', 'Soldado'), ('CB', 'Cabo'), ('3SGT', '3º Sargento'),
    ('2SGT', '2º Sargento'), ('1SGT', '1º Sargento'),
    ('SUB', 'Subtenente'), ('2TEN', '2º Tenente'), ('1TEN', '1º Tenente'), 
    ('CAP', 'Capitão'), ('MAJ', 'Major'),
]

UNIDADES_PM_CHOICES = [
    ('RPA', 'RPA'),
    ('DEAEV', 'DEAEV'),
    ('ROCAM', 'ROCAM'),
    ('GOTRAN', 'GOTRAN'),
    ('CAVALARIA', 'CAVALARIA'),
    ('CHOQUE', 'CHOQUE'),
    ('CHOQUE CANIL', 'CHOQUE CANIL'),
    ('TRANSITO', 'TRANSITO'),
    ('ROTAM', 'ROTAM'),
    ('CPU', 'CPU'),
    ('P2', 'P2'),
    ('OUTRA', 'Outra Unidade (Especificar)'),
]

STATUS_MATERIAL_CHOICES = [
    ('AGUARDANDO_CONFERENCIA', 'Aguardando Conferência'), # Recém cadastrado
    ('NO_COFRE', 'No Cofre'),                             # Já pesado e guardado
    ('AUTORIZADO', 'Autorizado para Queima'),             # Tem ordem judicial, mas segue no cofre
    ('INCINERADO', 'Incinerado'),                         # Já foi destruído
]

# --- MODELOS ---

class LoteIncineracao(models.Model):
    identificador = models.CharField(max_length=50, unique=True, verbose_name="Código do Lote")
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_incineracao = models.DateTimeField(null=True, blank=True)
    responsavel = models.ForeignKey(User, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, default='ABERTO') # ABERTO, INCINERADO
    eprotocolo_geral = models.CharField(max_length=50, blank=True, null=True, verbose_name="eProtocolo do Comando")

    class Meta:
        verbose_name = "Lote de Incineração"
        verbose_name_plural = "Lotes de Incineração"

    def __str__(self):
        return f"Lote {self.identificador} - {self.status}"


class Ocorrencia(models.Model):
    bou = models.CharField(max_length=20, unique=True, verbose_name="BOU")
    vara = models.CharField(max_length=20, choices=VARA_CHOICES)
    processo = models.CharField(max_length=30, null=True, blank=True, verbose_name="PROJUDI")
    
    # Dados do Policial
    policial_nome = models.CharField(max_length=100, blank=True, null=True)
    policial_graduacao = models.CharField(max_length=10, choices=GRADUACAO_CHOICES, blank=True, null=True)
    rg_policial = models.CharField(max_length=20, blank=True, null=True)
    
    # Unidade (Lógica de Unidade de Fora)
    unidade_origem = models.CharField(max_length=20, choices=UNIDADES_PM_CHOICES, default='RPA')
    unidade_especifica = models.CharField(max_length=100, blank=True, null=True, help_text="Caso seja unidade de fora")
    
    # Administrativo
    data_entrada = models.DateTimeField(auto_now_add=True)
    data_registro = models.DateField(null=True, blank=True, verbose_name="Data do Fato/BOU")
    cartorario = models.ForeignKey(User, on_delete=models.PROTECT, related_name='registros_realizados')

    def get_nome_vara_formal(self):
        """Retorna o nome por extenso para o relatório oficial"""
        nomes = {
            'VARA_01': '1ª Vara Criminal de Cascavel',
            'VARA_02': '2ª Vara Criminal de Cascavel',
            'VARA_03': '3ª Vara Criminal de Cascavel',
            
        }
        return nomes.get(self.vara, self.get_vara_display()) 

    def save(self, *args, **kwargs):
        if self.policial_nome: 
            self.policial_nome = self.policial_nome.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"BOU {self.bou} - {self.unidade_especifica or self.get_unidade_origem_display()}"


class Noticiado(models.Model):
    ocorrencia = models.ForeignKey(Ocorrencia, on_delete=models.CASCADE, related_name='noticiados')
    nome = models.CharField(max_length=200)

    def save(self, *args, **kwargs):
        self.nome = self.nome.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nome} (BOU: {self.ocorrencia.bou})"


class Material(models.Model):
    id = models.BigAutoField(primary_key=True)
    noticiado = models.ForeignKey('Noticiado', on_delete=models.CASCADE, related_name='materiais')
    substancia = models.CharField(max_length=50, choices=DROGAS_CHOICES)
    outra_substancia = models.CharField(max_length=100, blank=True, null=True)
    
    # Pesos e Medidas
    peso_estimado = models.DecimalField(max_digits=12, decimal_places=3, verbose_name="Peso Estimado")
    peso_real = models.DecimalField(max_digits=12, decimal_places=3, blank=True, null=True, verbose_name="Peso Real")
    unidade = models.CharField(max_length=3, choices=UNIDADES_MEDIDA_CHOICES, default='G')
    
    # Cadeia de Custódia e Status
    numero_lacre = models.CharField(max_length=50, blank=True, null=True, verbose_name="Nº Lacre/Vestígio")
    status = models.CharField(max_length=30, choices=STATUS_MATERIAL_CHOICES, default='AGUARDANDO_CONFERENCIA')
    
    # Relacionamentos de Saída e Auditoria
    conferido_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='materiais_conferidos')
    data_conferencia_fisica = models.DateTimeField(null=True, blank=True)
    lote = models.ForeignKey('LoteIncineracao', on_delete=models.SET_NULL, null=True, blank=True, related_name='materiais')

    class Meta:
        verbose_name = "Material"
        verbose_name_plural = "Materiais"

    def save(self, *args, **kwargs):
        """
        REGRA DE OURO: Garante que a unidade faça sentido com a droga.
        """
        # Se for Pé de Maconha, SEMPRE será Unidade (UN)
        if self.substancia == 'PE_MACONHA':
            self.unidade = 'UN'
        
        # Se for Ecstasy e o usuário não marcou nada, ou se for Cocaína/Crack, 
        # a lógica do formulário decidirá, mas aqui garantimos o salvamento.
        super().save(*args, **kwargs)

    def peso_formatado(self):
        """
        Retorna o peso/quantidade formatado com a unidade correta.
        """
        valor = self.peso_real if self.peso_real is not None else self.peso_estimado
        
        if not valor:
            return "0,000"

        # 1. Se a UNIDADE no banco for 'UN' (Unidades)
        if self.unidade == 'UN':
            return f"{int(valor)} un"
        
        # 2. Se a UNIDADE no banco for 'KG' (Quilos)
        if self.unidade == 'KG':
            return f"{valor:,.3f}".replace(',', 'X').replace('.', ',').replace('X', '.') + " kg"
            
        # 3. Se a UNIDADE for 'G' (Gramas)
        # Se passar de 1kg, mostramos como kg para facilitar a leitura
        if valor >= 1000:
            valor_kg = valor / 1000
            return f"{valor_kg:,.3f}".replace(',', 'X').replace('.', ',').replace('X', '.') + " kg"
        
        # Padrão: Gramas
        return f"{valor:,.3f}".replace(',', 'X').replace('.', ',').replace('X', '.') + " g"

    def __str__(self):
        return f"{self.get_substancia_display()} | {self.peso_formatado()} | BOU: {self.noticiado.ocorrencia.bou}"

class RegistroHistorico(models.Model):
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='historico_set')
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    status_novo = models.CharField(max_length=20)
    data_evento = models.DateTimeField(auto_now_add=True)
    observacao = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Histórico {self.material.id} - {self.status_novo}"