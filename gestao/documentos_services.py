import os
from io import BytesIO
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.pdfgen import canvas
from datetime import datetime
from django.utils import timezone
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF

# ╔═══════════════════════════════════════════════════════════════╗
# ║               CONSTANTES E CORES INSTITUCIONAIS              ║
# ╚═══════════════════════════════════════════════════════════════╝

VERDE_PMPR = colors.HexColor('#1a3a2a')
DOURADO = colors.HexColor('#c5a059')
CINZA_CLARO = colors.HexColor('#f8f9fa')
CINZA_BORDA = colors.HexColor('#dee2e6')
CINZA_TEXTO = colors.HexColor('#495057')
BRANCO = colors.white

LOGO_PARANA = os.path.join(settings.BASE_DIR, 'static_files', 'img', 'brasao_parana.svg')
LOGO_PMPR = os.path.join(settings.BASE_DIR, 'static_files', 'img', 'brasao_pmpr.svg')


def draw_svg(canvas_obj, path, x, y, width, height):
    """Auxiliar para desenhar SVG no ReportLab usando svglib"""
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
    except Exception as e:
        print(f"Erro ao desenhar SVG {path}: {e}")
        return False


def _get_styles():
    """Retorna estilos personalizados para todos os documentos"""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        'DocTitle', parent=styles['Title'],
        fontSize=14, fontName='Helvetica-Bold',
        alignment=TA_CENTER, spaceAfter=4,
        textColor=VERDE_PMPR
    ))
    styles.add(ParagraphStyle(
        'DocSubtitle', parent=styles['Normal'],
        fontSize=10, fontName='Helvetica-Bold',
        alignment=TA_CENTER, spaceAfter=12,
        textColor=CINZA_TEXTO
    ))
    styles.add(ParagraphStyle(
        'CorpoJustificado', parent=styles['Normal'],
        fontSize=10, leading=14, alignment=TA_JUSTIFY,
        fontName='Helvetica', firstLineIndent=40,
        spaceBefore=6, spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        'CorpoNormal', parent=styles['Normal'],
        fontSize=9, leading=13, alignment=TA_LEFT,
        fontName='Helvetica'
    ))
    styles.add(ParagraphStyle(
        'SectionHeader', parent=styles['Normal'],
        fontSize=10, fontName='Helvetica-Bold',
        textColor=VERDE_PMPR, spaceBefore=14, spaceAfter=6,
        borderPadding=4
    ))
    styles.add(ParagraphStyle(
        'CenterBold', alignment=TA_CENTER,
        fontSize=10, fontName='Helvetica-Bold'
    ))
    styles.add(ParagraphStyle(
        'CenterSmall', alignment=TA_CENTER,
        fontSize=8, fontName='Helvetica',
        textColor=CINZA_TEXTO
    ))
    styles.add(ParagraphStyle(
        'DireitaData', alignment=TA_RIGHT,
        fontSize=9, fontName='Helvetica'
    ))
    styles.add(ParagraphStyle(
        'Rodape', alignment=TA_CENTER,
        fontSize=7, fontName='Helvetica-Oblique',
        textColor=CINZA_TEXTO
    ))
    return styles


