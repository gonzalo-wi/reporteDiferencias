from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from typing import List, Dict
import os

def build_diffs_pdf(filepath: str, fecha: str, filas: List[Dict]):
    doc = SimpleDocTemplate(
        filepath, 
        pagesize=A4, 
        leftMargin=2*cm, 
        rightMargin=2*cm, 
        topMargin=2*cm, 
        bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    story = []

    # Estilo personalizado para el título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#2c3e50')
    )
    
    # Estilo para subtítulos
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=10,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#34495e')
    )
    
    # Verificar si existe la imagen y agregarla
    image_path = os.path.join(os.path.dirname(filepath), "..", "images", "camion.png")
    if os.path.exists(image_path):
        try:
            # Crear imagen con tamaño fijo que mantenga proporciones
            img = Image(image_path)
            
            # Obtener dimensiones originales
            original_width = img.imageWidth
            original_height = img.imageHeight
            
            # Establecer un tamaño máximo manteniendo el aspect ratio
            max_size = 2.5*cm  # Tamaño máximo tanto para ancho como alto
            
            # Calcular el factor de escala
            scale_factor = min(max_size / original_width, max_size / original_height)
            
            # Aplicar el escalado
            img.drawWidth = original_width * scale_factor
            img.drawHeight = original_height * scale_factor
            
            img.hAlign = 'CENTER'
            story.append(img)
            story.append(Spacer(1, 15))
        except Exception as ex:
            print(f"Error cargando imagen: {ex}")
            pass  # Si hay error con la imagen, continuar sin ella
    
    # Encabezado de la empresa
    story.append(Paragraph("EL JUMILLANO", title_style))
    story.append(Paragraph("Reporte de Diferencias en Depósitos", subtitle_style))
    story.append(Spacer(1, 10))
    
    # Información del reporte
    info_style = ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#7f8c8d')
    )
    
    story.append(Paragraph(f"<b>Fecha del Reporte:</b> {fecha}", info_style))
    story.append(Paragraph(f"<b>Criterio:</b> Faltantes ≥ $10.000", info_style))
    story.append(Spacer(1, 20))

    if not filas:
        no_data_style = ParagraphStyle(
            'NoDataStyle',
            parent=styles['Normal'],
            fontSize=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#27ae60'),
            spaceAfter=20
        )
        story.append(Paragraph("✅ ¡Excelente! No se registraron diferencias significativas.", no_data_style))
        story.append(Paragraph("Todos los depósitos están dentro del rango esperado.", no_data_style))
        doc.build(story)
        return

    # Resumen estadístico
    total_faltante = sum(abs(r.get("diferencia", 0)) for r in filas)
    summary_style = ParagraphStyle(
        'SummaryStyle',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_LEFT,
        textColor=colors.HexColor('#e74c3c'),
        spaceBefore=10,
        spaceAfter=15
    )
    
    story.append(Paragraph(f"<b>📊 Resumen:</b>", summary_style))
    story.append(Paragraph(f"• <b>{len(filas)}</b> depósitos con diferencias significativas", summary_style))
    story.append(Paragraph(f"• <b>Total faltante:</b> ${total_faltante:,.0f}".replace(",", "."), summary_style))
    story.append(Spacer(1, 15))

    # Tabla de datos
    data = [["Reparto", "Esperado", "Real", "Diferencia"]]
    for r in filas:
        esperado = r.get("deposit_esperado", 0)
        real = r.get("total_amount", 0)
        diferencia = r.get("diferencia", 0)
        
        # Formatear números con separadores de miles
        esperado_fmt = f'${esperado:,.0f}'.replace(",", ".")
        real_fmt = f'${real:,.0f}'.replace(",", ".")
        diferencia_fmt = f'${diferencia:,.0f}'.replace(",", ".")
        
        # Obtener solo el número del reparto (sin texto adicional)
        reparto_numero = r.get("reparto", "")
        
        data.append([
            reparto_numero,  # Solo el número del reparto
            esperado_fmt,
            real_fmt,
            diferencia_fmt
        ])

    table = Table(data, colWidths=[3*cm, 4*cm, 4*cm, 4*cm])
    table.setStyle(TableStyle([
        # Estilo del encabezado
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor('#34495e')),
        ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,0), 12),
        ("BOTTOMPADDING", (0,0), (-1,0), 12),
        ("TOPPADDING", (0,0), (-1,0), 12),
        
        # Estilo de las filas de datos
        ("BACKGROUND", (0,1), (-1,-1), colors.white),
        ("TEXTCOLOR", (0,1), (-1,-1), colors.black),
        ("FONTNAME", (0,1), (-1,-1), "Helvetica"),
        ("FONTSIZE", (0,1), (-1,-1), 10),
        
        # Bordes y alineación
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor('#bdc3c7')),
        ("ALIGN", (1,0), (-1,-1), "RIGHT"),  # Alinear números a la derecha
        ("ALIGN", (0,0), (0,-1), "CENTER"),  # Centrar reparto
        
        # Alternar colores de filas
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor('#f8f9fa')]),
        
        # Resaltar diferencias negativas en rojo
        ("TEXTCOLOR", (3,1), (3,-1), colors.HexColor('#e74c3c')),
        ("FONTNAME", (3,1), (3,-1), "Helvetica-Bold"),
        
        # Padding para mejor legibilidad
        ("TOPPADDING", (0,1), (-1,-1), 10),
        ("BOTTOMPADDING", (0,1), (-1,-1), 10),
    ]))

    story.append(table)
    story.append(Spacer(1, 20))
    
    # Footer
    footer_style = ParagraphStyle(
        'FooterStyle',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#95a5a6')
    )
    
    story.append(Paragraph(f"Generado automáticamente el {fecha} • Sistema PAC", footer_style))
    
    doc.build(story)