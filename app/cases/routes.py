import os, uuid
from flask import render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import Case, EvidenceItem
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
    cases = Case.query.filter_by(created_by=current_user.id).all()
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
        flash('No file selected', 'error')
        return redirect(url_for('cases.view_case', case_id=case_id))

    file = request.files['file']
    if not allowed_file(file.filename):
        flash('Only JPG, PNG, and MP4 files allowed', 'error')
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