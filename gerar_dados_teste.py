import os
import sys
import django
from datetime import datetime, timedelta
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from gestao.models import (
    Ocorrencia, Noticiado, Material, LoteIncineracao, 
    RegistroHistorico, NaturezaPenal, EquipePM
)
from django.db import transaction

def apagar_banco():
    db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
    if os.path.exists(db_path):
        os.remove(db_path)
        print("[OK] Banco de dados removido")

def criar_usuario():
    user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'first_name': 'Administrador',
            'last_name': 'Sistema',
            'email': 'admin@6bpm.pr.gov.br',
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        user.set_password('admin123')
        user.save()
        print(f"[OK] Usuario criado: admin / admin123")
    return user

def criar_naturezas_penais():
    naturezas = [
        ('Trafico de Drogas', 'CRIME'),
        ('Posse Ilegal de Armas', 'CRIME'),
        ('Ameaca', 'CRIME'),
        ('Lesao Corporal', 'CRIME'),
        ('Roubo', 'CRIME'),
        ('Furto', 'CRIME'),
        ('Estelionato', 'CRIME'),
        ('Violencia Domestica', 'CRIME'),
        ('Dano ao Patrimonio', 'CRIME'),
        ('Dirigir Embriagado', 'CONTRAVENCAO'),
    ]
    for nome, tipo in naturezas:
        NaturezaPenal.objects.get_or_create(nome=nome, defaults={'tipo': tipo})
    print(f"[OK] {len(naturezas)} naturezas penais criadas")

def criar_equipes():
    equipes = [
        ('Sgt. Oliveira', 'Sargento', '123456', '1a Cia'),
        ('Cb. Santos', 'Cabo', '234567', '1a Cia'),
        ('Sd. Pereira', 'Soldado', '345678', '2a Cia'),
        ('Cb. Lima', 'Cabo', '456789', '3a Cia'),
        ('Sgt. Costa', 'Sargento', '567890', '4a Cia'),
    ]
    for nome, grad, rg, unidade in equipes:
        EquipePM.objects.get_or_create(nome=nome, defaults={
            'graduacao': grad, 'rg': rg, 'unidade': unidade
        })
    print(f"[OK] {len(equipes)} equipes criadas")

def criar_ocorrencias(user, quantidade=150):
    varas = ['1A VARA CRIMINAL', '2A VARA CRIMINAL', '3A VARA CRIMINAL', 'VARA DE VIOLENCIA DOMESTICA', 'JUIZADO ESPECIAL CRIMINAL']
    unidades = ['RPA', 'RP2', 'RP3', 'RP4', 'OUTRA']
    graduacoes = ['SGT', 'SD', 'CB', 'TEN', 'CAP']
    
    ocorrencias = []
    base_date = datetime.now() - timedelta(days=365)
    
    for i in range(quantidade):
        data_bou = base_date + timedelta(days=random.randint(0, 365))
        numero_bou = f"{random.randint(2020, 2025)}-{random.randint(100000, 999999)}"
        
        ocorrencia = Ocorrencia.objects.create(
            bou=numero_bou,
            vara=random.choice(varas),
            processo=f"000{random.randint(1,9999)}.{random.randint(2020,2025)}.8.16.00{random.randint(1,5)}" if random.random() > 0.3 else None,
            policial_nome=f"{random.choice(['JOAO', 'MARIA', 'PEDRO', 'ANA', 'CARLOS', 'BRASILIA', 'ANTONIO', 'JOSE', 'LUIZ', 'PAULO'])} {random.choice(['SILVA', 'SANTOS', 'OLIVEIRA', 'SOUZA', 'PEREIRA', 'LIMA', 'COSTA', 'FERREIRA'])}",
            policial_graduacao=random.choice(graduacoes),
            rg_policial=f"{random.randint(100000, 999999)}",
            unidade_origem=random.choice(unidades),
            unidade_especifica="Companhia Independente" if random.random() > 0.7 else None,
            natureza_penal=random.choice(['Trafico de Drogas', 'Posse Ilegal de Armas', 'Roubo', 'Furto', 'Estelionato']),
            data_registro_bou=data_bou.date(),
            criado_por=user
        )
        ocorrencias.append(ocorrencia)
    
    print(f"[OK] {quantidade} ocorrencias criadas")
    return ocorrencias

