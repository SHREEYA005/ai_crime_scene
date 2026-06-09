from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable, KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics import renderPDF
from PIL import Image as PILImage, ImageDraw, ImageFont
import io, os
from datetime import datetime
 
# ── COLORS ──────────────────────────────────────────────────────
DARK_NAVY   = colors.HexColor('#0D1B2A')
MID_NAVY    = colors.HexColor('#1A2E4A')
ACCENT_RED  = colors.HexColor('#C0392B')
ACCENT_BLUE = colors.HexColor('#2980B9')
LIGHT_BG    = colors.HexColor('#F0F4F8')
LIGHT_BG2   = colors.HexColor('#E8EEF4')
WHITE       = colors.white
GRAY_TEXT   = colors.HexColor('#555555')
GRAY_BORDER = colors.HexColor('#CCCCCC')
GREEN       = colors.HexColor('#27AE60')
ORANGE      = colors.HexColor('#E67E22')
 
PAGE_W, PAGE_H = A4
 
 
def _confidence_color(conf):
    if conf >= 0.80: return GREEN
    if conf >= 0.60: return ORANGE
    return ACCENT_RED
 
 
def _draw_boxes_on_image(file_path, annotations, max_w=500):
    """Draw colored bounding boxes on the image and return a PIL image."""
    try:
        pil_img = PILImage.open(file_path).convert('RGB')
        orig_w, orig_h = pil_img.size
        scale = min(max_w / orig_w, 1.0)
        new_w = int(orig_w * scale)
        new_h = int(orig_h * scale)
        pil_img = pil_img.resize((new_w, new_h), PILImage.LANCZOS)
        draw = ImageDraw.Draw(pil_img)
 
        for ann in annotations:
            x = int(ann.x * orig_w * scale)
            y = int(ann.y * orig_h * scale)
            w = int(ann.width * orig_w * scale)
            h = int(ann.height * orig_h * scale)
            color = (192, 57, 43) if ann.source == 'auto' else (39, 174, 96)
            # Draw box with thickness
            for t in range(3):
                draw.rectangle([x-t, y-t, x+w+t, y+h+t], outline=color)
            # Draw label background
            label = ann.label
            if ann.confidence:
                label += f' {round(ann.confidence*100)}%'
            box_h = 16
            draw.rectangle([x, max(0, y-box_h), x+len(label)*7+6, y], fill=color)
            draw.text((x+3, max(0, y-box_h+2)), label, fill=(255,255,255))
 
        return pil_img
    except Exception as e:
        return None
 
 
def _pil_to_rl_image(pil_img, max_w_cm=16):
    """Convert PIL image to ReportLab Image flowable."""
    buf = io.BytesIO()
    pil_img.save(buf, format='JPEG', quality=85)
    buf.seek(0)
    w_px, h_px = pil_img.size
    max_w_pt = max_w_cm * cm
    aspect = h_px / w_px
    rl_img = Image(buf, width=max_w_pt, height=max_w_pt * aspect)
    return rl_img
 
 
