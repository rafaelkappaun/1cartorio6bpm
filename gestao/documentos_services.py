import os
import logging
from io import BytesIO
from django.conf import settings
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from datetime import datetime
from django.utils import timezone
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF

logger = logging.getLogger(__name__)

PRETO = colors.black
BRANCO = colors.white
CINZA_CLARO = colors.Color(0.95, 0.95, 0.95)
CINZA_MEDIO = colors.Color(0.85, 0.85, 0.85)

LOGO_PARANA = os.path.join(settings.BASE_DIR, 'static_files', 'img', 'brasao_parana.svg')
LOGO_PMPR = os.path.join(settings.BASE_DIR, 'static_files', 'img', 'brasao_pmpr.svg')


def draw_svg(canvas_obj, path, x, y, width, height):
    try:
        drawing = svg2rlg(path)
        if not drawing:
            return False
        sx = width / drawing.width
        sy = height / drawing.height
        scale = min(sx, sy)
        drawing.width = drawing.width * scale
        drawing.height = drawing.height * scale
        drawing.scale(scale, scale)
        renderPDF.draw(drawing, canvas_obj, x, y)
        return True
    except Exception:
        return False


def _estilos():
    s = getSampleStyleSheet()
    
    s.add(ParagraphStyle('Titulo', fontSize=13, fontName='Helvetica-Bold',
        alignment=TA_CENTER, spaceAfter=4, textColor=PRETO))
    s.add(ParagraphStyle('Subtitulo', fontSize=10, fontName='Helvetica-Bold',
        alignment=TA_CENTER, spaceAfter=8, textColor=PRETO))
    s.add(ParagraphStyle('Corpo', fontSize=10, leading=13, fontName='Helvetica',
        alignment=TA_JUSTIFY, spaceBefore=6, spaceAfter=6))
    s.add(ParagraphStyle('CorpoLeft', fontSize=10, leading=13, fontName='Helvetica',
        alignment=TA_LEFT))
    s.add(ParagraphStyle('Centro', fontSize=10, fontName='Helvetica-Bold',
        alignment=TA_CENTER))
    s.add(ParagraphStyle('Direita', fontSize=10, fontName='Helvetica',
        alignment=TA_RIGHT))
    s.add(ParagraphStyle('Rodape', fontSize=8, fontName='Helvetica-Oblique',
        alignment=TA_CENTER, textColor=colors.Color(0.4, 0.4, 0.4)))
    s.add(ParagraphStyle('Assinatura', fontSize=9, fontName='Helvetica',
        alignment=TA_CENTER))
    return s


def _cabecalho_oficio(c, doc, cidade="CASCAVEL"):
    c.save()
    w, h = A4
    m = doc.leftMargin
    
    c.setStrokeColor(PRETO)
    c.setLineWidth(0.5)
    c.line(m, h - 45, w - m, h - 45)
    
    cx = w / 2
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(cx, h - 25, "ESTADO DO PARANA")
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(cx, h - 36, "POLICIA MILITAR DO PARANA")
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(cx, h - 47, "6o BATALHAO DE POLICIA MILITAR")
    c.setFont("Helvetica", 8)
    c.drawCentredString(cx, h - 57, f"CARTORIO DE TERMOS CIRCUNSTANCIADOS - {cidade}/PR")
    
    c.setFont("Helvetica", 7)
    c.drawCentredString(cx, 18, "6o BPM - Rua Pernambuco, 1711, Centro - Fone: (45) 3321-6200")
    
    c.restore()


def _cabecalho_landscape(c, doc):
    c.saveState()
    w, h = landscape(A4)
    m = doc.leftMargin
    
    c.setStrokeColor(PRETO)
    c.setLineWidth(0.5)
    c.line(m, h - 40, w - m, h - 40)
    
    cx = w / 2
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(cx, h - 22, "ESTADO DO PARANA - POLICIA MILITAR DO PARANA")
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(cx, h - 32, "6o BATALHAO DE POLICIA MILITAR - CASCAVEL/PR")
    
    c.setFont("Helvetica", 7)
    c.drawCentredString(cx, 15, "6o BPM - Rua Pernambuco, 1711, Centro - Fone: (45) 3321-6200")
    
    c.restoreState()


def _tabela_info(dados, estilos, cols=None):
    if cols is None:
        cols = [4*cm, 5*cm, 4*cm, 5*cm]
    
    linhas = []
    for i in range(0, len(dados), 2):
        row = []
        for j in range(2):
            idx = i + j
            if idx < len(dados):
                k, v = dados[idx]
                row.extend([Paragraph(f"<b>{k}:</b>", estilos['CorpoLeft']), Paragraph(str(v or '-'), estilos['CorpoLeft'])])
            else:
                row.extend(['', ''])
        linhas.append(row)
    
    t = Table(linhas, colWidths=cols)
    t.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, PRETO),
        ('BACKGROUND', (0,0), (0,-1), CINZA_CLARO),
        ('BACKGROUND', (2,0), (2,-1), CINZA_CLARO),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 5),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    return t


