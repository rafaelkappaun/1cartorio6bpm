"""
tc_parser.py \u2014 Parser de Termos Circunstanciados (TC)
Suporta PDF digital (sistema SESP/intranet) e arquivo Word (.docx).
O arquivo nunca \u00e9 gravado em disco \u2014 processa em mem\u00f3ria e descarta.
"""

import re
import io


# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# EXTRA\u00c7\u00c3O DE TEXTO
# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def extrair_texto_pdf(file_bytes: bytes) -> str:
    """Extrai todo o texto de um PDF (suporte a m\u00faltiplas p\u00e1ginas)."""
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


# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# HELPERS DE REGEX
# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def _primeiro(pattern, texto, flags=re.IGNORECASE):
    try:
        m = re.search(pattern, texto, flags)
        if not m: return ""
        return m.group(1).strip() if m.groups() else m.group(0).strip()
    except IndexError:
        return m.group(0).strip() if m else ""


def _todos(pattern, texto, flags=re.IGNORECASE):
    return [m.strip() for m in re.findall(pattern, texto, flags)]


# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# PARSER PRINCIPAL
# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def _converter_data_extenso(texto):
    meses = {
        'janeiro': '01', 'fevereiro': '02', 'mar\u00e7o': '03', 'abril': '04',
        'maio': '05', 'junho': '06', 'julho': '07', 'agosto': '08',
        'setembro': '09', 'outubro': '10', 'novembro': '11', 'dezembro': '12'
    }
    m = re.search(r'([a-z\u00e1\u00e9\u00ed\u00f3\u00fa\u00e7]+)\s+dias\s+do\s+m\u00eas\s+de\s+([a-z\u00e1\u00ea\u00ed\u00f3\u00fa\u00e7]+)\s+do\s+ano\s+de\s+(\d{4})', texto, re.IGNORECASE)
    if m:
        dia_str = m.group(1).lower()
        dias_map = {'primeiro': '01', 'dois': '02', 'tr\u00eas': '03', 'quatro': '04', 'cinco': '05', 'seis': '06', 'sete': '07', 'oito': '08', 'nove': '09', 'dez': '10', 'onze': '11', 'doze': '12', 'treze': '13', 'quatorze': '14', 'catorze': '14', 'quinze': '15', 'dezesseis': '16', 'dezessete': '17', 'dezoito': '18', 'dezenove': '19', 'vinte': '20', 'vinte e um': '21', 'vinte e dois': '22', 'vinte e tr\u00eas': '23', 'vinte e quatro': '24', 'vinte e cinco': '25', 'vinte e seis': '26', 'vinte e sete': '27', 'vinte e oito': '28', 'vinte e nove': '29', 'trinta': '30', 'trinta e um': '31'}
        dia = dias_map.get(dia_str, dia_str.zfill(2) if dia_str.isdigit() else "01")
        mes = meses.get(m.group(2).lower(), "01")
        return f"{dia}/{mes}/{m.group(3)}"
    return ""

