from datetime import datetime, time
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum, DateTime, Numeric, Text, Boolean,Time
from sqlalchemy.orm import relationship, backref
from OrderingFoodApp import db
from enum import Enum as enum
from flask_login import UserMixin
from sqlalchemy.ext.hybrid import hybrid_property


# ========== ENUMS ==========
class UserRole(enum):
    CUSTOMER = "customer"
    OWNER = "owner"
    ADMIN = "admin"


class OrderStatus(enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PaymentMethod(enum):
    CREDIT_CARD = "credit_card"
    MOMO = "momo"
    VNPAY = "vnpay"
    CASH_ON_DELIVERY = "cash_on_delivery"


class PaymentStatus(enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class DiscountType(enum):
    PERCENT = "percent"
    FIXED = "fixed"


class NotificationType(enum):
    ORDER_STATUS = "order_status"
    REVIEW_RESPONSE = "review_response"
    PROMO = "promos"
    OTHER = "other"

class Gender(enum):
    male   = "male"
    female = "female"

# ========== USER ==========
class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    # ─── MỚI ──────────────────────────────
    date_of_birth = Column(DateTime, nullable=True)
    gender = Column(Enum(Gender), nullable=True)
    phone = Column(String(20), nullable=True)
    # Quan hệ với Address
    addresses = relationship('Address', backref='user', lazy=True)

    @property
    def default_address(self):
        for a in self.addresses:
            if a.is_default:
                return a.address_line
        return None

    # ──────────────────────────────────────

    restaurants = relationship('Restaurant', backref='owner', lazy=True)
    carts = relationship('Cart', backref='customer', lazy=True)
    orders = relationship('Order', backref='customer', lazy=True)
    reviews = relationship('Review', backref='customer', lazy=True)
    review_responses = relationship('ReviewResponse', backref='owner', lazy=True)
    notifications = relationship('Notification', backref='user', lazy=True)

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True  # Flask-Login tự xử lý logged-in

    @property
    def is_anonymous(self):
        return False  # Không phải user anonymous

    def get_id(self):
        return str(self.id)

    # ==========================================================
    # THÊM CÁC PHƯƠNG THỨC PROPERTY
    # ==========================================================
    @property
    def is_admin(self):
        """Kiểm tra xem người dùng có vai trò ADMIN hay không."""
        return self.role == UserRole.ADMIN

    @property
    def is_owner(self):
        """Kiểm tra xem người dùng có vai trò OWNER hay không."""
        return self.role == UserRole.OWNER

    @property
    def is_customer(self):
        """Kiểm tra xem người dùng có vai trò CUSTOMER hay không."""
        return self.role == UserRole.CUSTOMER
    # ==========================================================

    def __repr__(self):
        return f'<User {self.email} - {self.role.value}>'


# ========== RESTAURANT ==========

class RestaurantApprovalStatus(enum):
    PENDING = "pending"      # Chờ duyệt
    APPROVED = "approved"    # Đã duyệt
    REJECTED = "rejected"    # Bị từ chối

class Restaurant(db.Model):
    __tablename__ = 'restaurants'
    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(150), nullable=False)
    description = Column(Text)
    address = Column(String(255))
    phone = Column(String(50))
    opening_time = Column(Time, nullable=False, default=time(8, 0))  # Mặc định 08:00
    closing_time = Column(Time, nullable=False, default=time(22, 0))  # Mặc định 22:00
    latitude = Column(Float)
    longitude = Column(Float)
    image_url = Column(String(255))  # Thêm dòng này
    created_at = Column(DateTime, default=datetime.utcnow)
    approval_status = Column(Enum(RestaurantApprovalStatus), nullable=False, default=RestaurantApprovalStatus.APPROVED)
    rejection_reason = Column(Text, nullable=True)  # Lưu lý do nếu bị từ chối


    menu_items = relationship('MenuItem', backref='restaurant', lazy=True)
    orders = relationship('Order', backref='restaurant', lazy=True)
    reviews = relationship('Review', backref='restaurant', lazy=True)


# ========== BRANCH ==========
class Branch(db.Model):
    __tablename__ = 'branches'
    id = Column(Integer, primary_key=True, autoincrement=True)
    restaurant_id = Column(Integer, ForeignKey('restaurants.id'), nullable=False)
    name = Column(String(150), nullable=False)
    address = Column(String(255), nullable=False)
    phone = Column(String(50))
    opening_time = Column(Time, nullable=False, default=time(8, 0))  # Mặc định 08:00
    closing_time = Column(Time, nullable=False, default=time(22, 0))  # Mặc định 22:00 # Đổi từ String sang Time
    status = Column(String(20), default='active')
    image_url = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    restaurant = relationship('Restaurant', backref=backref('branches', lazy=True))


# ========== MENU ==========
class MenuCategory(db.Model):
    __tablename__ = 'menu_categories'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    image_url = Column(String(255))  # Thêm trường này
    menu_items = relationship('MenuItem', backref='category', lazy=True)


class MenuItem(db.Model):
    __tablename__ = 'menu_items'
    id = Column(Integer, primary_key=True, autoincrement=True)
    restaurant_id = Column(Integer, ForeignKey('restaurants.id'), nullable=False)
    category_id = Column(Integer, ForeignKey('menu_categories.id'), nullable=False)
    name = Column(String(150), nullable=False)
    description = Column(Text)
    price = Column(Numeric(10, 2), nullable=False)
    image_url = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    cart_items = relationship('CartItem', backref='menu_item', lazy=True)
    order_items = relationship('OrderItem', backref='menu_item', lazy=True)
    is_active = Column(Boolean, default=True)


# ========== CART ==========
class Cart(db.Model):
    __tablename__ = 'carts'
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cart_items = relationship('CartItem', backref='cart', lazy=True)


class CartItem(db.Model):
    __tablename__ = 'cart_items'
    id = Column(Integer, primary_key=True, autoincrement=True)
    cart_id = Column(Integer, ForeignKey('carts.id'), nullable=False)
    menu_item_id = Column(Integer, ForeignKey('menu_items.id'), nullable=False)
    quantity = Column(Integer, nullable=False)


# ========== ORDER ==========
class Order(db.Model):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    restaurant_id = Column(Integer, ForeignKey('restaurants.id'), nullable=False)
    promo_code_id = Column(Integer, ForeignKey('promo_codes.id'))
    total_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    order_items = relationship('OrderItem', backref='order', lazy=True)
    payment = relationship('Payment', backref='order', uselist=False)


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    menu_item_id = Column(Integer, ForeignKey('menu_items.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)  # giá tại thời điểm đặt


# ========== PAYMENT ==========
class Payment(db.Model):
    __tablename__ = 'payments'
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    method = Column(Enum(PaymentMethod), nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    paid_at = Column(DateTime)


# ========== PROMO ==========
class PromoCode(db.Model):
    __tablename__ = 'promo_codes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    discount_type = Column(Enum(DiscountType), nullable=False)
    discount_value = Column(Numeric(10, 2), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    usage_limit = Column(Integer)
    image_url = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    restaurant_id = Column(Integer, ForeignKey('restaurants.id'), nullable=True)  # null = mã dùng chung toàn hệ thống
    restaurant = relationship('Restaurant', backref='promo_codes')
    orders = relationship('Order', backref='promo_code', lazy=True)


# ========== REVIEW ==========
class Review(db.Model):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    restaurant_id = Column(Integer, ForeignKey('restaurants.id'), nullable=False)
    order_id = Column(Integer, ForeignKey('orders.id'))
    rating = Column(Integer, nullable=False)  # customer–5
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    responses = relationship('ReviewResponse', backref='review', lazy=True)


class ReviewResponse(db.Model):
    __tablename__ = 'review_responses'
    id = Column(Integer, primary_key=True, autoincrement=True)
    review_id = Column(Integer, ForeignKey('reviews.id'), nullable=False)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    response_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ========== NOTIFICATION ==========
class Notification(db.Model):
    __tablename__ = 'notifications'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    order_id = Column(Integer, ForeignKey('orders.id'))
    type = Column(Enum(NotificationType), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Address(db.Model):
    __tablename__ = 'addresses'
    id            = Column(Integer, primary_key=True, autoincrement=True)
    user_id       = Column(Integer, ForeignKey('users.id'), nullable=False)
    address_line  = Column(String(255), nullable=False)
    is_default    = Column(Boolean, default=False)
    created_at    = Column(DateTime, default=datetime.utcnow)
