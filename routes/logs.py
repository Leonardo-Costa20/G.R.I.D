import csv
import io
from datetime import datetime
from flask import render_template, request, jsonify, Response, session, redirect, url_for
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from core import supabase


def logs_page():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('logs.html', username=session.get('username'), role=session.get('role'))


def api_logs():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    sensor_filter = request.args.get('sensor', '', type=str)
    start_date = request.args.get('start', '', type=str)
    end_date = request.args.get('end', '', type=str)

    if not supabase:
        return jsonify({'error': 'Database unavailable'}), 503

    try:
        query = supabase.table('logs_operacao').select('*', count='exact')
        if sensor_filter:
            query = query.eq('origem', sensor_filter)
        else:
            query = query.neq('origem', 'mapa')
        if start_date:
            query = query.gte('data_hora', start_date + 'T00:00:00')
        if end_date:
            query = query.lte('data_hora', end_date + 'T23:59:59')
        query = query.order('data_hora', desc=True)
        offset = (page - 1) * per_page
        res = query.range(offset, offset + per_page - 1).execute()
        total = res.count if res.count is not None else len(res.data)
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1
        return jsonify({
            'logs': res.data,
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def api_logs_sensors():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    if not supabase:
        return jsonify({'sensors': []}), 503
    try:
        res = supabase.table('logs_operacao').select('origem').execute()
        sensors = sorted({item['origem'] for item in res.data if item.get('origem') and item['origem'] != 'mapa'})
        return jsonify({'sensors': sensors})
    except Exception:
        return jsonify({'sensors': []}), 500


def api_logs_export():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401

    sensor_filter = request.args.get('sensor', '', type=str)
    start_date = request.args.get('start', '', type=str)
    end_date = request.args.get('end', '', type=str)

    if not supabase:
        return jsonify({'error': 'Database unavailable'}), 503

    try:
        query = supabase.table('logs_operacao').select('*').order('data_hora', desc=True)
        if sensor_filter:
            query = query.eq('origem', sensor_filter)
        else:
            query = query.neq('origem', 'mapa')
        if start_date:
            query = query.gte('data_hora', start_date + 'T00:00:00')
        if end_date:
            query = query.lte('data_hora', end_date + 'T23:59:59')
        res = query.limit(1000).execute()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Sensor', 'Valor', 'Hora'])
        for log in res.data:
            writer.writerow([log.get('origem', 'N/A'), log.get('valor', ''), log.get('data_hora', '')])
        output.seek(0)
        filename = f"GRID_Logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return Response(
            output,
            mimetype='text/csv; charset=utf-8',
            headers={
                'Content-Disposition': f'attachment; filename={filename}',
                'Content-Type': 'text/csv; charset=utf-8'
            }
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def api_logs_export_pdf():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401

    sensor_filter = request.args.get('sensor', '', type=str)
    start_date = request.args.get('start', '', type=str)
    end_date = request.args.get('end', '', type=str)

    if not supabase:
        return jsonify({'error': 'Database unavailable'}), 503

    try:
        query = supabase.table('logs_operacao').select('*').order('data_hora', desc=True)
        if sensor_filter:
            query = query.eq('origem', sensor_filter)
        else:
            query = query.neq('origem', 'mapa')
        if start_date:
            query = query.gte('data_hora', start_date + 'T00:00:00')
        if end_date:
            query = query.lte('data_hora', end_date + 'T23:59:59')
        res = query.limit(500).execute()

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        elements = []
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#3ecf8e'),
            spaceAfter=20,
            alignment=1
        )
        elements.append(Paragraph('G.R.I.D OS - MISSION LOGS', title_style))
        elements.append(Spacer(1, 0.3*cm))
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.grey,
            spaceAfter=5
        )
        now = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        elements.append(Paragraph(f"<b>Operador:</b> {session.get('username', 'N/A')}", info_style))
        elements.append(Paragraph(f"<b>Gerado em:</b> {now}", info_style))
        elements.append(Paragraph(f"<b>Total de registos:</b> {len(res.data)}", info_style))
        elements.append(Spacer(1, 0.5*cm))

        table_data = [['Sensor', 'Valor', 'Hora']]
        unidades = {
            'MQ2': 'ppm',
            'Distancia': 'cm',
            'Acel_X': 'm/s²', 'Acel_Y': 'm/s²', 'Acel_Z': 'm/s²',
            'Gyro_X': '°/s', 'Gyro_Y': '°/s', 'Gyro_Z': '°/s',
            'Temperatura': '°C',
            'Pressao': 'hPa'
        }
        for log in res.data:
            origem = log.get('origem', 'N/A')
            valor = log.get('valor', '')
            unidade = unidades.get(origem, '')
            hora = log.get('data_hora', '')[:16]
            valor_str = f"{valor} {unidade}" if unidade else str(valor)
            table_data.append([origem, valor_str, hora])

        table = Table(table_data, colWidths=[6*cm, 4*cm, 5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#161b22')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#3ecf8e')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#0d1117')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.white),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#30363d')),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#3ecf8e')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#0d1117'), colors.HexColor('#161b22')]),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 1*cm))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=1
        )
        elements.append(Paragraph('G.R.I.D OS | Ground Recon & Intelligent Detection', footer_style))
        doc.build(elements)
        buffer.seek(0)
        filename = f"GRID_Mission_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        return Response(
            buffer,
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename={filename}',
                'Content-Type': 'application/pdf'
            }
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500
