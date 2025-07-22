# order_owner.py
from OrderingFoodApp.models import Order, OrderItem, User, Restaurant, db, Notification, NotificationType, OrderStatus, \
    RestaurantApprovalStatus
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError


class OrderDAO:
    @staticmethod
    def get_orders_by_owner(owner_id, status=None, start_date=None, end_date=None, branch_id=None, page=1, per_page=10):
        query = Order.query.join(Restaurant).filter(
            Restaurant.owner_id == owner_id,
            Restaurant.approval_status == RestaurantApprovalStatus.APPROVED
        )

        # Lọc theo trạng thái
        if status:
            query = query.filter(Order.status == status)

        # Lọc theo ngày
        if start_date and end_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            # end_date = datetime.strptime(end_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(and_(Order.created_at >= start_date,
                                      Order.created_at <= end_date))

        # Lọc theo chi nhánh
        if branch_id:
            query = query.filter(Order.restaurant_id == branch_id)

        # Phân trang
        pagination = query.order_by(Order.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

        orders = pagination.items
        total = pagination.total

        # Thêm thông tin khách hàng và số món
        result = []
        for order in orders:
            customer = User.query.get(order.customer_id)
            item_count = OrderItem.query.filter_by(order_id=order.id).count()

            result.append({
                'id': order.id,
                'code': f"#{order.id:06d}",
                'created_at': order.created_at.strftime('%H:%M %d/%m/%Y'),
                'customer_name': customer.name,
                'item_count': item_count,
                'total_amount': order.total_amount,
                'status': order.status.value,
                'status_display': OrderDAO.get_status_display(order.status),
                'restaurant_id': order.restaurant_id
            })

        return {
            'orders': result,
            'total': total,
            'pages': pagination.pages,
            'current_page': page
        }

    @staticmethod
    def get_status_display(status):
        status_map = {
            'pending': 'Chờ xác nhận',
            'confirmed': 'Đã xác nhận',
            'preparing': 'Đang chuẩn bị',
            'delivered': 'Đang giao',
            'cancelled': 'Đã huỷ',
            'completed': 'Hoàn thành'
        }
        return status_map.get(status.value, status.value)

    @staticmethod
    def update_order_status(order_id, status):
        order = Order.query.get(order_id)
        if not order:
            return False

        # Kiểm tra luồng chuyển trạng thái hợp lệ
        valid_transitions = {
            'pending': ['confirmed', 'cancelled'],
            'confirmed': ['preparing', 'cancelled'],
            'preparing': ['delivered'],
            'delivered': ['completed']
        }

        current_status = order.status.value
        if status not in valid_transitions.get(current_status, []):
            return False

        order.status = status
        db.session.commit()

        # Tạo thông báo cho khách hàng
        status_messages = {
            'confirmed': f"Đơn hàng #{order.id} đã được xác nhận",
            'preparing': f"Đơn hàng #{order.id} đang được chuẩn bị",
            'delivered': f"Đơn hàng #{order.id} đang trên đường giao đến bạn",
            'completed': f"Đơn hàng #{order.id} đã hoàn thành",
            'cancelled': f"Đơn hàng #{order.id} đã bị huỷ"
        }

        if status in status_messages:
            notification = Notification(
                user_id=order.customer_id,
                type=NotificationType.ORDER_STATUS,
                message=status_messages[status],
                is_read=False
            )
            db.session.add(notification)
            db.session.commit()

        return True

    @staticmethod
    def get_order_details(order_id):
        order = Order.query.get(order_id)
        if not order:
            return None

        customer = User.query.get(order.customer_id)
        restaurant = Restaurant.query.get(order.restaurant_id)
        items = OrderItem.query.filter_by(order_id=order.id).all()

        order_details = {
            'id': order.id,
            'code': f"#{order.id:06d}",
            'created_at': order.created_at.strftime('%H:%M %d/%m/%Y'),
            'customer': {
                'name': customer.name,
                'email': customer.email
            },
            'restaurant': {
                'id': restaurant.id,
                'name': restaurant.name,
                'address': restaurant.address,
                'phone': restaurant.phone
            },
            'restaurant_id': restaurant.id,
            'status': order.status.value,
            'status_display': OrderDAO.get_status_display(order.status),
            'total_amount': order.total_amount,
            'items': []
        }

        for item in items:
            menu_item = item.menu_item
            order_details['items'].append({
                'name': menu_item.name,
                'quantity': item.quantity,
                'price': item.price,
                'total': item.quantity * item.price
            })

        return order_details

def count_orders_by_status(status=None):
    """
    Đếm tổng số đơn hàng hoặc số đơn hàng theo trạng thái cụ thể.
    Args:
        status (OrderStatus, optional): Trạng thái cần đếm. Nếu None, đếm tất cả đơn hàng.
    Returns:
        int: Tổng số đơn hàng.
    """
    try:
        query = db.session.query(Order)
        if status:
            query = query.filter_by(status=status)
        return query.count()
    except SQLAlchemyError as e:
        print(f"Error counting orders by status: {e}")
        return 0

def get_total_revenue(status=OrderStatus.COMPLETED):
    """
    Tính tổng doanh thu từ các đơn hàng (mặc định là đơn hàng đã giao thành công).
    Args:
        status (OrderStatus): Trạng thái đơn hàng để tính doanh thu.
    Returns:
        float: Tổng doanh thu.
    """
    try:
        # Sum total_amount from orders with the specified status
        total_revenue = db.session.query(func.sum(Order.total_amount))\
                            .filter(Order.status == status)\
                            .scalar()
        return float(total_revenue) if total_revenue else 0.0
    except SQLAlchemyError as e:
        print(f"Error calculating total revenue: {e}")
        return 0.0