def _tabela_items(materiais, estilos, cols=None, col_headers=None):
    if cols is None:
        cols = [0.7*cm, 3*cm, 2.5*cm, 3*cm, 2*cm, 2.5*cm]
    if col_headers is None:
        col_headers = ['N', 'BOU', 'PROC', 'DESCRICAO', 'PESO', 'LACRE']
    
    dados = [col_headers]
    for i, m in enumerate(materiais):
        oc = m.noticiado.ocorrencia if m.noticiado else None
        bou = oc.bou if oc else '-'
        proc = oc.processo[:15] if oc and oc.processo else '-'
        
        if m.categoria == 'ENTORPECENTE':
            desc = m.get_substancia_display() if m.substancia else 'Entorpecente'
        elif m.categoria == 'DINHEIRO':
            desc = f"R$ {m.valor_monetario}" if m.valor_monetario else 'Dinheiro'
        else:
            desc = (m.descricao_geral or m.get_categoria_display())[:30]
        
        peso = m.peso_formatado() if m.categoria == 'ENTORPECENTE' else '-'
        lacre = m.numero_lacre or '-'
        
        dados.append([str(i+1), bou[:15], proc, desc[:25], peso, lacre[:15]])
    
    t = Table(dados, colWidths=cols, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), CINZA_CLARO),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('ALIGN', (0,0), (0,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, PRETO),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    return t


def _tabela_items_landscape(materiais, estilos, cols=None, col_headers=None):
    if cols is None:
        cols = [0.7*cm, 2.5*cm, 2*cm, 3*cm, 2.5*cm, 1.5*cm, 1.5*cm, 3.5*cm, 2*cm]
    if col_headers is None:
        col_headers = ['N', 'BOU', 'PROC', 'NOTICIADO', 'SUBST/DESC', 'PESO', 'UN', 'OBS', 'LACRE']
    
    dados = [col_headers]
    for i, m in enumerate(materiais):
        oc = m.noticiado.ocorrencia if m.noticiado else None
        bou = oc.bou if oc else '-'
        proc = oc.processo[:12] if oc and oc.processo else '-'
        noti = (m.noticiado.nome or '-')[:20]
        
        if m.categoria == 'ENTORPECENTE':
            desc = m.get_substancia_display() if m.substancia else 'Entorpecente'
        elif m.categoria == 'DINHEIRO':
            desc = f"R$ {m.valor_monetario}" if m.valor_monetario else 'Dinheiro'
        else:
            desc = (m.descricao_geral or m.get_categoria_display())[:25]
        
        peso = str(m.peso_real or m.peso_estimado or '-')
        un = m.unidade or '-'
        obs = (m.observacao_material or '-')[:25]
        lacre = m.numero_lacre or '-'
        
        dados.append([str(i+1), bou[:12], proc, noti, desc[:20], peso[:8], un[:3], obs[:20], lacre[:12]])
    
    t = Table(dados, colWidths=cols, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), CINZA_CLARO),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 7),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('ALIGN', (0,0), (0,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, PRETO),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    return t


def _bloco_assinaturas(linhas, estilos, largura=17*cm):
    cells = []
    for nome, cargo in linhas:
        cells.append(Paragraph(
            f"<br/><br/>________________________________<br/>"
            f"<b>{nome}</b><br/>{cargo}",
            estilos['Assinatura']
        ))
    
    rows = [cells[i:i+2] for i in range(0, len(cells), 2)]
    
    t = Table(rows, colWidths=[largura/2, largura/2])
    t.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 15),
    ]))
    return t