class CaseReportGenerator:
 
    def generate(self, case, output_path):
        doc = SimpleDocTemplate(
            output_path, pagesize=A4,
            topMargin=2.5*cm, bottomMargin=2.5*cm,
            leftMargin=2*cm, rightMargin=2*cm,
            title=f'Crime Scene Report — {case.case_number}',
            author='CrimeScene.AI',
        )
 
        styles = getSampleStyleSheet()
        story = []
 
        # ── STYLES ──────────────────────────────────────────────
        def S(name, **kw):
            return ParagraphStyle(name, parent=styles.get('Normal', styles['Normal']), **kw)
 
        title_style   = S('ReportTitle', fontSize=22, fontName='Helvetica-Bold',
                          textColor=WHITE, alignment=TA_CENTER, spaceAfter=4)
        sub_style     = S('ReportSub', fontSize=10, fontName='Helvetica',
                          textColor=colors.HexColor('#AACCEE'), alignment=TA_CENTER)
        section_style = S('Section', fontSize=13, fontName='Helvetica-Bold',
                          textColor=DARK_NAVY, spaceBefore=14, spaceAfter=6)
        body_style    = S('Body', fontSize=10, fontName='Helvetica',
                          textColor=GRAY_TEXT, leading=15, spaceAfter=4)
        label_style   = S('Label', fontSize=9, fontName='Helvetica-Bold',
                          textColor=MID_NAVY)
        mono_style    = S('Mono', fontSize=9, fontName='Courier',
                          textColor=DARK_NAVY)
        caption_style = S('Caption', fontSize=9, fontName='Helvetica-Oblique',
                          textColor=GRAY_TEXT, alignment=TA_CENTER, spaceAfter=8)
        footer_style  = S('Footer', fontSize=8, fontName='Helvetica',
                          textColor=GRAY_BORDER, alignment=TA_CENTER)
 
        # ── HEADER BANNER ───────────────────────────────────────
        header_data = [[
            Paragraph('CRIME SCENE INVESTIGATION REPORT', title_style),
        ]]
        header_table = Table(header_data, colWidths=[17*cm])
        header_table.setStyle(TableStyle([
            ('BACKGROUND',  (0,0), (-1,-1), DARK_NAVY),
            ('TOPPADDING',  (0,0), (-1,-1), 18),
            ('BOTTOMPADDING',(0,0),(-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 16),
            ('RIGHTPADDING',(0,0), (-1,-1), 16),
            ('ROUNDEDCORNERS', [6]),
        ]))
        story.append(header_table)
 
        sub_data = [[Paragraph('AI-Assisted Forensic Analysis Platform · Confidential', sub_style)]]
        sub_table = Table(sub_data, colWidths=[17*cm])
        sub_table.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,-1), MID_NAVY),
            ('TOPPADDING',    (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(sub_table)
        story.append(Spacer(1, 0.6*cm))
 
        # ── CASE INFORMATION ────────────────────────────────────
        story.append(Paragraph('● CASE INFORMATION', section_style))
        story.append(HRFlowable(width='100%', thickness=1.5, color=MID_NAVY, spaceAfter=8))
 
        now = datetime.now()
        investigator = case.created_by if hasattr(case, 'created_by') else 'System'
 
        info_data = [
            ['Case Number',    case.case_number,
             'Report Date',    now.strftime('%B %d, %Y')],
            ['Case Title',     case.title or '—',
             'Report Time',    now.strftime('%H:%M:%S')],
            ['Location',       case.location or 'Not specified',
             'Status',         case.status.upper() if case.status else 'OPEN'],
            ['Investigator ID',str(investigator),
             'Classification', 'CONFIDENTIAL'],
        ]
 
        info_table = Table(info_data, colWidths=[3.5*cm, 5.5*cm, 3.5*cm, 4.5*cm])
        info_table.setStyle(TableStyle([
            ('FONTNAME',    (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE',    (0,0), (-1,-1), 9),
            ('FONTNAME',    (0,0), (0,-1), 'Helvetica-Bold'),
            ('FONTNAME',    (2,0), (2,-1), 'Helvetica-Bold'),
            ('TEXTCOLOR',   (0,0), (0,-1), MID_NAVY),
            ('TEXTCOLOR',   (2,0), (2,-1), MID_NAVY),
            ('TEXTCOLOR',   (1,0), (1,-1), DARK_NAVY),
            ('TEXTCOLOR',   (3,0), (3,-1), DARK_NAVY),
            ('BACKGROUND',  (0,0), (0,-1), LIGHT_BG2),
            ('BACKGROUND',  (2,0), (2,-1), LIGHT_BG2),
            ('ROWBACKGROUNDS', (1,0), (1,-1), [WHITE, LIGHT_BG]),
            ('ROWBACKGROUNDS', (3,0), (3,-1), [WHITE, LIGHT_BG]),
            ('GRID',        (0,0), (-1,-1), 0.5, GRAY_BORDER),
            ('PADDING',     (0,0), (-1,-1), 7),
            ('VALIGN',      (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.5*cm))
 
        # ── SUMMARY STATS ────────────────────────────────────────
        total_evidence = len(case.evidence) if case.evidence else 0
        total_annotations = sum(len(e.annotations) for e in case.evidence) if case.evidence else 0
        auto_count = sum(1 for e in case.evidence for a in e.annotations if a.source == 'auto') if case.evidence else 0
        manual_count = total_annotations - auto_count
        avg_conf = 0
        conf_vals = [a.confidence for e in case.evidence for a in e.annotations if a.confidence] if case.evidence else []
        if conf_vals:
            avg_conf = sum(conf_vals) / len(conf_vals)
 
        story.append(Paragraph('● STATISTICAL OVERVIEW', section_style))
        story.append(HRFlowable(width='100%', thickness=1.5, color=MID_NAVY, spaceAfter=8))
 
        stats_data = [
            ['EVIDENCE FILES', 'TOTAL DETECTIONS', 'AI DETECTIONS', 'MANUAL ANNOTATIONS', 'AVG CONFIDENCE'],
            [str(total_evidence), str(total_annotations), str(auto_count), str(manual_count),
             f'{round(avg_conf*100)}%' if avg_conf else '—'],
        ]
        stats_table = Table(stats_data, colWidths=[3.4*cm]*5)
        stats_table.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,0), DARK_NAVY),
            ('TEXTCOLOR',     (0,0), (-1,0), WHITE),
            ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',      (0,0), (-1,0), 8),
            ('FONTNAME',      (0,1), (-1,1), 'Helvetica-Bold'),
            ('FONTSIZE',      (0,1), (-1,1), 18),
            ('TEXTCOLOR',     (0,1), (-1,1), MID_NAVY),
            ('ALIGNMENT',     (0,0), (-1,-1), 'CENTER'),
            ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING',    (0,0), (-1,0), 8),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('TOPPADDING',    (0,1), (-1,1), 14),
            ('BOTTOMPADDING', (0,1), (-1,1), 14),
            ('GRID',          (0,0), (-1,-1), 0.5, GRAY_BORDER),
            ('ROWBACKGROUNDS',(0,1), (-1,1), [LIGHT_BG]),
        ]))
        story.append(stats_table)
        story.append(Spacer(1, 0.6*cm))
 
        # ── EVIDENCE ITEMS ───────────────────────────────────────
        if case.evidence:
            story.append(Paragraph('● EVIDENCE ANALYSIS', section_style))
            story.append(HRFlowable(width='100%', thickness=1.5, color=MID_NAVY, spaceAfter=8))
 
            for idx, item in enumerate(case.evidence, 1):
                # Evidence header
                ev_header = [
                    [Paragraph(f'Evidence #{idx}: {item.original_filename}', S('EvH',
                        fontSize=11, fontName='Helvetica-Bold', textColor=WHITE)),
                     Paragraph(item.file_type.upper() + ' · ' + (item.status or 'pending').upper(),
                        S('EvS', fontSize=9, fontName='Helvetica', textColor=colors.HexColor('#AACCEE'),
                          alignment=TA_RIGHT))],
                ]
                ev_hdr_table = Table(ev_header, colWidths=[11*cm, 6*cm])
                ev_hdr_table.setStyle(TableStyle([
                    ('BACKGROUND',    (0,0), (-1,-1), MID_NAVY),
                    ('PADDING',       (0,0), (-1,-1), 8),
                    ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
                ]))
                story.append(ev_hdr_table)
 
                # Upload metadata
                meta_rows = []
                if item.uploaded_at:
                    meta_rows.append(['Uploaded', item.uploaded_at.strftime('%B %d, %Y at %H:%M')])
                meta_rows.append(['File Type', item.file_type.upper()])
                meta_rows.append(['Detections', str(len(item.annotations))])
                if meta_rows:
                    meta_table = Table(meta_rows, colWidths=[3*cm, 14*cm])
                    meta_table.setStyle(TableStyle([
                        ('FONTNAME',   (0,0), (0,-1), 'Helvetica-Bold'),
                        ('FONTSIZE',   (0,0), (-1,-1), 8),
                        ('TEXTCOLOR',  (0,0), (0,-1), MID_NAVY),
                        ('TEXTCOLOR',  (1,0), (1,-1), GRAY_TEXT),
                        ('BACKGROUND', (0,0), (-1,-1), LIGHT_BG),
                        ('GRID',       (0,0), (-1,-1), 0.3, GRAY_BORDER),
                        ('PADDING',    (0,0), (-1,-1), 5),
                    ]))
                    story.append(meta_table)
 
                story.append(Spacer(1, 0.3*cm))
 
                # Annotated image
                if item.file_type in ['jpg', 'jpeg', 'png'] and os.path.exists(item.file_path):
                    pil_img = _draw_boxes_on_image(item.file_path, item.annotations or [])
                    if pil_img:
                        rl_img = _pil_to_rl_image(pil_img, max_w_cm=15)
                        img_table = Table([[rl_img]], colWidths=[17*cm])
                        img_table.setStyle(TableStyle([
                            ('ALIGN',   (0,0), (-1,-1), 'CENTER'),
                            ('BORDER',  (0,0), (-1,-1), 1, GRAY_BORDER),
                            ('PADDING', (0,0), (-1,-1), 4),
                            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#1A1A1A')),
                        ]))
                        story.append(img_table)
                        story.append(Paragraph(
                            f'Figure {idx}: {item.original_filename} — Red boxes = AI detected, Green boxes = Manual annotations',
                            caption_style))
 
                # Detection table
                if item.annotations:
                    story.append(Paragraph(f'Detection Results — {len(item.annotations)} objects identified:', label_style))
                    story.append(Spacer(1, 0.2*cm))
 
                    det_header = [['#', 'Object Label', 'Detection Source', 'Confidence Score', 'Confidence Level']]
                    det_rows = []
                    for i, ann in enumerate(item.annotations, 1):
                        conf_pct = f'{round(ann.confidence*100, 1)}%' if ann.confidence else '—'
                        if ann.confidence:
                            if ann.confidence >= 0.80: level = 'HIGH'
                            elif ann.confidence >= 0.60: level = 'MEDIUM'
                            else: level = 'LOW'
                        else:
                            level = 'MANUAL'
                        det_rows.append([
                            str(i),
                            ann.label.upper(),
                            ann.source.upper() if ann.source else 'MANUAL',
                            conf_pct,
                            level,
                        ])
 
                    det_table = Table(det_header + det_rows,
                                      colWidths=[1*cm, 5*cm, 4*cm, 3.5*cm, 3.5*cm])
                    style_cmds = [
                        ('BACKGROUND',    (0,0), (-1,0), DARK_NAVY),
                        ('TEXTCOLOR',     (0,0), (-1,0), WHITE),
                        ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
                        ('FONTSIZE',      (0,0), (-1,0), 9),
                        ('FONTSIZE',      (0,1), (-1,-1), 9),
                        ('FONTNAME',      (0,1), (-1,-1), 'Helvetica'),
                        ('GRID',          (0,0), (-1,-1), 0.5, GRAY_BORDER),
                        ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
                        ('ALIGN',         (1,0), (1,-1), 'LEFT'),
                        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
                        ('PADDING',       (0,0), (-1,-1), 7),
                        ('ROWBACKGROUNDS',(0,1), (-1,-1), [WHITE, LIGHT_BG]),
                    ]
                    # Color confidence level column
                    for i, ann in enumerate(item.annotations, 1):
                        if ann.confidence:
                            c = _confidence_color(ann.confidence)
                            style_cmds.append(('TEXTCOLOR', (4,i), (4,i), c))
                            style_cmds.append(('FONTNAME',  (4,i), (4,i), 'Helvetica-Bold'))
 
                    det_table.setStyle(TableStyle(style_cmds))
                    story.append(det_table)
 
                story.append(Spacer(1, 0.8*cm))
 
        # ── FINDINGS SUMMARY ─────────────────────────────────────
        story.append(Paragraph('● FINDINGS SUMMARY', section_style))
        story.append(HRFlowable(width='100%', thickness=1.5, color=MID_NAVY, spaceAfter=8))
 
        labels_found = {}
        for e in (case.evidence or []):
            for a in (e.annotations or []):
                labels_found[a.label] = labels_found.get(a.label, 0) + 1
 
        if labels_found:
            sum_rows = [['Object Type', 'Count', 'Significance']]
            sig_map = {
                'person': 'Primary subject — requires identity verification',
                'weapon': 'Critical evidence — handle with care',
                'knife': 'Critical evidence — potential murder weapon',
                'handgun': 'Critical evidence — ballistic analysis required',
                'bloodstain': 'Biological evidence — DNA analysis recommended',
                'footprint': 'Trace evidence — cast and photograph',
                'shell_casing': 'Ballistic evidence — firearms matching required',
                'body': 'Deceased individual — forensic autopsy required',
                'evidence_marker': 'Marked evidence — cross-reference case log',
            }
            for label, count in sorted(labels_found.items(), key=lambda x: -x[1]):
                sig = sig_map.get(label, 'Physical evidence — document and preserve')
                sum_rows.append([label.upper(), str(count), sig])
 
            sum_table = Table(sum_rows, colWidths=[4*cm, 2*cm, 11*cm])
            sum_table.setStyle(TableStyle([
                ('BACKGROUND',    (0,0), (-1,0), ACCENT_BLUE),
                ('TEXTCOLOR',     (0,0), (-1,0), WHITE),
                ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE',      (0,0), (-1,-1), 9),
                ('GRID',          (0,0), (-1,-1), 0.5, GRAY_BORDER),
                ('PADDING',       (0,0), (-1,-1), 7),
                ('ROWBACKGROUNDS',(0,1), (-1,-1), [WHITE, LIGHT_BG]),
                ('FONTNAME',      (0,1), (0,-1), 'Helvetica-Bold'),
                ('TEXTCOLOR',     (0,1), (0,-1), DARK_NAVY),
                ('ALIGN',         (1,0), (1,-1), 'CENTER'),
            ]))
            story.append(sum_table)
            story.append(Spacer(1, 0.4*cm))
 
        # Written summary paragraph
        summary_text = (
            f'This report was generated automatically by the CrimeScene.AI platform on '
            f'{now.strftime("%B %d, %Y at %H:%M")}. '
            f'Case <b>{case.case_number}</b> — <i>{case.title}</i> — '
            f'contains {total_evidence} evidence file(s) with a total of '
            f'<b>{total_annotations} detected objects</b> '
            f'({auto_count} via AI, {manual_count} manually annotated). '
        )
        if avg_conf:
            summary_text += f'Average AI confidence score: <b>{round(avg_conf*100)}%</b>. '
        summary_text += (
            'All findings are preliminary and subject to review by a qualified forensic investigator. '
            'This document is classified as confidential and should be handled in accordance with '
            'applicable law enforcement protocols.'
        )
        story.append(Paragraph(summary_text, body_style))
        story.append(Spacer(1, 0.6*cm))
 
        # ── FOOTER ──────────────────────────────────────────────
        story.append(HRFlowable(width='100%', thickness=0.5, color=GRAY_BORDER, spaceAfter=6))
        story.append(Paragraph(
            f'CrimeScene.AI · AI-Powered Forensic Analysis · Generated {now.strftime("%Y-%m-%d %H:%M:%S")} · CONFIDENTIAL',
            footer_style))
 
        doc.build(story)
        return {'total_objects': total_annotations}