"""
Script para limpar o banco e gerar dados de teste.
Gera 3 lotes por mês dentro de um semestre (6 meses = 18 lotes).
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from gestao.models import (
    Ocorrencia, Noticiado, Material, LoteIncineracao, 
    RegistroHistorico, CaixaIncineracao, NaturezaPenal, EquipePM,
    DROGAS_CHOICES, VARA_CHOICES, UNIDADES_PM_CHOICES
)
from django.utils import timezone
from datetime import date, timedelta
from django.db.models import Max
import random

def limpar_banco():
    """Remove todos os dados do banco"""
    print("[1/2] Limpando banco de dados...")
    RegistroHistorico.objects.all().delete()
    Material.objects.all().delete()
    Noticiado.objects.all().delete()
    Ocorrencia.objects.all().delete()
    LoteIncineracao.objects.all().delete()
    CaixaIncineracao.objects.all().delete()
    NaturezaPenal.objects.all().delete()
    EquipePM.objects.all().delete()
    print("   OK - Todos os dados removidos")

def criar_usuario():
    """Cria usuário admin para testes"""
    user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'first_name': 'Escrivao',
            'last_name': 'Teste',
            'email': 'admin@6bpm.pr.gov.br',
            'is_staff': True,
            'is_superuser': True,
            'is_active': True
        }
    )
    if created:
        user.set_password('admin123')
        user.save()
        print(f"   OK - Usuario admin criado (admin/admin123)")
    return user

def criar_dados_base():
    """Cria dados base (naturezas penais, equipes)"""
    naturezas = [
        ('Trafico de Drogas', 'IP'),
        ('Posse Ilegal de Armas', 'IP'),
        ('Ameaca', 'IP'),
        ('Lesao Corporal', 'IP'),
        ('Roubo', 'IP'),
        ('Furto', 'IP'),
    ]
    for nome, tipo in naturezas:
        NaturezaPenal.objects.get_or_create(nome=nome, defaults={'tipo': tipo})
    
    equipes = [
        ('Sgt. Oliveira', '1SGT', '12345678', 'RPA'),
        ('Cb. Santos', 'CB', '23456789', 'RPA'),
        ('Sd. Pereira', 'SD', '34567890', 'ROTAM'),
    ]
    for nome, grad, rg, unid in equipes:
        EquipePM.objects.get_or_create(nome=nome, defaults={
            'graduacao': grad, 'rg': rg, 'unidade': unid
        })
    print("   OK - Dados base criados")

def gerar_dados_teste():
    """Gera dados de exemplo realistas"""
    print("[2/2] Gerando dados de teste...")
    
    user = criar_usuario()
    criar_dados_base()
    
    VARAS = [v[0] for v in VARA_CHOICES]
    UNIDADES = [u[0] for u in UNIDADES_PM_CHOICES if u[0] != 'OUTRA']
    GRADUACOES = ['SD', 'CB', '3SGT', '2SGT', '1SGT', '2TEN', '1TEN', 'CAP']
    
    # Drogas com pesos (proporção realista)
    DROGAS = [
        ('MACONHA', 35),      # 35% maconha
        ('COCAINA_PO', 25),   # 25% cocaína
        ('CRACK', 20),        # 20% crack
        ('SKUNK', 8),         # 8% skunk
        ('COCAINA_CRA', 7),   # 7% crack/cocaína base
        ('HASHISH', 3),       # 3% haxixe
        ('ECSTASY', 1),      # 1% ecstasy
        ('METANFETAMINA', 1), # 1% crystal
    ]
    
    NOMES = ['JOÃO SILVA', 'PEDRO SANTOS', 'MARIA OLIVEIRA', 'CARLOS SOUZA', 
             'ANTÔNIO PEREIRA', 'PAULA FERREIRA', 'JOSÉ COSTA', 'ANA RODRIGUES',
             'LUCAS MARTINS', 'BEATRIZ LIMA', 'MATEUS CARVALHO', 'JULIANA ANDRADE']
    
    # Determinar semestre
    hoje = date.today()
    if hoje.month <= 6:
        semestre_ano = date(hoje.year, 1, 1)
    else:
        semestre_ano = date(hoje.year, 7, 1)
    
    # Contadores
    total_bous = 0
    total_materiais = 0
    total_processos_multiplos = 0
    
    # Gerar 3 lotes por mês x 6 meses = 18 lotes
    for mes in range(1, 7):
        for numero_lote_mes in range(1, 4):
            # Calcular identificador do lote
            count_total = LoteIncineracao.objects.count() + 1
            identificador = f"LOTE-{semestre_ano.year}-{count_total:03d}"
            
            # Data do lote (dia 10, 20 ou último do mês)
            if numero_lote_mes == 1:
                dia = 10
            elif numero_lote_mes == 2:
                dia = 20
            else:
                dia = 28 if mes in [1,3,5,7,8,10,12] else 27 if mes == 2 else 30
                dia = min(dia, (date(semestre_ano.year, mes, 1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)).day
            
            data_lote = date(semestre_ano.year, mes, dia)
            
            # Criar lote
            lote = LoteIncineracao.objects.create(
                identificador=identificador,
                status='ABERTO',
                criado_por=user
            )
            
            # Atualizar data_criacao
            LoteIncineracao.objects.filter(id=lote.id).update(
                data_criacao=timezone.make_aware(
                    timezone.datetime.combine(data_lote, timezone.datetime.min.time())
                )
            )
            
            # 15-20 processos por lote (vai de 15 a 20 aleatoriamente)
            qtd_processos = random.randint(15, 20)
            
            lote_materiais = 0
            lote_processos_com_multiplos = 0
            
            for i in range(qtd_processos):
                # Data do BOU (espalhada dentro do mês, ordenação por data)
                # Quanto mais antigo o lote, mais antigos os BOU's
                dias_atras = random.randint(1, 30)
                data_bou = data_lote - timedelta(days=dias_atras)
                
                # BOUs únicos
                total_bous += 1
                bou_numero = f"{data_bou.year}/{total_bous:05d}"
                
                # 70% tem processo judicial
                numero_processo = None
                if random.random() < 0.70:
                    numero_processo = f"{random.randint(1000000, 9999999)}-{random.randint(10, 99)}.{random.randint(1000, 9999)}.{random.randint(1, 8)}.{random.randint(1000, 9999)}"
                
                # Escolhas
                vara = random.choice(VARAS)
                unidade = random.choice(UNIDADES)
                graduacao = random.choice(GRADUACOES)
                nome_policial = f"PM {random.choice(NOMES).split()[0]}"
                rg_policial = f"{random.randint(10000000, 99999999)}"
                
                # Criar ocorrência
                ocorrencia = Ocorrencia.objects.create(
                    bou=bou_numero,
                    vara=vara,
                    processo=numero_processo,
                    policial_nome=nome_policial,
                    policial_graduacao=graduacao,
                    rg_policial=rg_policial,
                    unidade_origem=unidade,
                    natureza_penal='Tráfico de Drogas',
                    data_registro_bou=data_bou,
                    criado_por=user
                )
                
                # Nome do noticiado
                nome_noticiado = random.choice(NOMES)
                
                # Criar noticiado
                noticiado = Noticiado.objects.create(
                    ocorrencia=ocorrencia,
                    nome=nome_noticiado,
                    criado_por=user
                )
                
                # 1 material (80%), 2 materiais (15%), 3 materiais (5%)
                rand = random.random()
                if rand < 0.80:
                    qtd_materiais = 1
                elif rand < 0.95:
                    qtd_materiais = 2
                    lote_processos_com_multiplos += 1
                else:
                    qtd_materiais = 3
                    lote_processos_com_multiplos += 1
                
                total_processos_multiplos += lote_processos_com_multiplos
                
                # Criar pacotinhos (materiais)
                for j in range(qtd_materiais):
                    # Escolher droga (usando pesos)
                    substancia = random.choices(
                        [d[0] for d in DROGAS],
                        weights=[d[1] for d in DROGAS]
                    )[0]
                    
                    # Peso varía por tipo
                    if substancia == 'MACONHA':
                        peso = round(random.uniform(10, 500), 3)
                    elif substancia in ['COCAINA_PO', 'COCAINA_CRA']:
                        peso = round(random.uniform(1, 80), 3)
                    elif substancia == 'CRACK':
                        peso = round(random.uniform(1, 30), 3)
                    elif substancia == 'SKUNK':
                        peso = round(random.uniform(5, 200), 3)
                    else:
                        peso = round(random.uniform(1, 20), 3)
                    
                    # Lacre único
                    lacre = f"LR{str(total_bous).zfill(5)}{j+1}"
                    
                    # Criar material já no lote e autorizado
                    material = Material.objects.create(
                        noticiado=noticiado,
                        categoria='ENTORPECENTE',
                        substancia=substancia,
                        peso_estimado=peso,
                        peso_real=peso,  # Já pesado e conferido
                        unidade='G',
                        numero_lacre=lacre,
                        status='AGUARDANDO_INCINERACAO',
                        lote=lote,
                        criado_por=user
                    )
                    
                    # Registrar histórico
                    RegistroHistorico.objects.create(
                        material=material,
                        criado_por=user,
                        status_na_epoca='AGUARDANDO_INCINERACAO',
                        observacao=f"Material adicionado ao {identificador}"
                    )
                    
                    total_materiais += 1
                    lote_materiais += 1
            
            print(f"   [LOTE] {identificador}: {qtd_processos} processos, {lote_materiais} pacotinhos ({lote_processos_com_multiplos} com multiplos)")
    
    # Criar uma caixa semestral
    ano_atual = timezone.now().year
    count_caixas = CaixaIncineracao.objects.count() + 1
    caixa = CaixaIncineracao.objects.create(
        identificador=f"CAIXA-{ano_atual}-S1-{count_caixas:03d}",
        status='ABERTO',
        criado_por=user
    )
    
    # Associar todos os lotes à caixa
    lotes = LoteIncineracao.objects.filter(status='ABERTO')
    for lote in lotes:
        lote.caixa = caixa
        lote.save(update_fields=['caixa'])
    
    print(f"\n📦 Caixa {caixa.identificador} criada com {lotes.count()} lotes")
    
    # Estatísticas finais
    print(f"\n" + "=" * 60)
    print("✅ DADOS GERADOS COM SUCESSO!")
    print("=" * 60)
    print(f"   📋 {total_bous} Boletins (BOU's)")
    print(f"   📦 {total_materiais} Pacotinhos/Materiais")
    print(f"   🔢 {total_processos_multiplos} Processos com múltiplos itens")
    print(f"   📁 {LoteIncineracao.objects.count()} Lotes (3 por mês x 6 meses)")
    print(f"   📬 {CaixaIncineracao.objects.count()} Caixa(s) semestral(is)")
    print(f"   ⏳ {Material.objects.filter(status='AGUARDANDO_INCINERACAO').count()} materiais aguardando incineração")

def main():
    print("=" * 60)
    print("  GERADOR DE DADOS DE TESTE - 6º BPM")
    print("  3 lotes por mês x 6 meses = 18 lotes")
    print("=" * 60)
    print()
    
    limpar_banco()
    print()
    gerar_dados_teste()
    
    print()
    print("=" * 60)
    print("  PARA TESTAR:")
    print("  • Acesse: http://localhost:8000")
    print("  • Login: admin / admin123")
    print("  • Vá em: Lotes > Montagem de Lotes")
    print("=" * 60)

if __name__ == '__main__':
    main()