# ====================== RECIBO DE ENTRADA ======================
def gerar_recibo_entrada_pdf(ocorrencia):
    ts = timezone.now().strftime('%Y%m%d_%H%M%S')
    fname = f"recibo_entrada_{ocorrencia.bou.replace('/','_')}_{ts}.pdf"
    pasta = os.path.join(settings.MEDIA_ROOT, 'recibos', 'entrada')
    os.makedirs(pasta, exist_ok=True)
    caminho = os.path.join(pasta, fname)

    est = _estilos()
    doc = SimpleDocTemplate(caminho, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm,
                           topMargin=2.5*cm, bottomMargin=2*cm)
    st = []

    st.append(Paragraph("RECIBO DE DEPOSITO DE MATERIAIS APREENDIDOS", est['Titulo']))
    st.append(Paragraph(f"No. {ocorrencia.id}/{datetime.now().year}", est['Subtitulo']))
    st.append(Spacer(1, 10))

    und = ocorrencia.unidade_especifica if ocorrencia.unidade_origem == 'OUTRA' else ocorrencia.get_unidade_origem_display()
    dados = [
        ('BOU', ocorrencia.bou),
        ('PROJUDI', ocorrencia.processo or 'Nao informado'),
        ('VARA', ocorrencia.get_vara_display()),
        ('UNIDADE', und),
        ('NATUREZA', ocorrencia.natureza_penal or '-'),
        ('DATA FATO', ocorrencia.data_registro_bou.strftime('%d/%m/%Y') if ocorrencia.data_registro_bou else '-'),
    ]
    st.append(_tabela_info(dados, est))
    st.append(Spacer(1, 12))

    pol = f"{ocorrencia.policial_graduacao or ''} {ocorrencia.policial_nome or ''}".strip()
    rg = ocorrencia.rg_policial or ''
    
    st.append(Paragraph(
        f"Certifico que recebi do(a) <b>{pol}</b>, RG <b>{rg}</b>, da unidade <b>{und}</b>, "
        f"a custodia dos materiais discriminados abaixo, ficando responsavel pela integridade dos mesmos conforme "
        f"Lei 11.343/06 (entorpecentes) e Lei 9.099/95 (demais objetos).",
        est['Corpo']
    ))
    st.append(Spacer(1, 10))

    st.append(Paragraph("MATERIAIS RECEBIDOS", est['Centro']))
    st.append(Spacer(1, 6))

    mats = []
    for n in ocorrencia.noticiados.all():
        mats.extend(list(n.materiais.all()))
    
    if mats:
        st.append(_tabela_items(mats, est, 
            cols=[0.7*cm, 3*cm, 2.5*cm, 5*cm, 2*cm, 3.5*cm],
            col_headers=['N', 'NOTICIADO', 'CATEGORIA', 'DESCRICAO', 'PESO', 'LACRE']))
    
    st.append(Spacer(1, 6))
    st.append(Paragraph("* Peso real sera aferido na conferencia fisica.", est['Rodape']))
    st.append(Spacer(1, 20))

    cart = ocorrencia.criado_por
    nome_cart = cart.get_full_name().upper() if cart and cart.get_full_name() else "ESCRIVAO(A)"
    st.append(_bloco_assinaturas([
        (f"{pol}".upper(), f"RG: {rg} - Responsavel pela Entrega"),
        (nome_cart, "6o BPM - Recebedor / Cartorio"),
    ], est))
    st.append(Spacer(1, 15))

    data_ext = timezone.now().strftime('%d de %B de %Y')
    st.append(Paragraph(f"Cascavel/PR, {data_ext}.", est['Direita']))

    doc.build(st, onFirstPage=_cabecalho_oficio, onLaterPages=_cabecalho_oficio)
    return os.path.join('recibos', 'entrada', fname).replace("\\", "/")


