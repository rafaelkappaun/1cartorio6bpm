"""
tc_parser.py — Parser de Termos Circunstanciados (TC)
Suporta PDF digital (sistema SESP/intranet) e arquivo Word (.docx).
O arquivo nunca é gravado em disco — processa em memória e descarta.
"""

import re
import io


# ─────────────────────────────────────────────
# EXTRAÇÃO DE TEXTO
# ─────────────────────────────────────────────

def extrair_texto_pdf(file_bytes: bytes) -> str:
    """Extrai todo o texto de um PDF (suporte a múltiplas páginas)."""
    import pdfplumber
    texto_total = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                texto_total.append(t)
    return "\n".join(texto_total)


def extrair_texto_docx(file_bytes: bytes) -> str:
    """Extrai todo o texto de um arquivo Word (.docx)."""
    from docx import Document
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


# ─────────────────────────────────────────────
# HELPERS DE REGEX
# ─────────────────────────────────────────────

def _primeiro(pattern, texto, flags=re.IGNORECASE):
    m = re.search(pattern, texto, flags)
    return m.group(1).strip() if m else ""


def _todos(pattern, texto, flags=re.IGNORECASE):
    return [m.strip() for m in re.findall(pattern, texto, flags)]


# ─────────────────────────────────────────────
# PARSER PRINCIPAL
# ─────────────────────────────────────────────

def parsear_tc(texto: str) -> dict:
    """
    Recebe o texto bruto do TC e devolve um dicionário estruturado.
    Tenta extrair múltiplos noticiados e seus itens apreendidos.
    """

    # ── BOU ──────────────────────────────────────────────────────────
    bou = (_primeiro(r'B\.?O\.?U\.?\s*[:\-]?\s*(\d{4}/\d+)', texto) or
           _primeiro(r'Boletim\s+de\s+Ocorr[êe]ncia\s*[:\-]?\s*(\d{4}/\d+)', texto) or
           _primeiro(r'N[°º]?\s*B\.?O\.?\s*[:\-]?\s*(\d{4}/\d+)', texto))

    # ── DATA DO REGISTRO ──────────────────────────────────────────────
    data_registro = (_primeiro(r'Data\s+(?:do\s+)?(?:Registro|fato|ocorr[êe]ncia)\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})', texto) or
                     _primeiro(r'(\d{2}/\d{2}/\d{4})', texto))  # fallback: primeira data

    # ── PROCESSO / NUMER DOS AUTOS ────────────────────────────────────
    processo = (_primeiro(r'(\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4})', texto) or   # CNJ
                _primeiro(r'Autos\s*[:\-]?\s*([\d\.\-/]+)', texto) or
                _primeiro(r'N[°º]?\s*Processo\s*[:\-]?\s*([\d\.\-/]+)', texto) or
                _primeiro(r'Projudi\s*[:\-]?\s*([\d\.\-/]+)', texto))

    # ── VARA ─────────────────────────────────────────────────────────
    vara = (_primeiro(r'(\d+[ªa°]?\s*Vara\s*Criminal)', texto) or
            _primeiro(r'JECRIM', texto) or
            _primeiro(r'Vara\s*[:\-]?\s*([^\n]+)', texto))

    # ── DATA DA AUDIÊNCIA ─────────────────────────────────────────────
    data_audiencia = _primeiro(
        r'(?:Audi[êe]ncia|Competi[çc][ãa]o|Designad[ao])\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})', texto)

    # ── NATUREZA PENAL ────────────────────────────────────────────────
    natureza = (_primeiro(r'Natureza\s*[:\-]?\s*([^\n]+)', texto) or
                _primeiro(r'(?:Art(?:igo)?\.?\s*\d+[^\n]{0,80})', texto))

    # ── UNIDADE / BATALHÃO ────────────────────────────────────────────
    unidade = (_primeiro(r'(\d+[°º]?\s*BPM[^\n]*)', texto) or
               _primeiro(r'Unidade\s*[:\-]?\s*([^\n]+)', texto) or
               _primeiro(r'Batalh[ãa]o\s*[:\-]?\s*([^\n]+)', texto))

    # ── POLICIAL ──────────────────────────────────────────────────────
    policial_nome = (_primeiro(r'Autua(?:nte|dor)\s*[:\-]?\s*([^\n]+)', texto) or
                     _primeiro(r'Policial\s*[:\-]?\s*([^\n]+)', texto) or
                     _primeiro(r'Agente\s*[:\-]?\s*([^\n]+)', texto))
    policial_graduacao = _primeiro(r'(Soldado|Cabo|Sargento|Subtenente|Tenente|Capitão|Major|Coronel|Delegado)', texto)
    policial_rg = _primeiro(r'RG\s*(?:do\s+)?(?:Policial|Agente|Autuante)\s*[:\-]?\s*([\d\.\-]+)', texto)

    # ── NOTICIADOS ────────────────────────────────────────────────────
    # Tenta identificar blocos separados por "NOTICIADO", "AUTUADO", "CONDUTOR", etc.
    noticiados = _extrair_noticiados(texto)

    # ── ITENS APREENDIDOS ─────────────────────────────────────────────
    itens = _extrair_itens(texto)

    # ── OBSERVAÇÃO ────────────────────────────────────────────────────
    observacao = (_primeiro(r'Observa[çc][ãa]o\s*[:\-]?\s*([^\n]+(?:\n\s+[^\n]+)*)', texto) or
                  _primeiro(r'Hist[óo]rico\s*[:\-]?\s*([^\n]+(?:\n\s+[^\n]+)*)', texto))

    return {
        'bou': bou,
        'data_registro': data_registro,
        'processo': processo,
        'vara': vara,
        'data_audiencia': data_audiencia,
        'natureza_penal': natureza,
        'unidade_origem': unidade,
        'policial_nome': policial_nome,
        'policial_graduacao': policial_graduacao,
        'policial_rg': policial_rg,
        'noticiados': noticiados,
        'itens_apreendidos': itens,
        'observacao': observacao,
        'texto_bruto': texto[:2000],  # Para diagnóstico
    }


