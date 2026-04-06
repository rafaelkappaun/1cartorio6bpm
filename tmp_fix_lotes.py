from gestao.models import Material, LoteIncineracao
from django.contrib.auth.models import User
from datetime import datetime

user = User.objects.first()
mats = Material.objects.filter(status='AUTORIZADO', lote=None)
print(f"Encontrados {mats.count()} materiais autorizados sem lote.")

if mats.exists():
    ident = f"LOTE-{datetime.now().strftime('%Y%m')}-001"
    lote, created = LoteIncineracao.objects.get_or_create(
        identificador=ident,
        defaults={'status': 'ABERTO', 'criado_por': user}
    )
    for m in mats:
        m.lote = lote
        m.status = 'AGUARDANDO_INCINERACAO'
        m.save()
    print(f"Sucesso: {mats.count()} materiais vinculados ao {ident}.")
else:
    print("Nenhum material pendente encontrado.")
