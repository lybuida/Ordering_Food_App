import pytest
from OrderingFoodApp.dao import restaurant_dao, user_dao
from OrderingFoodApp.models import UserRole, RestaurantApprovalStatus, Restaurant


def create_owner(name="owner1", email="owner1@example.com"):
    return user_dao.add_user(name, email, "123456", UserRole.OWNER)


def test_add_restaurant_success(app):
    with app.app_context():
        owner = create_owner()
        restaurant = restaurant_dao.add_restaurant(
            name="Testaurant",
            description="Good food",
            address="123 Street",
            phone="123456789",
            owner_id=owner.id,
            image_url="http://image.com/1.png",
            latitude=10.0,
            longitude=106.0
        )
        assert restaurant is not None
        assert restaurant.name == "Testaurant"
        assert restaurant.owner_id == owner.id


def test_get_restaurant_by_id(app):
    with app.app_context():
        owner = create_owner()
        restaurant = restaurant_dao.add_restaurant("R1", "desc", "addr", "0123", owner.id)
        fetched = restaurant_dao.get_restaurant_by_id(restaurant.id)
        assert fetched is not None
        assert fetched.name == "R1"


def test_update_restaurant_success(app):
    with app.app_context():
        owner = create_owner()
        restaurant = restaurant_dao.add_restaurant("OldName", "desc", "addr", "0123", owner.id)
        updated = restaurant_dao.update_restaurant(restaurant.id, name="NewName", address="New Addr")
        assert updated is True

        updated_restaurant = restaurant_dao.get_restaurant_by_id(restaurant.id)
        assert updated_restaurant.name == "NewName"
        assert updated_restaurant.address == "New Addr"


def test_delete_restaurant_success(app):
    with app.app_context():
        owner = create_owner()
        restaurant = restaurant_dao.add_restaurant("R2", "desc", "addr", "0123", owner.id)
        result = restaurant_dao.delete_restaurant(restaurant.id)
        assert result is True

        deleted = restaurant_dao.get_restaurant_by_id(restaurant.id)
        assert deleted is None


def test_count_all_restaurants(app):
    with app.app_context():
        owner = create_owner()
        restaurant_dao.add_restaurant("A", "", "", "", owner.id)
        restaurant_dao.add_restaurant("B", "", "", "", owner.id)
        count = restaurant_dao.count_all_restaurants()
        assert count >= 2


def test_get_all_restaurants_with_filter(app):
    with app.app_context():
        owner = create_owner()
        restaurant_dao.add_restaurant("FilterName", "desc", "addr", "0123", owner.id)
        result = restaurant_dao.get_all_restaurants(query="filter", only_approved=False)
        assert result.total >= 1


def test_get_pending_restaurants(app):
    with app.app_context():
        owner = create_owner()
        r = restaurant_dao.add_restaurant("PendingR", "desc", "addr", "0123", owner.id)
        # Trạng thái mặc định là PENDING
        pending_list = restaurant_dao.get_pending_restaurants()
        assert any(res.id == r.id for res in pending_list)


def test_approve_restaurant(app):
    with app.app_context():
        owner = create_owner()
        r = restaurant_dao.add_restaurant("ToApprove", "desc", "addr", "0123", owner.id)
        success = restaurant_dao.approve_restaurant(r.id)
        assert success is True

        updated = restaurant_dao.get_restaurant_by_id(r.id)
        assert updated.approval_status == RestaurantApprovalStatus.APPROVED


def test_reject_restaurant(app):
    with app.app_context():
        owner = create_owner()
        r = restaurant_dao.add_restaurant("ToReject", "desc", "addr", "0123", owner.id)
        success = restaurant_dao.reject_restaurant(r.id, "Sai thông tin")
        assert success is True

        updated = restaurant_dao.get_restaurant_by_id(r.id)
        assert updated.approval_status == RestaurantApprovalStatus.REJECTED
        assert updated.rejection_reason == "Sai thông tin"
