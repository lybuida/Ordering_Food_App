# tests/conftest.py

import os
import pytest
from flask import Flask
from OrderingFoodApp import init_app, db

@pytest.fixture(scope='session')
def app():
    # Cho biết ta đang ở môi trường test
    os.environ['FLASK_ENV'] = 'testing'

    # Tạo app từ init_app
    app: Flask = init_app()
    app.config.update({
        'TESTING': True,
        # Chỉ điểm tới database test (tạo trước bằng Workbench)
        # 'SQLALCHEMY_DATABASE_URI': 'mysql+pymysql://root:password@127.0.0.1:3306/test_db',
        'SQLALCHEMY_DATABASE_URI': 'mysql+pymysql://root:26032004@localhost/test_db',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret',
    })

    # Tạo toàn bộ bảng
    with app.app_context():
        db.create_all()

    yield app

    # Sau cùng drop bảng
    with app.app_context():
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture(autouse=True)
def clean_db(app):
    # Trước mỗi test truncate hết các bảng
    with app.app_context():
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()