def _draw_header(c, doc):
    """Cabeçalho oficial com brasões do Paraná e da PMPR"""
    c.saveState()
    w, h = A4
    margin = doc.leftMargin
    logo_size = 48

    # Brasões
    draw_svg(c, LOGO_PARANA, margin, h - margin - logo_size + 5, logo_size, logo_size)
    draw_svg(c, LOGO_PMPR, w - margin - logo_size, h - margin - logo_size + 5, logo_size, logo_size)

    # Linha dourada superior
    c.setStrokeColor(DOURADO)
    c.setLineWidth(2)
    c.line(margin, h - margin + 8, w - margin, h - margin + 8)

    # Textos do cabeçalho
    cx = w / 2
    y_start = h - margin - 8
    c.setFillColor(VERDE_PMPR)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(cx, y_start, "ESTADO DO PARANÁ")
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(cx, y_start - 14, "POLÍCIA MILITAR DO PARANÁ")
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(cx, y_start - 27, "6º BATALHÃO DE POLÍCIA MILITAR")
    c.setFillColor(CINZA_TEXTO)
    c.setFont("Helvetica", 8)
    c.drawCentredString(cx, y_start - 39, "CARTÓRIO DE TERMOS CIRCUNSTANCIADOS — CASCAVEL/PR")

    # Linha divisória dupla
    line_y = y_start - 50
    c.setStrokeColor(VERDE_PMPR)
    c.setLineWidth(1.5)
    c.line(margin, line_y, w - margin, line_y)
    c.setStrokeColor(DOURADO)
    c.setLineWidth(0.5)
    c.line(margin, line_y - 3, w - margin, line_y - 3)

    # Rodapé
    c.setFillColor(CINZA_TEXTO)
    c.setFont("Helvetica-Oblique", 7)
    c.drawCentredString(cx, 22, "6º BPM — Rua Pernambuco, nº 1.711, Centro, Cascavel/PR — Fone: (45) 3321-6200")
    c.setStrokeColor(CINZA_BORDA)
    c.setLineWidth(0.5)
    c.line(margin, 18, w - margin, 18)

    c.restoreState()


def _info_box(data_pairs, styles, col_widths=None):
    """Cria uma tabela-caixa com pares de dados"""
    if col_widths is None:
        col_widths = [4 * cm, 6 * cm, 4 * cm, 4 * cm]
    rows = []
    for i in range(0, len(data_pairs), 2):
        row = []
        for j in range(2):
            idx = i + j
            if idx < len(data_pairs):
                k, v = data_pairs[idx]
                row.extend([
                    Paragraph(f"<b>{k}:</b>", styles['CorpoNormal']),
                    Paragraph(str(v or 'N/I'), styles['CorpoNormal'])
                ])
            else:
                row.extend(['', ''])
        rows.append(row)

    t = Table(rows, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, CINZA_BORDA),
        ('BACKGROUND', (0, 0), (0, -1), CINZA_CLARO),
        ('BACKGROUND', (2, 0), (2, -1), CINZA_CLARO),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    return t


def _tabela_materiais(materiais, styles, colunas='completa'):
    """Gera uma tabela profissional de materiais"""
    if colunas == 'incineracao':
        header = ['Nº', 'BOU / PROJUDI', 'NOTICIADO', 'SUBSTÂNCIA', 'PESO', 'LACRE', 'LOTE']
        widths = [0.8*cm, 3*cm, 3.5*cm, 3*cm, 2.2*cm, 2.5*cm, 2.5*cm]
    elif colunas == 'remessa':
        header = ['Nº', 'BOU', 'NOTICIADO', 'DESCRIÇÃO DO OBJETO', 'LACRE']
        widths = [0.8*cm, 2.5*cm, 3.5*cm, 7*cm, 3.7*cm]
    else:
        header = ['Nº', 'BOU', 'PROCESSO', 'CATEGORIA', 'DESCRIÇÃO', 'LACRE', 'STATUS']
        widths = [0.8*cm, 2.5*cm, 2.5*cm, 2.5*cm, 4.5*cm, 2.5*cm, 2.2*cm]

    data_table = [header]
    for idx, mat in enumerate(materiais):
        oc = mat.noticiado.ocorrencia if mat.noticiado else None
        bou = oc.bou if oc else '-'
        proc = oc.processo if oc else '-'
        noti = mat.noticiado.nome if mat.noticiado else '-'

        if colunas == 'incineracao':
            subst = mat.get_substancia_display() if mat.substancia else mat.get_categoria_display()
            peso = mat.peso_formatado()
            lacre = mat.numero_lacre or '-'
            lote_id = mat.lote.identificador if mat.lote else '-'
            row = [str(idx+1), f"{bou}\n{proc or ''}", noti[:25], subst, peso, lacre, lote_id]
        elif colunas == 'remessa':
            desc = mat.descricao_geral or mat.get_categoria_display()
            lacre = mat.numero_lacre or 'SEM LACRE'
            row = [str(idx+1), bou, noti[:25],
                   Paragraph(desc[:80], styles['CorpoNormal']), lacre]
        else:
            cat = mat.get_categoria_display()
            desc = mat.descricao_amigavel()[:35]
            lacre = mat.numero_lacre or '-'
            status = mat.get_status_display()[:25]
            row = [str(idx+1), bou, proc or '-', cat[:15], desc, lacre, status[:20]]
        data_table.append(row)

    t = Table(data_table, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        # Cabeçalho
        ('BACKGROUND', (0, 0), (-1, 0), VERDE_PMPR),
        ('TEXTCOLOR', (0, 0), (-1, 0), BRANCO),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        # Corpo
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.4, CINZA_BORDA),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        # Faixas alternadas
        *[('BACKGROUND', (0, i), (-1, i), CINZA_CLARO)
          for i in range(2, len(data_table), 2)],
    ]))
    return t


