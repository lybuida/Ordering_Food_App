import pytest
from OrderingFoodApp import db
from OrderingFoodApp.dao import user_dao
from OrderingFoodApp.models import User, UserRole


def test_add_user_success(app):
    with app.app_context():
        user = user_dao.add_user("Alice", "alice@example.com", "secret", "customer")
        assert user is not None
        assert user.id is not None
        assert user.role == UserRole.CUSTOMER


def test_add_user_invalid_role(app):
    with app.app_context():
        user = user_dao.add_user("Bob", "bob@example.com", "secret", "invalid_role")
        assert user is not None
        assert user.role == UserRole.CUSTOMER  # Mặc định


def test_add_user_duplicate_email(app):
    with app.app_context():
        user1 = user_dao.add_user("Carol", "carol@example.com", "123", "admin")
        user2 = user_dao.add_user("Carol2", "carol@example.com", "456", "admin")
        assert user1 is not None
        assert user2 is None


def test_get_user_by_email_and_id(app):
    with app.app_context():
        user = user_dao.add_user("Dan", "dan@example.com", "123", "owner")
        by_email = user_dao.get_user_by_email("dan@example.com")
        by_id = user_dao.get_user_by_id(user.id)

        assert by_email is not None
        assert by_email.id == user.id
        assert by_id.email == "dan@example.com"


def test_update_user_success(app):
    with app.app_context():
        user = user_dao.add_user("Eve", "eve@example.com", "pass", "owner")
        success = user_dao.update_user(user.id, name="Eve Updated", email="eve2@example.com", role="admin")
        assert success

        updated = user_dao.get_user_by_id(user.id)
        assert updated.name == "Eve Updated"
        assert updated.email == "eve2@example.com"
        assert updated.role == UserRole.ADMIN


def test_update_user_invalid_id(app):
    with app.app_context():
        success = user_dao.update_user(9999, name="Should Fail")
        assert success is False


def test_delete_user_success(app):
    with app.app_context():
        user = user_dao.add_user("Frank", "frank@example.com", "123", "customer")
        deleted = user_dao.delete_user(user.id)
        assert deleted
        assert user_dao.get_user_by_id(user.id) is None


def test_delete_user_invalid_id(app):
    with app.app_context():
        deleted = user_dao.delete_user(123456)
        assert deleted is False


def test_get_all_users_basic(app):
    with app.app_context():
        user_dao.add_user("Gina", "gina@example.com", "111", "customer")
        user_dao.add_user("Hank", "hank@example.com", "222", "admin")
        result = user_dao.get_all_users(page=1, page_size=10)

        assert result.total >= 2
        emails = [user.email for user in result.items]
        assert "gina@example.com" in emails


def test_get_all_users_search_and_role(app):
    with app.app_context():
        user_dao.add_user("Isaac", "isaac@example.com", "pass", "owner")
        result = user_dao.get_all_users(query="isaac", role="owner")
        assert result.total >= 1
        assert result.items[0].email == "isaac@example.com"


def test_count_users_by_role(app):
    with app.app_context():
        user_dao.add_user("Jack", "jack@example.com", "1", "admin")
        user_dao.add_user("Jill", "jill@example.com", "2", "admin")
        user_dao.add_user("Jen", "jen@example.com", "3", "customer")

        total = user_dao.count_users_by_role()
        admin_count = user_dao.count_users_by_role(UserRole.ADMIN)

        assert total >= 3
        assert admin_count >= 2