# ====================== RECIBO UNICO ======================
def gerar_recibo_entrega_unico(material, usuario=None, tipo='ENTREGA'):
    ts = timezone.now().strftime('%Y%m%d%H%M%S')
    fname = f"recibo_{tipo.lower()}_{material.id}_{ts}.pdf"
    pasta = os.path.join(settings.MEDIA_ROOT, 'recibos', 'entrega_unica')
    os.makedirs(pasta, exist_ok=True)
    caminho = os.path.join(pasta, fname)

    est = _estilos()
    doc = SimpleDocTemplate(caminho, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm,
                           topMargin=2.5*cm, bottomMargin=2*cm)
    st = []

    oc = material.noticiado.ocorrencia if material.noticiado else None

    st.append(Paragraph(f"RECIBO DE {tipo}", est['Titulo']))
    st.append(Paragraph(f"No. {material.id}/{datetime.now().year}", est['Subtitulo']))
    st.append(Spacer(1, 10))

    dados = []
    if oc:
        dados.extend([
            ('BOU', oc.bou),
            ('PROJUDI', oc.processo or '-'),
            ('VARA', oc.get_vara_display()),
            ('DATA BOU', oc.data_registro_bou.strftime('%d/%m/%Y') if oc.data_registro_bou else '-'),
        ])
    dados.extend([
        ('DATA EMISSAO', timezone.now().strftime('%d/%m/%Y')),
        ('HORA', timezone.now().strftime('%H:%M')),
    ])
    st.append(_tabela_info(dados, est))
    st.append(Spacer(1, 12))

    cat = material.get_categoria_display()
    desc = material.get_substancia_display() if material.categoria == 'ENTORPECENTE' and material.substancia else (material.descricao_geral or cat)

    dados_mat = [
        ('CATEGORIA', cat),
        ('DESCRICAO', desc),
        ('N. LACRE', material.numero_lacre or 'Sem lacre'),
        ('PESO EST.', material.peso_formatado() if material.categoria == 'ENTORPECENTE' else '-'),
        ('STATUS', material.get_status_display()),
    ]
    if material.lote:
        dados_mat.append(('LOTE', material.lote.identificador))
    st.append(Paragraph("DADOS DO MATERIAL", est['Centro']))
    st.append(Spacer(1, 4))
    st.append(_tabela_info(dados_mat, est))
    st.append(Spacer(1, 12))

    if material.noticiado:
        st.append(Paragraph("NOTICIADO/PROPRIETARIO", est['Centro']))
        st.append(Spacer(1, 4))
        st.append(_tabela_info([('NOME', material.noticiado.nome), ('DEP. FIEL', 'Sim' if material.noticiado.depositario_fiel else 'Nao')], est))
        st.append(Spacer(1, 12))

    st.append(Paragraph(
        "Declaro estar ciente de que sou responsavel pelo material acima, comprometendo-me a mantelo "
        "em condicoes adequadas de custodia, conforme Lei 11.343/2006 e demais aplicaveis.",
        est['Corpo']
    ))
    st.append(Spacer(1, 25))

    st.append(_bloco_assinaturas([
        ("", "Responsavel pela Entrega / Nome, Assinatura e RG"),
        ("", f"6o BPM - Recebedor / Nome, Assinatura e Matricula"),
    ], est))
    st.append(Spacer(1, 15))

    st.append(Paragraph(f"Cascavel/PR, {timezone.now().strftime('%d de %B de %Y')}.", est['Direita']))
    st.append(Spacer(1, 10))
    st.append(Paragraph("Documento gerado pelo Sistema do 6o BPM Cascavel.", est['Rodape']))

    doc.build(st, onFirstPage=_cabecalho_oficio, onLaterPages=_cabecalho_oficio)
    return os.path.join('recibos', 'entrega_unica', fname).replace("\\", "/")


# ====================== OFICIO DE REMESSA ======================
def gerar_oficio_materiais_gerais(materiais, usuario):
    ts = timezone.now().strftime('%Y%m%d_%H%M%S')
    fname = f"oficio_remessa_{ts}.pdf"
    pasta = os.path.join(settings.MEDIA_ROOT, 'oficios')
    os.makedirs(pasta, exist_ok=True)
    caminho = os.path.join(pasta, fname)

    varas = set()
    for m in materiais:
        if m.noticiado and m.noticiado.ocorrencia:
            varas.add(m.noticiado.ocorrencia.get_vara_display())
    vara_str = ", ".join(varas) or "Vara Criminal Competente"

    ofc_id = f"{timezone.now().year}/{ts[-4:]}"

    est = _estilos()
    doc = SimpleDocTemplate(caminho, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm,
                           topMargin=2.5*cm, bottomMargin=2*cm)
    st = []

    st.append(Paragraph(f"<b>OFICIO No {ofc_id} - CARTORIO DO 6o BPM</b>", est['Titulo']))
    st.append(Spacer(1, 6))
    st.append(Paragraph(f"Cascavel/PR, {timezone.now().strftime('%d de %B de %Y')}.", est['Direita']))
    st.append(Spacer(1, 15))

    st.append(Paragraph("A(o) Excelentissimo(a) Senhor(a) Juiz(a) de Direito", est['CorpoLeft']))
    st.append(Paragraph(f"<b>{vara_str}</b>", est['CorpoLeft']))
    st.append(Paragraph("Comarca de Cascavel/PR", est['CorpoLeft']))
    st.append(Spacer(1, 10))

    st.append(Paragraph("<b>ASSUNTO:</b> Encaminhamento de materiais apreendidos - Termos Circunstanciados", est['CorpoLeft']))
    st.append(Spacer(1, 12))

    st.append(Paragraph("Excelentissimo(a) Senhor(a) Juiz(a),", est['CorpoLeft']))
    st.append(Spacer(1, 6))
    st.append(Paragraph(
        "O 6o Batalhao de Policia Militar de Cascavel/PR encaminha a Vossa Excelencia os materiais "
        "abaixo discriminados, apreendidos em ocorrencias policiais e vinculados aos respectivos "
        "Termos Circunstanciados, conforme Lei 9.099/95, para as providencias cabiveis.",
        est['Corpo']
    ))
    st.append(Spacer(1, 10))

    st.append(Paragraph("RELACAO DE MATERIAIS ENCAMINHADOS", est['Centro']))
    st.append(Spacer(1, 6))
    st.append(_tabela_items(materiais, est,
        cols=[0.7*cm, 2.5*cm, 3*cm, 5.5*cm, 3*cm],
        col_headers=['N', 'BOU', 'NOTICIADO', 'DESCRICAO DO OBJETO', 'LACRE']))
    st.append(Spacer(1, 12))

    st.append(Paragraph(
        "Solicita-se a devolucao da segunda via deste oficio devidamente assinada e carimbada, "
        "servindo como recibo de entrega.",
        est['Corpo']
    ))
    st.append(Spacer(1, 8))
    st.append(Paragraph("Respeitosamente,", est['Centro']))
    st.append(Spacer(1, 8))

    nome_user = usuario.get_full_name().upper() if usuario and usuario.get_full_name() else "ESCRIVAO(A)"
    st.append(_bloco_assinaturas([
        (nome_user, "Encarregado do Cartorio - 6o Batalhao de Policia Militar"),
        ("", "Recebido pelo Forum (assinatura e carimbo)"),
    ], est))

    doc.build(st, onFirstPage=_cabecalho_oficio, onLaterPages=_cabecalho_oficio)
    return os.path.join('oficios', fname).replace("\\", "/")