def _assinaturas(nomes_cargos, styles):
    """Gera bloco de assinaturas 2 por linha"""
    rows = []
    for i in range(0, len(nomes_cargos), 2):
        row = []
        for j in range(2):
            idx = i + j
            if idx < len(nomes_cargos):
                nome, cargo = nomes_cargos[idx]
                cell = Paragraph(
                    f"<br/><br/>________________________________________<br/>"
                    f"<b>{nome}</b><br/>{cargo}",
                    styles['CenterSmall']
                )
            else:
                cell = ''
            row.append(cell)
        rows.append(row)

    t = Table(rows, colWidths=[8.5*cm, 8.5*cm])
    t.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
    ]))
    return t


# ╔═══════════════════════════════════════════════════════════════╗
# ║          1. RECIBO DE ENTRADA (Policial → Cartório)          ║
# ╚═══════════════════════════════════════════════════════════════╝

def gerar_recibo_entrada_pdf(ocorrencia):
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    filename = f"recibo_entrada_{ocorrencia.bou.replace('/','_')}_{timestamp}.pdf"
    pasta = os.path.join(settings.MEDIA_ROOT, 'recibos', 'entrada')
    os.makedirs(pasta, exist_ok=True)
    caminho = os.path.join(pasta, filename)

    styles = _get_styles()
    doc = SimpleDocTemplate(caminho, pagesize=A4,
                            leftMargin=1.8*cm, rightMargin=1.8*cm,
                            topMargin=4.5*cm, bottomMargin=2*cm)
    Story = []

    # Título
    Story.append(Paragraph("RECIBO DE DEPÓSITO DE MATERIAIS APREENDIDOS", styles['DocTitle']))
    Story.append(Paragraph(f"Nº {ocorrencia.id}/{datetime.now().year}", styles['DocSubtitle']))
    Story.append(Spacer(1, 8))

    # Info box
    und = ocorrencia.unidade_especifica if ocorrencia.unidade_origem == 'OUTRA' else ocorrencia.get_unidade_origem_display()
    info = [
        ('BOU', ocorrencia.bou),
        ('PROJUDI', ocorrencia.processo or 'Não informado'),
        ('VARA', ocorrencia.get_vara_display()),
        ('UNIDADE', und),
        ('NATUREZA', ocorrencia.natureza_penal or 'N/I'),
        ('DATA DO FATO', ocorrencia.data_registro_bou.strftime('%d/%m/%Y') if ocorrencia.data_registro_bou else 'N/I'),
    ]
    Story.append(_info_box(info, styles))
    Story.append(Spacer(1, 12))

    # Texto legal
    pol = f"{ocorrencia.policial_graduacao or ''} {ocorrencia.policial_nome or ''}".strip()
    rg = ocorrencia.rg_policial or ''
    texto = (
        f"Certifico para os devidos fins que, na data de hoje, recebi do(a) "
        f"<b>{pol}</b>, RG <b>{rg}</b>, pertencente à unidade <b>{und}</b>, "
        f"a custódia dos materiais abaixo discriminados. "
        f"Os itens foram conferidos quanto à integridade e lacração, sendo "
        f"destinados conforme a natureza de cada material: entorpecentes para "
        f"armazenamento em cofre e posterior incineração (Lei 11.343/06); "
        f"demais objetos para encaminhamento ao Judiciário (Lei 9.099/95)."
    )
    Story.append(Paragraph(texto, styles['CorpoJustificado']))
    Story.append(Spacer(1, 10))

    # Seção: Itens
    Story.append(Paragraph("▸ RELAÇÃO DE MATERIAIS RECEBIDOS", styles['SectionHeader']))

    # Monta lista de todos os materiais
    all_mats = []
    for noti in ocorrencia.noticiados.all():
        for mat in noti.materiais.all():
            all_mats.append(mat)

    if all_mats:
        header = ['Nº', 'NOTICIADO', 'CATEGORIA', 'DESCRIÇÃO', 'PESO EST.', 'LACRE']
        widths = [0.8*cm, 3*cm, 2.5*cm, 4.5*cm, 2.5*cm, 3.5*cm]
        data_t = [header]
        for i, mat in enumerate(all_mats):
            noti_nome = mat.noticiado.nome[:20] if mat.noticiado else '-'
            cat = mat.get_categoria_display()
            if mat.categoria == 'ENTORPECENTE':
                desc = mat.get_substancia_display() if mat.substancia else 'Entorpecente'
            elif mat.categoria == 'DINHEIRO':
                desc = f"R$ {mat.valor_monetario}" if mat.valor_monetario else 'Dinheiro'
            else:
                desc = (mat.descricao_geral or cat)[:35]
            peso = mat.peso_formatado() if mat.categoria == 'ENTORPECENTE' else '-'
            lacre = mat.numero_lacre or 'SEM LACRE'
            data_t.append([str(i+1), noti_nome, cat[:15], desc, peso, lacre])

        t = Table(data_t, colWidths=widths, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), VERDE_PMPR),
            ('TEXTCOLOR', (0,0), (-1,0), BRANCO),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 0.4, CINZA_BORDA),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            *[('BACKGROUND', (0,i), (-1,i), CINZA_CLARO) for i in range(2, len(data_t), 2)],
        ]))
        Story.append(t)

    Story.append(Spacer(1, 6))
    Story.append(Paragraph(
        "* O peso real definitivo será aferido em balança de precisão durante a conferência física.",
        styles['Rodape']
    ))
    Story.append(Spacer(1, 20))

    # Assinaturas
    cartorario = ocorrencia.criado_por
    nome_cart = cartorario.get_full_name().upper() if cartorario and cartorario.get_full_name() else "ESCRIVÃO(Ã)"
    Story.append(_assinaturas([
        (f"{pol}".upper(), f"RG: {rg} — Responsável pela Entrega"),
        (nome_cart, "6º BPM — Recebedor / Cartorário"),
    ], styles))

    Story.append(Spacer(1, 10))
    data_ext = timezone.now().strftime('%d de %B de %Y às %H:%M')
    Story.append(Paragraph(f"Cascavel/PR, {data_ext}.", styles['DireitaData']))

    doc.build(Story, onFirstPage=_draw_header, onLaterPages=_draw_header)
    return os.path.join('recibos', 'entrada', filename).replace("\\", "/")


