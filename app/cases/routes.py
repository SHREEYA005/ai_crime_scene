import os
import uuid
from flask import render_template, redirect, url_for, request, flash, current_app, jsonify, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import Case, EvidenceItem, Annotation
from app.cases import cases_bp
from datetime import date

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'mp4'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_case_number():
    today = date.today()
    return f'CR-{today.year}-{str(uuid.uuid4())[:6].upper()}'


@cases_bp.route('/')
@login_required
def list_cases():
    cases = Case.query.filter_by(created_by=current_user.id).order_by(Case.created_at.desc()).all()
    return render_template('cases/list.html', cases=cases)


@cases_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_case():
    if request.method == 'POST':
        case = Case(
            case_number=generate_case_number(),
            title=request.form.get('title'),
            location=request.form.get('location'),
            created_by=current_user.id
        )
        db.session.add(case)
        db.session.commit()
        flash(f'Case {case.case_number} created!', 'success')
        return redirect(url_for('cases.view_case', case_id=case.id))
    return render_template('cases/new.html')


@cases_bp.route('/<int:case_id>')
@login_required
def view_case(case_id):
    case = Case.query.get_or_404(case_id)
    return render_template('cases/view.html', case=case)


@cases_bp.route('/<int:case_id>/upload', methods=['POST'])
@login_required
def upload_evidence(case_id):
    case = Case.query.get_or_404(case_id)

    if 'file' not in request.files:
        flash('No file selected.', 'danger')
        return redirect(url_for('cases.view_case', case_id=case_id))

    file = request.files['file']
    if not allowed_file(file.filename):
        flash('Only JPG, PNG, and MP4 files are allowed.', 'danger')
        return redirect(url_for('cases.view_case', case_id=case_id))

    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(case_id))
    os.makedirs(upload_dir, exist_ok=True)

    safe_name = secure_filename(file.filename)
    ext = safe_name.rsplit('.', 1)[1].lower()
    unique_name = f'{uuid.uuid4()}.{ext}'
    file_path = os.path.join(upload_dir, unique_name)
    file.save(file_path)

    evidence = EvidenceItem(
        case_id=case_id,
        file_path=file_path,
        original_filename=safe_name,
        file_type=ext,
        uploaded_by=current_user.id
    )
    db.session.add(evidence)
    db.session.commit()

    flash(f'{safe_name} uploaded successfully!', 'success')
    return redirect(url_for('cases.view_case', case_id=case_id))


@cases_bp.route('/evidence/<int:evidence_id>/image')
@login_required
def serve_image(evidence_id):
    evidence = EvidenceItem.query.get_or_404(evidence_id)
    return send_file(evidence.file_path)


@cases_bp.route('/evidence/<int:evidence_id>/detect', methods=['POST'])
@login_required
def run_detection(evidence_id):
    evidence = EvidenceItem.query.get_or_404(evidence_id)

    if evidence.file_type not in ['jpg', 'jpeg', 'png']:
        flash('Detection only works on image files.', 'danger')
        return redirect(url_for('cases.view_case', case_id=evidence.case_id))

    Annotation.query.filter_by(evidence_id=evidence_id, source='auto').delete()

    try:
        from app.detection.yolo_detector import CrimeSceneDetector
        detector = CrimeSceneDetector.get_instance()
        detections = detector.detect(evidence.file_path)

        for d in detections:
            annotation = Annotation(
                evidence_id=evidence_id,
                label=d['label'],
                x=d['x'], y=d['y'],
                width=d['width'], height=d['height'],
                confidence=d['confidence'],
                source='auto',
                annotated_by=current_user.id
            )
            db.session.add(annotation)

        evidence.status = 'detected'
        db.session.commit()
        flash(f'Detection complete! Found {len(detections)} objects.', 'success')
    except Exception as e:
        flash(f'Detection failed: {str(e)}', 'danger')

    return redirect(url_for('cases.view_case', case_id=evidence.case_id))


@cases_bp.route('/evidence/<int:evidence_id>/annotate')
@login_required
def annotate(evidence_id):
    evidence = EvidenceItem.query.get_or_404(evidence_id)
    return render_template('cases/annotate.html', evidence=evidence)


@cases_bp.route('/evidence/<int:evidence_id>/annotations')
@login_required
def get_annotations(evidence_id):
    annotations = Annotation.query.filter_by(evidence_id=evidence_id).all()
    data = [{
        'id': a.id, 'label': a.label,
        'x': a.x, 'y': a.y, 'width': a.width, 'height': a.height,
        'confidence': a.confidence, 'source': a.source
    } for a in annotations]
    return jsonify({'annotations': data, 'count': len(data)})


@cases_bp.route('/evidence/<int:evidence_id>/annotations', methods=['POST'])
@login_required
def save_annotations(evidence_id):
    evidence = EvidenceItem.query.get_or_404(evidence_id)
    data = request.get_json()

    if not data or 'annotations' not in data:
        return jsonify({'success': False, 'error': 'No annotation data'}), 400

    Annotation.query.filter_by(evidence_id=evidence_id).delete()

    for ann in data['annotations']:
        annotation = Annotation(
            evidence_id=evidence_id,
            label=ann['label'],
            x=ann['x'], y=ann['y'],
            width=ann['width'], height=ann['height'],
            confidence=ann.get('confidence'),
            source=ann.get('source', 'manual'),
            annotated_by=current_user.id
        )
        db.session.add(annotation)

    evidence.status = 'annotated'
    db.session.commit()
    return jsonify({'success': True, 'saved': len(data['annotations'])})


@cases_bp.route('/<int:case_id>/export/scene', methods=['POST'])
@login_required
def export_scene(case_id):
    case = Case.query.get_or_404(case_id)
    output_path = os.path.join('exports', f'scene_{case.case_number}.json')
    os.makedirs('exports', exist_ok=True)

    try:
        from app.detection.scene_builder import build_scene_json
        scene = build_scene_json(case, output_path)
        flash(f'Scene exported! {scene["total_objects"]} objects included.', 'success')
    except Exception as e:
        flash(f'Export failed: {str(e)}', 'danger')

    return redirect(url_for('cases.view_case', case_id=case_id))


@cases_bp.route('/<int:case_id>/export/scene/download')
@login_required
def download_scene(case_id):
    case = Case.query.get_or_404(case_id)
    path = os.path.join('exports', f'scene_{case.case_number}.json')
    if not os.path.exists(path):
        flash('Generate the scene first.', 'danger')
        return redirect(url_for('cases.view_case', case_id=case_id))
    return send_file(path, as_attachment=True)


@cases_bp.route('/<int:case_id>/export/pdf', methods=['POST'])
@login_required
def export_pdf(case_id):
    case = Case.query.get_or_404(case_id)
    output_path = os.path.join('exports', f'report_{case.case_number}.pdf')
    os.makedirs('exports', exist_ok=True)

    try:
        from app.reports.pdf_generator import CaseReportGenerator
        CaseReportGenerator().generate(case, output_path)
        flash('PDF report generated!', 'success')
    except Exception as e:
        flash(f'PDF generation failed: {str(e)}', 'danger')

    return redirect(url_for('cases.view_case', case_id=case_id))


@cases_bp.route('/<int:case_id>/export/pdf/download')
@login_required
def download_pdf(case_id):
    case = Case.query.get_or_404(case_id)
    path = os.path.join('exports', f'report_{case.case_number}.pdf')
    if not os.path.exists(path):
        flash('Generate the report first.', 'danger')
        return redirect(url_for('cases.view_case', case_id=case_id))
    return send_file(path, as_attachment=True)
