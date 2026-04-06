import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from gestao.models import Material, Ocorrencia, LoteIncineracao

print('=== TESTE DO SISTEMA ===')
print()

print('=== RESUMO DO BANCO ===')
print(f'Materiais: {Material.objects.count()}')
print(f'Ocorrencias: {Ocorrencia.objects.count()}')
print(f'Lotes: {LoteIncineracao.objects.count()}')

print()
print('=== MATERIAIS ===')
for m in Material.objects.all():
    print(f'  ID {m.id}: {m.categoria} - Status: {m.status}')

print()
print('=== LOTES ===')
for l in LoteIncineracao.objects.all():
    print(f'  {l.identificador}: Status={l.status}')

print()
print('=== USUARIOS ===')
for u in User.objects.all():
    print(f'  {u.username} (superuser: {u.is_superuser})')

print()
print('=== VERIFICACOES ===')
# Verificar se h� admin
admin = User.objects.filter(is_superuser=True).first()
if admin:
    print(f'[OK] Usuario admin: {admin.username}')
else:
    print('[ERRO] Nenhum usuario admin!')

# Verificar materiais
if Material.objects.count() > 0:
    print(f'[OK] {Material.objects.count()} materiais cadastrados')
else:
    print('[AVISO] Nenhum material cadastrado')

# Verificar lotes
if LoteIncineracao.objects.count() > 0:
    print(f'[OK] {LoteIncineracao.objects.count()} lotes cadastrados')
else:
    print('[AVISO] Nenhum lote cadastrado')

print()
print('=== TESTE CONCLUIDO ===')