# ====================== CAPA DO LOTE ======================
def gerar_capa_lote_pdf(lote, usuario=None):
    ts = timezone.now().strftime('%Y%m%d_%H%M%S')
    fname = f"capa_lote_{lote.identificador}_{ts}.pdf"
    pasta = os.path.join(settings.MEDIA_ROOT, 'lotes', 'capas')
    os.makedirs(pasta, exist_ok=True)
    caminho = os.path.join(pasta, fname)

    mats = list(lote.materiais.all().select_related('noticiado__ocorrencia'))
    total_peso = sum(float(m.peso_real or m.peso_estimado or 0) for m in mats)

    est = _estilos()
    doc = SimpleDocTemplate(caminho, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm,
                           topMargin=2.5*cm, bottomMargin=2*cm)
    st = []

    st.append(Paragraph("TERMO DE DESTRUICAO DE ENTORPECENTES", est['Titulo']))
    st.append(Paragraph(f"LOTE {lote.identificador}", est['Subtitulo']))
    st.append(Spacer(1, 10))

    dados = [
        ('IDENTIFICADOR', lote.identificador),
        ('STATUS', lote.get_status_display()),
        ('DATA FORMACAO', lote.data_criacao.strftime('%d/%m/%Y %H:%M')),
        ('TOTAL ITENS', str(len(mats))),
        ('PROCESSOS', str(lote.processos_count)),
        ('PESO TOTAL', f"{total_peso/1000:.3f} kg" if total_peso >= 1000 else f"{total_peso:.1f} g"),
    ]
    st.append(_tabela_info(dados, est))
    st.append(Spacer(1, 12))

    st.append(Paragraph("RELACAO DE MATERIAIS", est['Centro']))
    st.append(Spacer(1, 6))
    st.append(_tabela_items(mats, est,
        cols=[0.7*cm, 2.5*cm, 2*cm, 3.5*cm, 2*cm, 2.5*cm, 3*cm],
        col_headers=['N', 'BOU', 'PROC', 'NOTICIADO', 'PESO', 'LACRE', 'SUBSTANCIA']))
    st.append(Spacer(1, 20))

    st.append(Paragraph("ASSINATURAS OBRIGATORIAS (Art. 50, Paragrafo 5o, Lei 11.343/06)", est['Centro']))
    st.append(Spacer(1, 8))
    st.append(_bloco_assinaturas([
        ("", "Oficial PM Responsavel - Posto/Graduacao e Nome"),
        ("", "Representante Vigilancia Sanitaria - Nome e CRF"),
        ("", "Promotor(a) de Justica - Nome e Matricula"),
        ("", "Testemunha - Nome e CPF"),
    ], est))

    doc.build(st, onFirstPage=_cabecalho_oficio, onLaterPages=_cabecalho_oficio)
    return os.path.join('lotes', 'capas', fname).replace("\\", "/")