# ╔═══════════════════════════════════════════════════════════════╗
# ║       2. OFÍCIO DE REMESSA (Materiais Gerais → Fórum)        ║
# ╚═══════════════════════════════════════════════════════════════╝

def gerar_oficio_materiais_gerais(materiais, usuario):
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    filename = f"oficio_remessa_{timestamp}.pdf"
    pasta = os.path.join(settings.MEDIA_ROOT, 'oficios')
    os.makedirs(pasta, exist_ok=True)
    caminho = os.path.join(pasta, filename)

    styles = _get_styles()
    doc = SimpleDocTemplate(caminho, pagesize=A4,
                            leftMargin=1.8*cm, rightMargin=1.8*cm,
                            topMargin=4.5*cm, bottomMargin=2*cm)
    Story = []

    # Identificar a(s) vara(s)
    varas = set()
    for mat in materiais:
        if mat.noticiado and mat.noticiado.ocorrencia:
            varas.add(mat.noticiado.ocorrencia.get_vara_display())
    vara_str = ", ".join(varas) if varas else "Vara Criminal Competente"

    oficio_id = f"{timezone.now().year}/{timestamp[-4:]}"

    Story.append(Paragraph(f"<b>OFÍCIO Nº {oficio_id} — CARTÓRIO DO 6º BPM</b>", styles['DocTitle']))
    Story.append(Spacer(1, 6))

    data_ext = timezone.now().strftime('%d de %B de %Y')
    Story.append(Paragraph(f"Cascavel/PR, {data_ext}.", styles['DireitaData']))
    Story.append(Spacer(1, 15))

    Story.append(Paragraph(f"<b>À(Ao)</b> Excelentíssimo(a) Senhor(a) Juiz(a) de Direito", styles['CorpoNormal']))
    Story.append(Paragraph(f"<b>{vara_str}</b>", styles['CorpoNormal']))
    Story.append(Paragraph("Comarca de Cascavel/PR", styles['CorpoNormal']))
    Story.append(Spacer(1, 12))

    Story.append(Paragraph(
        "<b>ASSUNTO:</b> Encaminhamento de materiais apreendidos em Boletim de Ocorrência Unificado",
        styles['CorpoNormal']
    ))
    Story.append(Spacer(1, 15))

    Story.append(Paragraph("Excelentíssimo(a) Senhor(a) Juiz(a),", styles['CorpoNormal']))
    Story.append(Spacer(1, 8))

    corpo = (
        "Pelo presente ofício, o 6º Batalhão de Polícia Militar de Cascavel/PR "
        "encaminha a Vossa Excelência os materiais abaixo discriminados, devidamente "
        "apreendidos em ocorrências policiais e vinculados aos respectivos Termos "
        "Circunstanciados, conforme rito processual da Lei 9.099/95, para as "
        "providências que Vossa Excelência entender cabíveis."
    )
    Story.append(Paragraph(corpo, styles['CorpoJustificado']))
    Story.append(Spacer(1, 12))

    Story.append(Paragraph("▸ RELAÇÃO DE MATERIAIS ENCAMINHADOS", styles['SectionHeader']))
    Story.append(_tabela_materiais(materiais, styles, colunas='remessa'))
    Story.append(Spacer(1, 15))

    Story.append(Paragraph(
        "Solicita-se, após o recebimento, a gentileza de devolver a segunda via "
        "deste ofício devidamente assinada e carimbada, servindo como recibo de entrega.",
        styles['CorpoJustificado']
    ))
    Story.append(Spacer(1, 8))
    Story.append(Paragraph("Respeitosamente,", styles['CenterBold']))
    Story.append(Spacer(1, 8))

    nome_user = usuario.get_full_name().upper() if usuario and usuario.get_full_name() else "ESCRIVÃO(Ã)"
    Story.append(_assinaturas([
        (nome_user, "Encarregado do Cartório\n6º Batalhão de Polícia Militar"),
        ("", "Recebido pelo Fórum\n(assinatura e carimbo)"),
    ], styles))

    doc.build(Story, onFirstPage=_draw_header, onLaterPages=_draw_header)
    return os.path.join('oficios', filename).replace("\\", "/")


