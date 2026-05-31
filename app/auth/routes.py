from flask import render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User
from app.auth import auth_bp


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('auth.dashboard'))
        else:
            flash('Wrong username or password.', 'error')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth_bp.route('/dashboard')
@login_required
def dashboard():
    from app.models import Case, EvidenceItem, Annotation

    total_cases = Case.query.filter_by(created_by=current_user.id).count()
    open_cases = Case.query.filter_by(created_by=current_user.id, status='open').count()
    total_evidence = EvidenceItem.query.join(Case).filter(Case.created_by == current_user.id).count()
    total_detections = Annotation.query.filter_by(source='auto').count()
    recent_cases = Case.query.filter_by(created_by=current_user.id).order_by(Case.created_at.desc()).limit(5).all()

    stats = {
        'total_cases': total_cases,
        'open_cases': open_cases,
        'total_evidence': total_evidence,
        'total_detections': total_detections
    }
    return render_template('auth/dashboard.html', stats=stats, recent_cases=recent_cases)