# ====================== CERTIDAO DE INCINERACAO ANTECIPADA ======================
def gerar_certidao_incineracao_antecipada(lotes, usuario):
    """Gera certidão ANTES da incineração para ser levada ao fórum/MP para assinatura"""
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    fname = f"certidao_antecipada_{ts}.pdf"
    pasta = os.path.join(settings.MEDIA_ROOT, 'incineracao')
    os.makedirs(pasta, exist_ok=True)
    caminho = os.path.join(pasta, fname)

    est = _estilos()
    doc = SimpleDocTemplate(caminho, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm,
                           topMargin=2.5*cm, bottomMargin=2*cm)
    st = []

    st.append(Paragraph("CERTIDAO DE DESTRUICAO DE SUBSTANCIAS ENTORPECENTES", est['Titulo']))
    st.append(Paragraph("DOCUMENTO PARA ASSINATURA ANTECIPADA", est['Subtitulo']))
    st.append(Spacer(1, 8))

    lotes_list = list(lotes)
    
    all_mats = []
    for lote in lotes_list:
        mats = list(lote.materiais.filter(categoria='ENTORPECENTE').select_related('noticiado__ocorrencia'))
        all_mats.extend(mats)
    
    lotes_str = ", ".join([l.identificador for l in lotes_list])
    
    processos_unicos = set()
    for m in all_mats:
        if m.noticiado and m.noticiado.ocorrencia:
            proc = m.noticiado.ocorrencia.processo or m.noticiado.ocorrencia.bou
            processos_unicos.add(proc)
    
    total_peso = sum(float(m.peso_real or m.peso_estimado or 0) for m in all_mats)

    por_vara = {}
    for m in all_mats:
        if m.noticiado and m.noticiado.ocorrencia:
            vn = m.noticiado.ocorrencia.get_vara_display()
            por_vara.setdefault(vn, []).append(m)

    st.append(Paragraph(
        f"O 6o Batalhao de Policia Militar de Cascavel/PR vem respeitosamente requerer a "
        f"destruicao termica (incineracao) das substancias entorpecentes relacionadas abaixo, "
        f"em conformidade com o Art. 50, paragrafo 5o, da Lei 11.343/2006.",
        est['Corpo']
    ))
    st.append(Spacer(1, 8))

    dados_resumo = [
        ('LOTES', lotes_str),
        ('TOTAL PROCESSOS', str(len(processos_unicos))),
        ('TOTAL SUBSTANCIAS', str(len(all_mats))),
        ('PESO TOTAL APROX.', f"{total_peso/1000:.3f} kg" if total_peso >= 1000 else f"{total_peso:.1f} g"),
    ]
    st.append(_tabela_info(dados_resumo, est))
    st.append(Spacer(1, 12))

    st.append(Paragraph("RELACAO DE SUBSTANCIAS POR VARA", est['Centro']))
    st.append(Spacer(1, 6))

    for vara, mats_vara in sorted(por_vara.items()):
        st.append(Paragraph(f"<b>- {vara.upper()}</b> ({len(mats_vara)} itens)", est['CorpoLeft']))
        st.append(Spacer(1, 4))
        
        for m in mats_vara[:10]:
            oc = m.noticiado.ocorrencia if m.noticiado else None
            proc = oc.processo or oc.bou if oc else '-'
            subst = m.get_substancia_display() if m.substancia else m.get_categoria_display()
            peso = str(m.peso_real or m.peso_estimado or '-')
            lacre = m.numero_lacre or '-'
            st.append(Paragraph(
                f"  {proc[:25]} | {subst[:15]} | {peso} | Lacres: {lacre[:15]}",
                ParagraphStyle('Lista', fontSize=8, fontName='Helvetica', leading=10)
            ))
        
        if len(mats_vara) > 10:
            st.append(Paragraph(f"  ... e mais {len(mats_vara) - 10} itens", 
                ParagraphStyle('Lista', fontSize=8, fontName='Helvetica-Oblique', leading=10)))
        
        st.append(Spacer(1, 6))

    st.append(Spacer(1, 15))
    st.append(Paragraph(
        "Requeremos que seja aposta a assinatura e o carimbo neste Documento, bem como "
        "emitida a autorizacao judicial para a destruicao das substancias acima relacionadas.",
        est['Corpo']
    ))
    st.append(Spacer(1, 20))

    st.append(Paragraph("ASSINATURAS PARA AUTORIZACAO", est['Centro']))
    st.append(Spacer(1, 6))
    st.append(_bloco_assinaturas([
        ("", "Comandante do 6o BPM - Matricula e Assinatura"),
        ("", "Promotor(a) de Justica - Nome, Matricula e Assinatura"),
        ("", "Juiz(a) de Direito - Nome e Assinatura"),
    ], est))
    st.append(Spacer(1, 15))

    st.append(Paragraph(f"Cascavel/PR, {datetime.now().strftime('%d de %B de %Y')}.", est['Direita']))
    st.append(Spacer(1, 10))
    st.append(Paragraph(
        "Apos a incineracao, este Documento devera ser devolvido ao 6o BPM para baixa no sistema.",
        est['Rodape']
    ))

    doc.build(st, onFirstPage=_cabecalho_oficio, onLaterPages=_cabecalho_oficio)
    
    lote_info = [{
        'identificador': l.identificador,
        'processos': l.processos_count,
        'materiais': l.materiais.count(),
        'peso': l.peso_total
    } for l in lotes_list]
    
    return fname, lote_info