# ╔═══════════════════════════════════════════════════════════════╗
# ║        3. CAPA DO LOTE (Etiqueta da Caixa Física)            ║
# ╚═══════════════════════════════════════════════════════════════╝

def gerar_capa_lote_pdf(lote, usuario=None):
    from .models import Material
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    filename = f"capa_lote_{lote.identificador}_{timestamp}.pdf"
    pasta = os.path.join(settings.MEDIA_ROOT, 'lotes', 'capas')
    os.makedirs(pasta, exist_ok=True)
    caminho = os.path.join(pasta, filename)

    styles = _get_styles()
    doc = SimpleDocTemplate(caminho, pagesize=A4,
                            leftMargin=1.8*cm, rightMargin=1.8*cm,
                            topMargin=4.5*cm, bottomMargin=2*cm)
    Story = []

    materiais = lote.materiais.all().select_related('noticiado__ocorrencia')
    total_itens = materiais.count()
    total_peso = sum([float(m.peso_real or m.peso_estimado or 0) for m in materiais])

    Story.append(Paragraph("TERMO DE DESTRUIÇÃO DE ENTORPECENTES", styles['DocTitle']))
    Story.append(Paragraph(f"LOTE {lote.identificador}", styles['DocSubtitle']))
    Story.append(Spacer(1, 10))

    # Info do lote
    info = [
        ('IDENTIFICADOR', lote.identificador),
        ('STATUS', lote.get_status_display()),
        ('DATA DE FORMAÇÃO', lote.data_criacao.strftime('%d/%m/%Y %H:%M')),
        ('TOTAL DE ITENS', str(total_itens)),
        ('PROCESSOS/BOUs', str(lote.processos_count)),
        ('PESO ESTIMADO', f"{total_peso/1000:.3f} kg" if total_peso >= 1000 else f"{total_peso:.1f} g"),
    ]
    Story.append(_info_box(info, styles))
    Story.append(Spacer(1, 12))

    # Tabela de itens
    Story.append(Paragraph("▸ RELAÇÃO DE MATERIAIS NO LOTE", styles['SectionHeader']))
    Story.append(_tabela_materiais(materiais, styles, colunas='incineracao'))
    Story.append(Spacer(1, 20))

    # Assinaturas
    Story.append(Paragraph("▸ ASSINATURAS OBRIGATÓRIAS (Art. 50, §5º, Lei 11.343/06)", styles['SectionHeader']))
    Story.append(_assinaturas([
        ("", "Oficial PM Responsável\nPosto/Graduação e Nome"),
        ("", "Representante Vigilância Sanitária\nNome e CRF"),
        ("", "Promotor(a) de Justiça\nNome e Matrícula"),
        ("", "Testemunha\nNome e CPF"),
    ], styles))

    doc.build(Story, onFirstPage=_draw_header, onLaterPages=_draw_header)
    return os.path.join('lotes', 'capas', filename).replace("\\", "/")


