DROGAS_CHOICES = [
    ('MACONHA', 'Maconha (Flor/Cume)'),
    ('SKUNK', 'Skunk (Maconha Importada)'),
    ('HASHISH', 'Haxixe (Hashish)'),
    ('COCAINA_PO', 'Cocaína (Pó/Branca)'),
    ('COCAINA_CRA', 'Crack (Cocaína Base)'),
    ('OPIACEOS', 'Ópio / Heroína'),
    ('MDF', 'Maconha de Fumo (MDF)'),
    ('LSD', 'LSD (Ácido)'),
    ('ECSTASY', 'Ecstasy / MDMA'),
    ('METANFETAMINA', 'Metanfetamina (Crystal)'),
    ('COCAINAMINA', 'Cocainaína (Merla)'),
    ('RECEPTACULO', 'Receptáculo/Eppendorf'),
    ('SEMENTE', 'Semente de Maconha'),
    ('COLHEITA', 'Planta/Colheita de Maconha'),
    ('OUTRA', 'Outra Substância'),
]

UNIDADES_MEDIDA_CHOICES = [
    ('G', 'Gramas (g)'),
    ('KG', 'Quilos (kg)'),
    ('UN', 'Unidades (Pés/Comprimidos)'),
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
    ('RPA', 'RPA'), ('DEAEV', 'DEAEV'), ('ROCAM', 'ROCAM'),
    ('GOTRAN', 'GOTRAN'), ('CAVALARIA', 'CAVALARIA'), ('CHOQUE', 'CHOQUE'),
    ('CHOQUE CANIL', 'CHOQUE CANIL'), ('TRANSITO', 'TRANSITO'),
    ('ROTAM', 'ROTAM'), ('CPU', 'CPU'), ('P2', 'P2'),
    ('OUTRA', 'Outra Unidade (Especificar)'),
]

CATEGORIA_CHOICES = [
    ('ENTORPECENTE', 'Entorpecente'),
    ('SOM', 'Equipamento de Som (Perturbação)'),
    ('FACA', 'Arma Branca / Faca'),
    ('SIMULACRO', 'Simulacro / Arma de Fogo'),
    ('OUTROS', 'Outros Objetos (Gerais)'),
    ('DINHEIRO', 'Dinheiro / Valores monetários'),
]

STATUS_CUSTODIA_CHOICES = [
    ('RECEBIDO', 'Entrada no Cartório (Lacre Conferido)'),
    ('CONSTATAÇÃO', 'Processamento (Auto de Constatação Realizado)'),
    ('ARMAZENADO', 'Armazenamento (No Cofre)'),
    ('RETIRADO_PERICIA', 'Saída Temporária (Enviado para Perícia Externa)'),
    ('RETORNO_PERICIA', 'Retorno de Perícia (Re-armazenado)'),
    ('AUTORIZADO', 'Aguardando Incineração (Ordem Judicial)'),
    ('TRANSPORTE', 'Em Transporte (Para Destruição)'),
    ('INCINERADO', 'Fim de Custódia (Incinerado)'),
    ('AGUARDANDO_OFICIO', 'Aguardando Geração de Ofício (Materiais Gerais)'),
    ('OFICIO_GERADO', 'Ofício Gerado (Aguardando Transporte)'),
    ('EM_TRANSPORTE_FORUM', 'Em Transporte (Para o Fórum)'),
    ('ENTREGUE_AO_JUDICIARIO', 'Entregue ao Judiciário (Fórum / Recibo Anexado)'),
    ('AGUARDANDO_GUIA', 'Aguardando Guia de Depósito (Dinheiro)'),
    ('GUIA_GERADA', 'Guia Gerada (Aguardando Depósito)'),
    ('DEPOSITADO_JUDICIALMENTE', 'Depositado (Comprovante Anexado)'),
]