def criar_noticiados_e_materiais(ocorrencias, user):
    nomes = ['JOAO PEDRO SILVA', 'MARIA JOSE SANTOS', 'ANTONIO CARLOS OLIVEIRA', 'ANA PAULA SOUZA', 
             'BRUNO HENRIQUE PEREIRA', 'LUCAS GABRIEL LIMA', 'RAFAEL COSTA FERREIRA', 
             'MARCOS VINICIUS RODRIGUES', 'GABRIEL HENRIQUE MARTINS', 'PEDRO HENRIQUE ALMEIDA',
             'VICTOR HUGO NUNES', 'LEONARDO DAVILA CARVALHO', 'KAIQUE MATHEUS BATISTA',
             'ALEX SANDRO TEIXEIRA', 'WASHINGTON LUIS ANDRADE', 'TIAGO HENRIQUE MOREIRA']
    
    sustancias = [
        ('COCANA', 'Cocaina'), ('CRACK', 'Crack'), ('MACONHA', 'Maconha'),
        ('LSD', 'LSD'), ('ECSTASY', 'Ecstasy'), ('REFRIIS', 'Refriis de Cocaina'),
        ('SKUNK', 'Skunk'), ('HAXIXE', 'Haxixe')
    ]
    
    categorias_materiais = [
        ('ENTORPECENTE', 0.6),
        ('ENTORPECENTE', 0.15),
        ('ENTORPECENTE', 0.15),
        ('SOM', 0.03),
        ('FACA', 0.03),
        ('SIMULACRO', 0.02),
        ('DINHEIRO', 0.02),
    ]
    
    total_materiais = 0
    
    for ocorrencia in ocorrencias:
        num_noticiados = random.randint(1, 4)
        
        for n in range(num_noticiados):
            noticiado = Noticiado.objects.create(
                ocorrencia=ocorrencia,
                nome=random.choice(nomes),
                depositario_fiel=random.random() > 0.8,
                criado_por=user
            )
            
            num_materiais = random.randint(1, 3)
            
            for m in range(num_materiais):
                cat_choice = random.choices(
                    [c[0] for c in categorias_materiais],
                    weights=[c[1] for c in categorias_materiais]
                )[0]
                
                substancia = None
                peso = None
                unidade = None
                descricao = None
                valor = None
                
                if cat_choice == 'ENTORPECENTE':
                    subst, subst_display = random.choice(sustancias)
                    peso = round(random.uniform(0.5, 150), 3)
                    unidade = 'G'
                elif cat_choice == 'DINHEIRO':
                    valor = round(random.uniform(50, 5000), 2)
                elif cat_choice == 'SOM':
                    descricao = f"{random.choice(['AMPLIFICADOR', 'CAIXA DE SOM', 'BOCA DE LOUSA', 'CAIXA AMPLIFICADA'])} {random.choice(['100W', '200W', '500W', '1000W'])} marca {random.choice(['AIWA', 'SONY', 'PHILIPS', 'GENERICO'])}"
                elif cat_choice == 'FACA':
                    descricao = f"{random.choice(['FACA DE COZINHA', 'FACA DE CACHA', 'FACA TATICA', 'FACA AUSTRALIANA'])} {random.choice(['10cm', '15cm', '20cm', '25cm'])}"
                elif cat_choice == 'SIMULACRO':
                    descricao = f"{random.choice(['Pistola', 'Revolver', 'Escopeta'])} {random.choice(['calibre 9mm', 'calibre 38', 'calibre 12'])} {random.choice(['(simulacro)', '(maquete)', '(replica)'])}"
                
                data_criacao = ocorrencia.data_registro_bou or datetime.now().date()
                
                material = Material.objects.create(
                    noticiado=noticiado,
                    categoria=cat_choice,
                    substancia=subst if cat_choice == 'ENTORPECENTE' else None,
                    peso_estimado=peso,
                    peso_real=None if random.random() > 0.5 else peso,
                    unidade=unidade,
                    descricao_geral=descricao,
                    valor_monetario=valor,
                    numero_lacre=f"LC-{random.randint(10000, 99999)}",
                    status='RECEBIDO',
                    criado_por=user
                )
                
                RegistroHistorico.objects.create(
                    material=material,
                    criado_por=user,
                    status_na_epoca='RECEBIDO',
                    observacao=f"Material registrado via BOU {ocorrencia.bou}"
                )
                total_materiais += 1
    
    print(f"[OK] {total_materiais} materiais criados")

def simular_fluxo_materiais():
    status_transicoes = [
        ('RECEBIDO', 'ARMAZENADO', 0.85),
        ('RECEBIDO', 'AGUARDANDO_OFICIO', 0.1),
        ('RECEBIDO', 'AGUARDANDO_GUIA', 0.05),
        ('ARMAZENADO', 'AUTORIZADO', 0.7),
        ('ARMAZENADO', 'AUTORIZADO', 0.7),
    ]
    
    materiais = Material.objects.filter(status='RECEBIDO')
    count = 0
    
    for mat in materiais[:int(materiais.count() * 0.7)]:
        mat.status = 'ARMAZENADO'
        mat.peso_real = mat.peso_estimado
        mat.localizacao_no_cofre = f"Prateleira {random.randint(1,10)}, Gaveta {random.choice(['A','B','C','D'])}"
        mat.save()
        
        RegistroHistorico.objects.create(
            material=mat,
            criado_por=mat.criado_por,
            status_na_epoca='ARMAZENADO',
            observacao="Conferencia fisica realizada. Peso aferido em balanca de precisao."
        )
        count += 1
    
    materiais_autorizados = Material.objects.filter(status='ARMAZENADO')
    for mat in materiais_autorizados[:int(materiais_autorizados.count() * 0.6)]:
        mat.status = 'AUTORIZADO'
        mat.save()
        
        RegistroHistorico.objects.create(
            material=mat,
            criado_por=mat.criado_por,
            status_na_epoca='AUTORIZADO',
            observacao="Despacho judicial verificado via PROJUDI. Autorizado para incineracao."
        )
        count += 1
    
    print(f"[OK] {count} transicoes de status simuladas")