# ====================== CERTIDAO DE INCINERACAO (POS) ======================
def gerar_certidao_incineracao_coletiva(lotes, usuario):
    """Gera certidão DEPOIS da incineração (apos assinatura do termo)"""
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    fname = f"certidao_coletiva_{ts}.pdf"
    pasta = os.path.join(settings.MEDIA_ROOT, 'incineracao')
    os.makedirs(pasta, exist_ok=True)
    caminho = os.path.join(pasta, fname)

    est = _estilos()
    doc = SimpleDocTemplate(caminho, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm,
                           topMargin=2.5*cm, bottomMargin=2*cm)
    st = []

    st.append(Paragraph("CERTIDAO DE INCINERACAO EFETIVADA", est['Titulo']))
    st.append(Paragraph("DESTRUICAO DE SUBSTANCIAS ENTORPECENTES", est['Subtitulo']))
    st.append(Spacer(1, 10))

    lotes_list = list(lotes)
    lotes_str = ", ".join([l.identificador for l in lotes_list])
    
    st.append(Paragraph(
        f"Certifico e dou fe que, em data de hoje, foi realizada a destruicao termica (incineracao) "
        f"das substancias entorpecentes relacionadas nos lotes: <b>{lotes_str}</b>, "
        f"em conformidade com as autorizacoes judiciais expedidas e em observancia as normas sanitarias vigentes.",
        est['Corpo']
    ))
    st.append(Spacer(1, 10))

    all_mats = []
    for lote in lotes_list:
        all_mats.extend(list(lote.materiais.all().select_related('noticiado__ocorrencia')))

    por_vara = {}
    for m in all_mats:
        oc = m.noticiado.ocorrencia if m.noticiado else None
        vn = oc.get_vara_display() if oc else "SEM VARA"
        por_vara.setdefault(vn, []).append(m)

    for vara, ms in por_vara.items():
        st.append(Paragraph(f"- {vara.upper()}", est['Centro']))
        st.append(Spacer(1, 4))
        st.append(_tabela_items(ms, est,
            cols=[0.7*cm, 2.5*cm, 2*cm, 3*cm, 2*cm, 2.5*cm],
            col_headers=['N', 'BOU', 'PROC', 'NOTICIADO', 'PESO', 'SUBST']))

    st.append(Spacer(1, 12))
    st.append(Paragraph(f"Cascavel/PR, {datetime.now().strftime('%d de %B de %Y')}.", est['Direita']))
    st.append(Spacer(1, 8))

    st.append(Paragraph("ASSINATURAS", est['Centro']))
    st.append(Spacer(1, 6))
    st.append(_bloco_assinaturas([
        ("", "6o BPM - Encarregado da Custodia"),
        ("", "Ministerio Publico"),
        ("", "Vigilancia Sanitaria"),
        ("", "Testemunha Judiciaria"),
    ], est))

    doc.build(st, onFirstPage=_cabecalho_oficio, onLaterPages=_cabecalho_oficio)
    return fname


# ====================== CAPAS EM MASSA (LANDSCAPE) ======================
def gerar_capas_lote_coletivas(lote_ids):
    from .models import LoteIncineracao
    buf = BytesIO()

    est = _estilos()
    est.add(ParagraphStyle('CapaTitulo', fontSize=20, alignment=TA_CENTER,
        fontName='Helvetica-Bold', spaceAfter=15, textColor=PRETO))
    est.add(ParagraphStyle('CapaID', fontSize=36, alignment=TA_CENTER,
        fontName='Helvetica-Bold', spaceAfter=20, leading=42, textColor=PRETO))

    W, H = landscape(A4)
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=2*cm, rightMargin=2*cm,
                           topMargin=2.5*cm, bottomMargin=2*cm)
    st = []
    lotes = list(LoteIncineracao.objects.filter(id__in=lote_ids))

    for i, lote in enumerate(lotes):
        if i > 0:
            st.append(PageBreak())
        
        st.append(Spacer(1, 1*cm))
        st.append(Paragraph("CAIXA DE INCINERACAO", est['CapaTitulo']))
        st.append(Paragraph(f"<b>{lote.identificador}</b>", est['CapaID']))

        dados = [
            [Paragraph("<b>DATA:</b>", est['CorpoLeft']), Paragraph(lote.data_criacao.strftime('%d/%m/%Y'), est['CorpoLeft'])],
            [Paragraph("<b>ESTADO:</b>", est['CorpoLeft']), Paragraph("AGUARDANDO TRANSPORTE", est['CorpoLeft'])],
            [Paragraph("<b>PROCESSOS:</b>", est['CorpoLeft']), Paragraph(str(lote.processos_count), est['CorpoLeft'])],
            [Paragraph("<b>PESO APROX.:</b>", est['CorpoLeft']), Paragraph(f"{(lote.peso_total/1000):.2f} kg", est['CorpoLeft'])],
        ]
        t = Table(dados, colWidths=[4*cm, 14*cm])
        t.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, PRETO),
            ('BACKGROUND', (0,0), (0,-1), CINZA_CLARO),
            ('FONTSIZE', (0,0), (-1,-1), 11),
            ('PADDING', (0,0), (-1,-1), 8),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        st.append(t)
        st.append(Spacer(1, 15))

        procs = lote.processos_list
        st.append(Paragraph("<b>PROCESSOS:</b>", est['CorpoLeft']))
        st.append(Spacer(1, 4))
        st.append(Paragraph(", ".join(procs[:30]) + ("..." if len(procs) > 30 else ""), est['CorpoLeft']))
        st.append(Spacer(1, 2*cm))

        st.append(Paragraph("6o BATALHAO DE POLICIA MILITAR - CASCAVEL/PR", est['Centro']))
        st.append(Paragraph("CARTORIO DE TERMOS CIRCUNSTANCIADOS", est['Centro']))

    doc.build(st, onFirstPage=_cabecalho_landscape, onLaterPages=_cabecalho_landscape)
    pdf = buf.getvalue()
    buf.close()
    return pdf