def parsear_tc(texto: str) -> dict:
    """
    Recebe o texto bruto do TC e devolve um dicion\u00e1rio estruturado.
    """
    # \u2500\u2500 BOU \u2500\u2500 (Suporta YYYY/NNNN e NNNN/YYYY)
    bou_match = re.search(r'B\.?O\.?U\.?\s*[:\-]?\s*(\d+/\d+)', texto, re.IGNORECASE)
    bou = bou_match.group(1) if bou_match else ""
    if bou and '/' in bou:
        parts = bou.split('/')
        if len(parts[0]) == 4 and parts[0].startswith('20'): bou = f"{parts[0]}/{parts[1]}"
        elif len(parts[1]) == 4 and parts[1].startswith('20'): bou = f"{parts[1]}/{parts[0]}"

    # \u2500\u2500 DATA DO REGISTRO \u2500\u2500
    data_registro = (_primeiro(r'Data\s+(?:do\s+)?(?:Registro|fato|ocorr\u00eancia)\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})', texto) or
                     _converter_data_extenso(texto) or
                     _primeiro(r'(\d{2}/\d{2}/\d{4})', texto))

    # \u2500\u2500 PROCESSO / NUMER DOS AUTOS \u2500\u2500 (Suporta CNJ com ou sem pontua\u00e7\u00e3o)
    processo = (_primeiro(r'(\d{7}-?\d{2}\.?\d{4}\.?\d\.?\d{2}\.?\d{4})', texto) or   
                _primeiro(r'Autos\s*[:\-]?\s*([\d\.\-/]+)', texto))

    # \u2500\u2500 VARA \u2500\u2500
    vara = (_primeiro(r'(\d+[\u00aa\u00ba]?\s*(?:Juizado|Vara)[^\n,]+)', texto) or
            _primeiro(r'(JECRIM)', texto))

    # \u2500\u2500 DATA DA AUDI\u00caNCIA \u2500\u2500
    data_audiencia = _primeiro(r'em\s+data\s+de\s+(\d{2}/\d{2}/\d{2,4})', texto)

    # \u2500\u2500 NATUREZA PENAL \u2500\u2500
    natureza = (_primeiro(r'Natureza\s*[:\-]?\s*([^\n]+)', texto) or
                _primeiro(r'fatos\s+notificados\s+como\s+([^\n]+)', texto) or
                _primeiro(r'(?:Art(?:igo)?\.?\s*\d+[^\n]{0,80})', texto))

    # \u2500\u2500 UNIDADE / BATALH\u00c3O \u2500\u2500
    unidade = (_primeiro(r'(\d+[\u00b0\u00ba]?\s*BPM[^\n]*)', texto) or
               _primeiro(r'P\.?M\.?P\.?R\.?\s*\n\s*([^\n]+)', texto) or
               _primeiro(r'Unidade\s*[:\-]?\s*([^\n]+)', texto))

    # \u2500\u2500 POLICIAL \u2500\u2500
    policial_nome = (_primeiro(r'ASSINATURA\s+POLICIAL\s+MILITAR\s*[:\-]?\s*\n\s*([A-Z\u00c1\u00c9\u00cd\u00d3\u00da\u00c3\u00d5\u00c2\u00ca\u00ce\u00d4\u00db\u00c0\u00c7\s]{5,})', texto) or
                     _primeiro(r'Agente\s*[:\-]?\s*([^\n]+)', texto))
    policial_rg = _primeiro(r'RG\s*(?:do\s+Policial)?\s*[:\-]?\s*([\d\.\-]+)', texto[texto.find('ASSINATURA POLICIAL'):] if 'ASSINATURA POLICIAL' in texto else texto)
    policial_graduacao = _primeiro(r'(Soldado|Cabo|Sargento|Subtenente|Tenente|Capit\u00e3o|Major|Coronel)', texto)

    # \u2500\u2500 NOTICIADOS \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    # Tenta identificar blocos separados por "NOTICIADO", "AUTUADO", "CONDUTOR", etc.
    noticiados = _extrair_noticiados(texto)

    # \u2500\u2500 ITENS APREENDIDOS \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    itens = _extrair_itens(texto)

    # \u2500\u2500 OBSERVA\u00c7\u00c3O \u2500\u2500
    observacao = (_primeiro(r'Observa[\u00e7\u00e7][\u00e3\u00e3]o\s*[:\-]?\s*([^\n]+(?:\n\s+[^\n]+)*)', texto) or
                  _primeiro(r'Hist[\u00f3\u00f3]rico\s*[:\-]?\s*([^\n]+(?:\n\s+[^\n]+)*)', texto) or
                  _primeiro(r'DECLARA[\u00c7\u00c7][\u00c3\u00c3]O\s+DO\s+NOTICIADO\s*[:\-]?\s*\n\s*([^\n]+(?:\n\s+[^\n]+)*)', texto))

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
        'texto_bruto': texto[:2000],  # Para diagn\u00f3stico
    }


# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# EXTRA\u00c7\u00c3O DE NOTICIADOS
# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def _extrair_noticiados(texto: str) -> list:
    noticiados = []
    
    # Busca por blocos de assinatura ou "eu [NOME]"
    m_eu = re.search(r'eu\s+([A-Z\u00c1\u00c9\u00cd\u00d3\u00da\u00c3\u00d5\u00c2\u00ca\u00ce\u00d4\u00db\u00c0\u00c7\s]{10,}),\s*RG[/]PR\s*([\d\.\-]+)', texto)
    if m_eu:
        noticiados.append({'nome': m_eu.group(1).strip().title(), 'rg': m_eu.group(2).strip(), 'cpf': '', 'data_nascimento': ''})

    # Busca em assinatura do compromissado
    m_ass = re.search(r'ASSINATURA\s+DO\s+COMPROMISSADO\s*\n\s*([A-Z\u00c1\u00c9\u00cd\u00d3\u00da\u00c3\u00d5\u00c2\u00ca\u00ce\u00d4\u00db\u00c0\u00c7\s]{10,})\s*\n\s*RG\s*[:\-]?\s*([\d\.\-]+)', texto)
    if m_ass:
        nome_ass = m_ass.group(1).strip().title()
        if not any(n['nome'] == nome_ass for n in noticiados):
            noticiados.append({'nome': nome_ass, 'rg': m_ass.group(2).strip(), 'cpf': '', 'data_nascimento': ''})

    if not noticiados:
        # Palavras-chave que indicam in\u00edcio de bloco de noticiado
        marcadores = r'(?:NOTICIADO|AUTUADO|CONDUTOR|INDICIADO|R\u00c9U|NOME DO NOTICIADO)'
        blocos = re.split(marcadores, texto, flags=re.IGNORECASE)

        for bloco in blocos[1:]:  # pula a parte antes do primeiro noticiado
            linhas = bloco.strip().split('\n')
            nome = ""; rg = ""; cpf = ""; data_nasc = ""
            for linha in linhas[:20]:
                linha = linha.strip()
                if not nome and re.match(r'^[A-Z\u00c1\u00c9\u00cd\u00d3\u00da\u00c3\u00d5\u00c2\u00ca\u00ce\u00d4\u00db\u00c0\u00c7\s]{5,}$', linha):
                    nome = linha.title()
                rg_m = re.search(r'RG\s*[:\-]?\s*([\d\.\-]+)', linha, re.IGNORECASE)
                if rg_m and not rg: rg = rg_m.group(1)
            if nome or rg:
                noticiados.append({
                    'nome': nome, 'rg': rg, 'cpf': cpf, 'data_nascimento': data_nasc,
                })

    return noticiados


# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# EXTRA\u00c7\u00c3O DE ITENS APREENDIDOS
# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def _extrair_itens(texto: str) -> list:
    """
    Extrai os bens/entorpecentes apreendidos.
    Procura pelo bloco de apreens\u00e3o e lista os itens.
    """
    itens = []

    # Tenta isolar o bloco de itens apreendidos
    match_bloco = re.search(
        r'(?:OBJETO|ITEM|BEM|MATERIAL|ENTORPECENTE|APREENDIDO)[S]?[:\s]*\n(.*?)(?:\n\n|\Z)',
        texto, re.IGNORECASE | re.DOTALL
    )
    bloco = match_bloco.group(1) if match_bloco else texto

    # Padr\u00f5es de drogas conhecidas
    drogas_map = {
        'MACONHA': ['maconha', 'cannabis', 'marijuana', 'erva', 'baseado'],
        'COCAINA': ['coca\u00edna', 'cocaina', 'p\u00f3', 'pasta base'],
        'CRACK': ['crack', 'pedra'],
        'ANFETAMINA': ['anfetamina', 'rebite', 'lan\u00e7a'],
        'ECSTASY': ['ecstasy', 'mdma'],
        'HAXIXE': ['haxixe', 'hash'],
    }

    # Verificar entorpecentes no texto
    texto_upper = bloco.upper()
    for droga_key, sinonimos in drogas_map.items():
        for sino in sinonimos:
            if sino.upper() in texto_upper:
                # Tenta capturar quantidade pr\u00f3xima
                pattern = rf'{re.escape(sino)}[^\d]{{0,50}}([\d,\.]+)\s*(g|kg|gramas?|quilos?|unidades?|p\u00e9s?)?'
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
        (r'(simulacro[^\n]*|r\u00e9plica[^\n]*)', 'SIMULACRO'),
        (r'(dinheiro[^\n]*|esp\u00e9cie[^\n]*|R\$\s*[\d\.,]+)', 'DINHEIRO'),
        (r'(celular[^\n]*|smartphone[^\n]*)', 'OUTROS'),
        (r'(arma\s+de\s+fogo[^\n]*|pistola[^\n]*|rev\u00f3lver[^\n]*)', 'OUTROS'),
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
