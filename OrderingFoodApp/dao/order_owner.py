# order_owner.py
from OrderingFoodApp.models import Order, OrderItem, User, Restaurant, db, Notification, NotificationType, OrderStatus, \
    RestaurantApprovalStatus, MenuItem
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
            query = query.filter(and_(Order.updated_at >= start_date,
                                      Order.updated_at <= end_date))

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
                'created_at': order.updated_at.strftime('%H:%M %d/%m/%Y'),
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
    def update_order_status(order_id, status, rj_reason=None):
        order = Order.query.get(order_id)
        if not order:
            return False

        # Kiểm tra luồng chuyển trạng thái hợp lệ
        valid_transitions = {
            'pending': ['confirmed', 'cancelled'],
            'confirmed': ['preparing'],
            'preparing': ['delivered'],
            'delivered': ['completed']
        }

        current_status = order.status.value
        if status not in valid_transitions.get(current_status, []):
            return False

        order.status = status
        if status == 'cancelled' and rj_reason:
            order.rj_reason = rj_reason
        db.session.commit()

        # Tạo thông báo cho khách hàng
        status_messages = {
            'confirmed': f"Đơn hàng #{order.id} đã được xác nhận",
            'preparing': f"Đơn hàng #{order.id} đang được chuẩn bị",
            'delivered': f"Đơn hàng #{order.id} đang trên đường giao đến bạn",
            'completed': f"Đơn hàng #{order.id} đã hoàn thành",
            'cancelled': f"Đơn hàng #{order.id} đã bị huỷ. Lý do: {rj_reason or 'Không có lý do'}"
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

    ###########3#####Doanh thu###
    @staticmethod
    def get_advanced_statistics(owner_id, restaurant_id=None, start_date=None, end_date=None):
        """Lấy thống kê nâng cao cho chủ nhà hàng (CHỈ tính doanh thu từ đơn COMPLETED)"""
        # Base query để lấy thống kê theo trạng thái
        query = db.session.query(
            Order.status,
            func.count(Order.id).label('count'),
            func.sum(Order.total_amount).label('total_amount')
        ).join(Restaurant).filter(
            Restaurant.owner_id == owner_id,
            Restaurant.approval_status == RestaurantApprovalStatus.APPROVED
        )

        # Filter by restaurant if specified
        if restaurant_id:
            query = query.filter(Order.restaurant_id == restaurant_id)

        # Filter by date range if specified
        if start_date and end_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(and_(
                Order.updated_at >= start_date,
                Order.updated_at <= end_date
            ))

        # Group by status
        results = query.group_by(Order.status).all()

        # Tính tổng số đơn hàng (tất cả trạng thái)
        total_orders = sum(r.count for r in results) if results else 0

        # Tính doanh thu
        completed_revenue_query = db.session.query(func.sum(Order.total_amount)).join(Restaurant).filter(
            Restaurant.owner_id == owner_id,
            Restaurant.approval_status == RestaurantApprovalStatus.APPROVED,
            Order.status == OrderStatus.COMPLETED  # <-- Chỉ lấy đơn hoàn thành
        )

        # Áp dụng các filter tương tự (nhà hàng/ngày tháng)
        if restaurant_id:
            completed_revenue_query = completed_revenue_query.filter(Order.restaurant_id == restaurant_id)
        if start_date and end_date:
            completed_revenue_query = completed_revenue_query.filter(
                and_(Order.updated_at >= start_date, Order.updated_at <= end_date)
            )

        total_revenue = completed_revenue_query.scalar() or 0  # Lấy giá trị tổng (mặc định 0 nếu None)

        # Format kết quả
        statistics = {
            'by_status': [
                {
                    'status': r.status.value,
                    'status_display': OrderDAO.get_status_display(r.status),
                    'count': r.count,
                    'percentage': round((float(r.count) / total_orders * 100), 2) if total_orders else 0,
                    'amount': float(r.total_amount or 0)
                }
                for r in results
            ],
            'total_orders': total_orders,
            'total_revenue': float(total_revenue),  # Doanh thu CHỈ từ đơn COMPLETED
            'success_rate': round(
                (sum(float(r.count) for r in results if r.status == OrderStatus.COMPLETED) / total_orders * 100),
                2
            ) if total_orders else 0,
            'cancellation_rate': round(
                (sum(float(r.count) for r in results if r.status == OrderStatus.CANCELLED) / total_orders * 100),
                2
            ) if total_orders else 0
        }

        return statistics

    @staticmethod
    def get_time_series_statistics(owner_id, restaurant_id=None, time_range='month'):
        """Lấy thống kê theo chuỗi thời gian (chỉ đơn hoàn thành)"""
        # Determine grouping based on time_range
        if time_range == 'day':
            truncate_func = func.date(Order.updated_at)
            date_format = '%d/%m/%Y'
        elif time_range == 'week':
            truncate_func = func.date_format(Order.updated_at, '%x-W%v')  # ISO Week
            date_format = 'Tuần %V, %Y'
        elif time_range == 'month':
            truncate_func = func.date_format(Order.updated_at, '%Y-%m')
            date_format = 'Tháng %m/%Y'
        elif time_range == 'quarter':
            # Tạo chuỗi dạng "2025-Q1", "2025-Q2"
            truncate_func = func.concat(
                func.year(Order.updated_at),
                '-Q',
                func.quarter(Order.updated_at)
            )
            date_format = 'Quý %q/%Y'
        else:
            truncate_func = func.date_format(Order.updated_at, '%Y-%m')  # Default: month
            date_format = 'Tháng %m/%Y'

        # Query for orders count
        orders_query = db.session.query(
            truncate_func.label('period'),
            func.count(Order.id).label('count')
        ).join(Restaurant).filter(
            Restaurant.owner_id == owner_id,
            Restaurant.approval_status == RestaurantApprovalStatus.APPROVED,
            Order.status == OrderStatus.COMPLETED
        )

        # Query for revenue
        revenue_query = db.session.query(
            truncate_func.label('period'),
            func.sum(Order.total_amount).label('amount')
        ).join(Restaurant).filter(
            Restaurant.owner_id == owner_id,
            Restaurant.approval_status == RestaurantApprovalStatus.APPROVED,
            Order.status == OrderStatus.COMPLETED
        )

        if restaurant_id:
            orders_query = orders_query.filter(Order.restaurant_id == restaurant_id)
            revenue_query = revenue_query.filter(Order.restaurant_id == restaurant_id)

        # Execute queries and format results
        orders_results = orders_query.group_by('period').order_by('period').all()
        revenue_results = revenue_query.group_by('period').order_by('period').all()

        # Create dictionaries for easy lookup
        orders_dict = {r.period: r.count for r in orders_results}
        revenue_dict = {r.period: float(r.amount or 0) for r in revenue_results}

        # Get all unique periods and sort them
        all_periods = sorted(set(orders_dict.keys()).union(set(revenue_dict.keys())))

        # Prepare data
        labels = []
        orders_data = []
        revenue_data = []

        for period in all_periods:
            labels.append(period)
            orders_data.append(orders_dict.get(period, 0))
            revenue_data.append(revenue_dict.get(period, 0))

        return {
            'labels': labels,
            'orders': orders_data,
            'revenue': revenue_data,
            'date_format': date_format
        }


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
        total_revenue = db.session.query(func.sum(Order.total_amount)) \
            .filter(Order.status == status) \
            .scalar()
        return float(total_revenue) if total_revenue else 0.0
    except SQLAlchemyError as e:
        print(f"Error calculating total revenue: {e}")
        return 0.0
