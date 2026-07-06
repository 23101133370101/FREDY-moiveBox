import os

from flask import Flask, render_template
from flask_wtf import CSRFProtect

from config import Config
from database import db, migrate, login_manager


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["POSTER_FOLDER"], exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    CSRFProtect(app)

    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.movies import movies_bp
    from routes.users import users_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(movies_bp)
    app.register_blueprint(users_bp)

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404

    @app.cli.command("create-admin")
    def create_admin():
        """Create the initial admin user from ADMIN_USERNAME / ADMIN_EMAIL / ADMIN_PASSWORD in .env"""
        from models.user import User

        username = app.config["ADMIN_USERNAME"]
        email = app.config["ADMIN_EMAIL"]
        password = app.config["ADMIN_PASSWORD"]

        if User.query.filter_by(username=username).first():
            print(f"Admin user {username} already exists.")
            return

        admin = User(username=username, email=email, is_admin=True)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print(f"Admin user created: {username}")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5002)