# ─────────────────────────────────────────────
# EXTRAÇÃO DE NOTICIADOS
# ─────────────────────────────────────────────

def _extrair_noticiados(texto: str) -> list:
    """
    Tenta separar blocos de noticiados e extrair nome, RG, CPF de cada um.
    """
    noticiados = []

    # Palavras-chave que indicam início de bloco de noticiado
    marcadores = r'(?:NOTICIADO|AUTUADO|CONDUTOR|INDICIADO|RÉU|NOME DO NOTICIADO)'
    blocos = re.split(marcadores, texto, flags=re.IGNORECASE)

    for bloco in blocos[1:]:  # pula a parte antes do primeiro noticiado
        linhas = bloco.strip().split('\n')
        nome = ""
        rg = ""
        cpf = ""
        data_nasc = ""

        for linha in linhas[:20]:  # Analisa as próximas 20 linhas do bloco
            linha = linha.strip()
            if not nome and re.match(r'^[A-ZÁÉÍÓÚÃÕÂÊÎÔÛÀÇ\s]{5,}$', linha):
                nome = linha.title()
            rg_m = re.search(r'RG\s*[:\-]?\s*([\d\.\-]+)', linha, re.IGNORECASE)
            if rg_m and not rg: rg = rg_m.group(1)
            cpf_m = re.search(r'CPF\s*[:\-]?\s*([\d\.\-/]+)', linha, re.IGNORECASE)
            if cpf_m and not cpf: cpf = cpf_m.group(1)
            dn_m = re.search(r'(?:Nasc|DN|Data de Nasc)\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})', linha, re.IGNORECASE)
            if dn_m and not data_nasc: data_nasc = dn_m.group(1)

        if nome or rg or cpf:
            noticiados.append({
                'nome': nome,
                'rg': rg,
                'cpf': cpf,
                'data_nascimento': data_nasc,
            })

    # Fallback: se não encontrou blocos, tenta pelo menos o nome após "Nome:"
    if not noticiados:
        nomes = _todos(r'(?:Nome|Noticiado)\s*[:\-]\s*([A-ZÁÉÍÓÚÃÕ][^\n]{4,50})', texto)
        rgs = _todos(r'RG\s*[:\-]?\s*([\d\.\-]{5,})', texto)
        for i, nome in enumerate(nomes):
            noticiados.append({
                'nome': nome.title(),
                'rg': rgs[i] if i < len(rgs) else '',
                'cpf': '',
                'data_nascimento': '',
            })

    return noticiados