# ╔═══════════════════════════════════════════════════════════════╗
# ║   4. CERTIDÃO DE INCINERAÇÃO (Coletiva, agrupada por Vara)   ║
# ╚═══════════════════════════════════════════════════════════════╝

def gerar_certidao_incineracao_coletiva(lotes, usuario):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"certidao_coletiva_{timestamp}.pdf"
    pasta = os.path.join(settings.MEDIA_ROOT, 'incineracao')
    os.makedirs(pasta, exist_ok=True)
    caminho = os.path.join(pasta, filename)

    styles = _get_styles()
    doc = SimpleDocTemplate(caminho, pagesize=A4,
                            leftMargin=1.8*cm, rightMargin=1.8*cm,
                            topMargin=4.5*cm, bottomMargin=2*cm)
    Story = []

    Story.append(Paragraph("CERTIDÃO COLETIVA DE INCINERAÇÃO E DESTRUIÇÃO", styles['DocTitle']))
    Story.append(Paragraph("DE SUBSTÂNCIAS ENTORPECENTES", styles['DocSubtitle']))
    Story.append(Spacer(1, 8))

    lotes_str = ", ".join([l.identificador for l in lotes])
    txt = (
        f"Pelo presente termo solene, o 6º Batalhão de Polícia Militar de Cascavel/PR "
        f"certifica que, em conformidade com as autorizações judiciais expedidas pelas "
        f"respectivas Varas Criminais e em observância às normas sanitárias vigentes, "
        f"procederá à destruição térmica (incineração) do material entorpecente "
        f"custodiado nesta Unidade Militar, acondicionado nos lotes: <b>{lotes_str}</b>."
    )
    Story.append(Paragraph(txt, styles['CorpoJustificado']))
    Story.append(Spacer(1, 10))

    # Agrupa por Vara
    all_mats = []
    for lote in lotes:
        all_mats.extend(list(lote.materiais.all().select_related('noticiado__ocorrencia', 'lote')))

    por_vara = {}
    for mat in all_mats:
        oc = mat.noticiado.ocorrencia if mat.noticiado else None
        vara_nome = oc.get_vara_display() if oc else "SEM VARA DEFINIDA"
        por_vara.setdefault(vara_nome, []).append(mat)

    for vara, mats in por_vara.items():
        Story.append(Paragraph(f"▸ {vara.upper()}", styles['SectionHeader']))
        Story.append(_tabela_materiais(mats, styles, colunas='incineracao'))
        Story.append(Spacer(1, 8))

    Story.append(Spacer(1, 12))
    data_ext = datetime.now().strftime('%d de %B de %Y')
    Story.append(Paragraph(f"Cascavel/PR, {data_ext}.", styles['DireitaData']))
    Story.append(Spacer(1, 8))

    Story.append(Paragraph("▸ ASSINATURAS", styles['SectionHeader']))
    Story.append(_assinaturas([
        ("", "6º BPM — Encarregado da Custódia"),
        ("", "Ministério Público"),
        ("", "Vigilância Sanitária"),
        ("", "Testemunha Judiciária"),
    ], styles))

    doc.build(Story, onFirstPage=_draw_header, onLaterPages=_draw_header)
    return filename


