from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from dotenv import load_dotenv
import os

# Load biến môi trường từ .env
load_dotenv()

# Khởi tạo extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


def init_app():
    """
    Khởi tạo Flask App, tích hợp các extension
    """
    app = Flask(__name__)

    # ====== CONFIGURATION ======
    app.config['SECRET_KEY'] = 'sieu-bi-mat-123'
    #app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:askme@localhost/db_orderingfood?charset=utf8mb4'
    #app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:26032004@localhost/db_orderingfood?charset=utf8mb4'
    app.config[
        "SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:01676831139Chi%40@localhost:3306/db_orderingfood?charset=utf8mb4"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ====== INITIALIZE EXTENSIONS ======
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # ====== FLASK-LOGIN CONFIG ======
    login_manager.login_view = 'auth.login'  # route login nếu chưa đăng nhập

    from OrderingFoodApp.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from OrderingFoodApp.models import UserRole
    app.jinja_env.globals['UserRole'] = UserRole

    login_manager.login_message_category = 'info'

    # ====== IMPORT MODELS ======
    from OrderingFoodApp import models  # Import models để Flask-Migrate nhận diện

    # ====== REGISTER BLUEPRINTS ======
    from OrderingFoodApp.routes.auth import auth_bp
    from OrderingFoodApp.routes.customer import customer_bp
    from OrderingFoodApp.routes.owner import owner_bp
    from OrderingFoodApp.routes.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(customer_bp, url_prefix='/customer')
    app.register_blueprint(owner_bp, url_prefix='/owner')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from OrderingFoodApp.routes.home import home_bp
    app.register_blueprint(home_bp)

    return app
