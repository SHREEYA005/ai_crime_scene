from app import create_app, db
from app.models import User

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', role='admin')
            admin.set_password('admin123')

            investigator = User(username='detective', role='investigator')
            investigator.set_password('detective123')

            analyst = User(username='analyst', role='analyst')
            analyst.set_password('analyst123')

            db.session.add_all([admin, investigator, analyst])
            db.session.commit()
            print('Test users created!')

    app.run(debug=True, port=5000)
