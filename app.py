import os
import logging
from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
import os
from models import db, User
from routes.auth import auth_bp
from routes.tasks import tasks_bp
from routes.main import main_bp
from routes.api import api_bp

log_file = os.getenv("LOG_FILE", "/home/ec2-user/cloud-task/app.log")


load_dotenv() 


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
    database_url = os.getenv("DATABASE_URL", "sqlite:///task_manager.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {}
    if database_url.startswith("postgresql"):
        # Avoid long hangs when host/security groups/network are unreachable.
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "connect_args": {"connect_timeout": 5},
            "pool_pre_ping": True,
        }
    app.config["UPLOAD_FOLDER"] = "uploads"
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB
    app.config["AWS_S3_BUCKET"] = os.getenv("AWS_S3_BUCKET", "").strip()
    app.config["AWS_REGION"] = os.getenv("AWS_REGION", "ap-south-1").strip()
    app.config["AWS_ACCESS_KEY_ID"] = os.getenv("AWS_ACCESS_KEY_ID", "").strip()
    app.config["AWS_SECRET_ACCESS_KEY"] = os.getenv("AWS_SECRET_ACCESS_KEY", "").strip()
    app.config["AWS_S3_OBJECT_PREFIX"] = os.getenv("AWS_S3_OBJECT_PREFIX", "task_uploads").strip("/")
    app.config["AWS_S3_USE_ACL"] = os.getenv("AWS_S3_USE_ACL", "false").lower() == "true"
    app.config["AWS_S3_ACL"] = os.getenv("AWS_S3_ACL", "public-read").strip()
    app.config["AWS_S3_CUSTOM_DOMAIN"] = os.getenv("AWS_S3_CUSTOM_DOMAIN", "").strip()

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))



    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=3
    )
    file_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    file_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    logging.getLogger("werkzeug").addHandler(file_handler)

    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
