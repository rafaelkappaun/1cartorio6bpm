import requests
import json

API = 'http://127.0.0.1:8000/api'

print('=== TESTE DE APIs REST ===')
print()

# Teste materiais
r = requests.get(f'{API}/materiais/')
print(f'GET /api/materiais/ - Status: {r.status_code}')
data = r.json()
results = data.get('results', data)
print(f'  Total: {len(results)}')

# Teste lotes
r = requests.get(f'{API}/lotes/')
print(f'GET /api/lotes/ - Status: {r.status_code}')
data = r.json()
results = data.get('results', data)
print(f'  Total: {len(results)}')

# Teste estatisticas
r = requests.get(f'{API}/materiais/estatisticas/')
print(f'GET /api/materiais/estatisticas/ - Status: {r.status_code}')
data = r.json()
print(f'  Total: {data.get("total")}')
resumo = data.get('resumo', {})
print(f'  Entorpecentes: {resumo.get("entorpecentes")}')
print(f'  No Cofre: {resumo.get("no_cofre")}')
print(f'  Incinerados: {resumo.get("incinerados")}')

# Teste naturezas penais
r = requests.get(f'{API}/naturezas-penais/')
print(f'GET /api/naturezas-penais/ - Status: {r.status_code}')

print()
print('=== APIs testadas com sucesso! ===')