# ─────────────────────────────────────────────
# EXTRAÇÃO DE ITENS APREENDIDOS
# ─────────────────────────────────────────────

def _extrair_itens(texto: str) -> list:
    """
    Extrai os bens/entorpecentes apreendidos.
    Procura pelo bloco de apreensão e lista os itens.
    """
    itens = []

    # Tenta isolar o bloco de itens apreendidos
    match_bloco = re.search(
        r'(?:OBJETO|ITEM|BEM|MATERIAL|ENTORPECENTE|APREENDIDO)[S]?[:\s]*\n(.*?)(?:\n\n|\Z)',
        texto, re.IGNORECASE | re.DOTALL
    )
    bloco = match_bloco.group(1) if match_bloco else texto

    # Padrões de drogas conhecidas
    drogas_map = {
        'MACONHA': ['maconha', 'cannabis', 'marijuana', 'erva', 'baseado'],
        'COCAINA': ['cocaína', 'cocaina', 'pó', 'pasta base'],
        'CRACK': ['crack', 'pedra'],
        'ANFETAMINA': ['anfetamina', 'rebite', 'lança'],
        'ECSTASY': ['ecstasy', 'mdma'],
        'HAXIXE': ['haxixe', 'hash'],
    }

    # Verificar entorpecentes no texto
    texto_upper = bloco.upper()
    for droga_key, sinonimos in drogas_map.items():
        for sino in sinonimos:
            if sino.upper() in texto_upper:
                # Tenta capturar quantidade próxima
                pattern = rf'{re.escape(sino)}[^\d]{{0,50}}([\d,\.]+)\s*(g|kg|gramas?|quilos?|unidades?|pés?)?'
                m = re.search(pattern, bloco, re.IGNORECASE)
                qtd = m.group(1).replace(',', '.') if m else "0"
                unid = (m.group(2) or 'G').upper()[:2] if m else 'G'
                if unid.startswith('K'): unid = 'KG'
                if unid.startswith('U') or unid.startswith('P'): unid = 'UN'
                itens.append({
                    'categoria': 'ENTORPECENTE',
                    'substancia': droga_key,
                    'quantidade': qtd,
                    'unidade': unid,
                    'descricao': '',
                })
                break

    # Verificar outros itens comuns pela nomenclatura do TC
    outros_patterns = [
        (r'(aparelho\s+de\s+som[^\n]*)', 'SOM'),
        (r'(faca[^\n]*|canivete[^\n]*)', 'FACA'),
        (r'(simulacro[^\n]*|réplica[^\n]*)', 'SIMULACRO'),
        (r'(dinheiro[^\n]*|espécie[^\n]*|R\$\s*[\d\.,]+)', 'DINHEIRO'),
        (r'(celular[^\n]*|smartphone[^\n]*)', 'OUTROS'),
        (r'(arma\s+de\s+fogo[^\n]*|pistola[^\n]*|revólver[^\n]*)', 'OUTROS'),
    ]
    for pattern, cat in outros_patterns:
        m = re.search(pattern, bloco, re.IGNORECASE)
        if m:
            desc = m.group(1).strip()
            valor = None
            if cat == 'DINHEIRO':
                vm = re.search(r'R\$\s*([\d\.,]+)', desc)
                valor = vm.group(1).replace('.', '').replace(',', '.') if vm else None
            itens.append({
                'categoria': cat,
                'substancia': None,
                'quantidade': valor or '1',
                'unidade': 'UN',
                'descricao': desc[:200],
            })

    return itens