# ╔═══════════════════════════════════════════════════════════════╗
# ║   5. CAPAS EM MASSA (Impressão de várias capas)              ║
# ╚═══════════════════════════════════════════════════════════════╝

def gerar_capas_lote_coletivas(lote_ids):
    from .models import LoteIncineracao
    buffer = BytesIO()

    styles = _get_styles()
    styles.add(ParagraphStyle('CapaTitulo', fontSize=26, alignment=TA_CENTER,
                              spaceAfter=20, fontName='Helvetica-Bold', textColor=VERDE_PMPR))
    styles.add(ParagraphStyle('CapaID', fontSize=48, alignment=TA_CENTER,
                              spaceAfter=30, fontName='Helvetica-Bold', leading=56,
                              textColor=VERDE_PMPR))
    styles.add(ParagraphStyle('CapaCenter', alignment=TA_CENTER, fontSize=10,
                              fontName='Helvetica-Bold', textColor=CINZA_TEXTO))

    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=4.5*cm, bottomMargin=2*cm)
    Story = []
    lotes = LoteIncineracao.objects.filter(id__in=lote_ids)

    for i, lote in enumerate(lotes):
        Story.append(Spacer(1, 1*cm))
        Story.append(Paragraph("CAIXA DE INCINERAÇÃO", styles['CapaTitulo']))
        Story.append(Paragraph(f"<b>{lote.identificador}</b>", styles['CapaID']))

        data = [
            [Paragraph("<b>DATA:</b>", styles['CorpoNormal']),
             lote.data_criacao.strftime('%d/%m/%Y')],
            [Paragraph("<b>ESTADO:</b>", styles['CorpoNormal']),
             "AGUARDANDO TRANSPORTE"],
            [Paragraph("<b>PROCESSOS:</b>", styles['CorpoNormal']),
             str(lote.processos_count)],
            [Paragraph("<b>PESO APROX.:</b>", styles['CorpoNormal']),
             f"{(lote.peso_total/1000):.2f} kg"],
        ]
        t = Table(data, colWidths=[5*cm, 12*cm])
        t.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, VERDE_PMPR),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 8),
            ('FONTSIZE', (0,0), (-1,-1), 12),
            ('BACKGROUND', (0,0), (0,-1), CINZA_CLARO),
        ]))
        Story.append(t)
        Story.append(Spacer(1, 20))

        procs = lote.processos_list
        Story.append(Paragraph("<b>PROCESSOS NESTA CAIXA:</b>", styles['CorpoNormal']))
        Story.append(Spacer(1, 6))
        Story.append(Paragraph(f"<font size=10>{', '.join(procs)}</font>", styles['CorpoNormal']))

        Story.append(Spacer(1, 3*cm))
        Story.append(Paragraph("6º BATALHÃO DE POLÍCIA MILITAR — CASCAVEL/PR", styles['CapaCenter']))
        Story.append(Paragraph("CARTÓRIO DE TERMOS CIRCUNSTANCIADOS", styles['CapaCenter']))

        if i < len(lotes) - 1:
            Story.append(PageBreak())

    doc.build(Story, onFirstPage=_draw_header, onLaterPages=_draw_header)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


# ╔═══════════════════════════════════════════════════════════════╗
# ║   6. RELATÓRIO FILTRADO (gerado a partir da tela de filtros) ║
# ╚═══════════════════════════════════════════════════════════════╝