# ====================== RELATORIO FILTRADO (LANDSCAPE) ======================
def gerar_relatorio_filtrado_pdf(materiais_qs, filtros_desc, tipo='inventario'):
    ts = timezone.now().strftime('%Y%m%d_%H%M%S')
    fname = f"relatorio_{tipo}_{ts}.pdf"
    pasta = os.path.join(settings.MEDIA_ROOT, 'relatorios')
    os.makedirs(pasta, exist_ok=True)
    caminho = os.path.join(pasta, fname)

    titulos = {
        'inventario': 'RELATORIO DE INVENTARIO GERAL',
        'incineracao': 'RELATORIO DE INCINERACAO DE ENTORPECENTES',
        'remessa': 'RELATORIO DE REMESSA AO JUDICIARIO',
        'custodia': 'RELATORIO DE CUSTODIA EM COFRE',
    }

    est = _estilos()
    W, H = landscape(A4)
    doc = SimpleDocTemplate(caminho, pagesize=landscape(A4), leftMargin=1.5*cm, rightMargin=1.5*cm,
                           topMargin=2.5*cm, bottomMargin=2*cm)
    st = []

    st.append(Paragraph(titulos.get(tipo, 'RELATORIO'), est['Titulo']))
    st.append(Paragraph(f"Gerado em {timezone.now().strftime('%d/%m/%Y as %H:%M')} - {materiais_qs.count()} registro(s)", est['Subtitulo']))
    st.append(Spacer(1, 8))

    if filtros_desc:
        pares = [(k.upper(), v) for k, v in filtros_desc.items() if v]
        if pares:
            st.append(_tabela_info(pares, est, cols=[3*cm, 5*cm, 3*cm, 5*cm, 3*cm, 4.5*cm]))
            st.append(Spacer(1, 8))

    mats = list(materiais_qs)
    ent = sum(1 for m in mats if m.categoria == 'ENTORPECENTE')
    ger = sum(1 for m in mats if m.categoria in ['SOM', 'FACA', 'SIMULACRO', 'OUTROS'])
    Bous = len(set(m.noticiado.ocorrencia.bou for m in mats if m.noticiado and m.noticiado.ocorrencia))

    resumo = [
        ('TOTAL', str(len(mats)), 'BOU UNICOS', str(Bous)),
        ('ENTORPECENTES', str(ent), 'MATERIAIS GERAIS', str(ger)),
    ]
    t_res = Table(resumo, colWidths=[4*cm, 3.5*cm, 4*cm, 3.5*cm])
    t_res.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, PRETO),
        ('BACKGROUND', (0,0), (0,-1), CINZA_CLARO),
        ('BACKGROUND', (2,0), (2,-1), CINZA_CLARO),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    st.append(t_res)
    st.append(Spacer(1, 8))

    st.append(Paragraph(f"RELACAO DETALHADA ({len(mats)} registros)", est['Centro']))
    st.append(Spacer(1, 4))
    st.append(_tabela_items_landscape(mats, est))
    st.append(Spacer(1, 15))

    st.append(Paragraph(f"Cascavel/PR, {timezone.now().strftime('%d de %B de %Y')}.", est['Direita']))
    st.append(Spacer(1, 6))
    st.append(_bloco_assinaturas([("", "Encarregado do Cartorio - 6o Batalhao de Policia Militar")], est, largura=W-3*cm))

    doc.build(st, onFirstPage=_cabecalho_landscape, onLaterPages=_cabecalho_landscape)
    return os.path.join('relatorios', fname).replace("\\", "/")