def criar_lotes():
    materiais = list(Material.objects.filter(
        status='AUTORIZADO'
    ).select_related('noticiado__ocorrencia'))
    
    if not materiais:
        print("[--] Nenhum material autorizado para criar lotes")
        return
    
    processos = {}
    for mat in materiais:
        proc = mat.noticiado.ocorrencia.processo or mat.noticiado.ocorrencia.bou
        if proc not in processos:
            processos[proc] = []
        processos[proc].append(mat)
    
    processo_keys = list(processos.keys())
    random.shuffle(processo_keys)
    
    lotes_criados = 0
    for i in range(0, min(len(processo_keys), 10), 20):
        bloco = processo_keys[i:i+20]
        if not bloco:
            break
            
        identificador = f"LOTE-{datetime.now().year}-{lotes_criados + 1:03d}"
        lote = LoteIncineracao.objects.create(
            identificador=identificador,
            status='ABERTO',
            criado_por=Material.objects.first().criado_por if Material.objects.exists() else None
        )
        
        for proc in bloco:
            for mat in processos[proc]:
                mat.lote = lote
                mat.status = 'AGUARDANDO_INCINERACAO'
                mat.save()
        
        lotes_criados += 1
    
    if lotes_criados > 0:
        print(f"[OK] {lotes_criados} lotes criados com materiais autorizados")
    else:
        print("[--] Nenhum lote criado")

def criar_lotes_incinerados():
    lotes_abertos = LoteIncineracao.objects.filter(status='ABERTO')[:3]
    for lote in lotes_abertos:
        lote.status = 'INCINERADO'
        lote.data_incineracao = datetime.now() - timedelta(days=random.randint(1, 30))
        lote.eprotocolo_geral = f"EP-{random.randint(100000, 999999)}"
        lote.save()
        
        for mat in lote.materiais.all():
            mat.status = 'INCINERADO'
            mat.save()
            
            RegistroHistorico.objects.create(
                material=mat,
                criado_por=lote.criado_por,
                status_na_epoca='INCINERADO',
                observacao=f"Material incinerado. Termo assinado. Lote {lote.identificador}"
            )
    
    print(f"[OK] {lotes_abertos.count()} lotes finalizados (incinerados)")

def main():
    print("=" * 50)
    print("GERADOR DE DADOS DE TESTE - 6o BPM")
    print("=" * 50)
    
    print("\n[1/8] Apagando banco de dados...")
    apagar_banco()
    
    print("\n[2/8] Rodando migrate...")
    from django.core.management import call_command
    call_command('migrate', '--noinput')
    
    print("\n[3/8] Criando usuario admin...")
    user = criar_usuario()
    
    print("\n[4/8] Criando naturezas penais...")
    criar_naturezas_penais()
    
    print("\n[5/8] Criando equipes PM...")
    criar_equipes()
    
    print("\n[6/8] Criando ocorrencias e materiais...")
    ocorrencias = criar_ocorrencias(user, quantidade=200)
    
    print("\n[7/8] Simulando fluxo de materiais...")
    criar_noticiados_e_materiais(ocorrencias, user)
    simular_fluxo_materiais()
    
    print("\n[8/8] Criando lotes de teste...")
    criar_lotes()
    criar_lotes_incinerados()
    
    print("\n" + "=" * 50)
    print("DADOS DE TESTE GERADOS COM SUCESSO!")
    print("=" * 50)
    print("\nACESSO AO SISTEMA:")
    print("  URL: http://127.0.0.1:8000/admin/")
    print("  Usuario: admin")
    print("  Senha: admin123")
    print("\nESTATISTICAS:")
    print(f"  - Ocorrencias: {Ocorrencia.objects.count()}")
    print(f"  - Noticiados: {Noticiado.objects.count()}")
    print(f"  - Materiais: {Material.objects.count()}")
    print(f"  - Lotes: {LoteIncineracao.objects.count()}")
    print("=" * 50)

if __name__ == '__main__':
    main()