def gerar_relatorio_filtrado_pdf(materiais_qs, filtros_desc, tipo='inventario'):
    """
    Gera um PDF profissional baseado nos materiais já filtrados.
    tipo: 'inventario', 'incineracao', 'remessa', 'custodia'
    filtros_desc: dicionário com labels dos filtros aplicados
    """
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    filename = f"relatorio_{tipo}_{timestamp}.pdf"
    pasta = os.path.join(settings.MEDIA_ROOT, 'relatorios')
    os.makedirs(pasta, exist_ok=True)
    caminho = os.path.join(pasta, filename)

    styles = _get_styles()
    doc = SimpleDocTemplate(caminho, pagesize=A4,
                            leftMargin=1.5*cm, rightMargin=1.5*cm,
                            topMargin=4.5*cm, bottomMargin=2*cm)
    Story = []

    TITULOS = {
        'inventario': 'RELATÓRIO DE INVENTÁRIO GERAL',
        'incineracao': 'RELATÓRIO DE INCINERAÇÃO DE ENTORPECENTES',
        'remessa': 'RELATÓRIO DE REMESSA AO JUDICIÁRIO',
        'custodia': 'RELATÓRIO DE CUSTÓDIA EM COFRE',
    }

    Story.append(Paragraph(TITULOS.get(tipo, 'RELATÓRIO'), styles['DocTitle']))
    Story.append(Paragraph(
        f"Gerado em {timezone.now().strftime('%d/%m/%Y às %H:%M')}",
        styles['DocSubtitle']
    ))
    Story.append(Spacer(1, 8))

    # Mostrar filtros aplicados
    if filtros_desc:
        Story.append(Paragraph("▸ PARÂMETROS DE FILTRO APLICADOS", styles['SectionHeader']))
        filtro_pairs = [(k, v) for k, v in filtros_desc.items() if v]
        if filtro_pairs:
            Story.append(_info_box(filtro_pairs, styles,
                                   col_widths=[3.5*cm, 5.5*cm, 3.5*cm, 5.5*cm]))
        Story.append(Spacer(1, 10))

    materiais = list(materiais_qs)
    total = len(materiais)

    # Resumo estatístico
    Story.append(Paragraph("▸ RESUMO ESTATÍSTICO", styles['SectionHeader']))
    ent_count = sum(1 for m in materiais if m.categoria == 'ENTORPECENTE')
    ger_count = sum(1 for m in materiais if m.categoria in ['SOM','FACA','SIMULACRO','OUTROS'])
    din_count = sum(1 for m in materiais if m.categoria == 'DINHEIRO')
    bous = len(set(m.noticiado.ocorrencia.bou for m in materiais if m.noticiado and m.noticiado.ocorrencia))

    resumo_data = [
        ['Total de Itens', str(total), 'BOUs Distintos', str(bous)],
        ['Entorpecentes', str(ent_count), 'Materiais Gerais', str(ger_count)],
        ['Dinheiro/Valores', str(din_count), '', ''],
    ]
    t_res = Table(resumo_data, colWidths=[4*cm, 4.5*cm, 4*cm, 4.5*cm])
    t_res.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.4, CINZA_BORDA),
        ('BACKGROUND', (0,0), (0,-1), CINZA_CLARO),
        ('BACKGROUND', (2,0), (2,-1), CINZA_CLARO),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    Story.append(t_res)
    Story.append(Spacer(1, 12))

    # Tabela principal
    col_tipo = 'incineracao' if tipo == 'incineracao' else ('remessa' if tipo == 'remessa' else 'completa')
    Story.append(Paragraph(f"▸ RELAÇÃO DETALHADA ({total} registros)", styles['SectionHeader']))
    Story.append(_tabela_materiais(materiais, styles, colunas=col_tipo))
    Story.append(Spacer(1, 20))

    # Rodapé com data e assinatura
    data_ext = timezone.now().strftime('%d de %B de %Y')
    Story.append(Paragraph(f"Cascavel/PR, {data_ext}.", styles['DireitaData']))
    Story.append(Spacer(1, 10))
    Story.append(_assinaturas([
        ("", "Encarregado do Cartório\n6º Batalhão de Polícia Militar"),
    ], styles))

    doc.build(Story, onFirstPage=_draw_header, onLaterPages=_draw_header)
    return os.path.join('relatorios', filename).replace("\\", "/")
