document.addEventListener('DOMContentLoaded', function() {
    // Hiệu ứng phóng to ảnh khi hover (cho cả Info và Menu Item)
    const images = document.querySelectorAll('.card-img-top, .restaurant-image img');
    images.forEach(img => {
        img.addEventListener('mouseenter', () => {
            img.style.transform = 'scale(1.1)';
            img.style.transition = 'transform 0.6s ease';
        });
        img.addEventListener('mouseleave', () => {
            img.style.transform = 'scale(1)';
        });
    });

    // Optional: Nhấn nút “Xem chi tiết” có hiệu ứng nhún
    const buttons = document.querySelectorAll('.btn-outline-primary');
    buttons.forEach(btn => {
        btn.addEventListener('mousedown', () => {
            btn.style.transform = 'scale(0.95)';
        });
        btn.addEventListener('mouseup', () => {
            btn.style.transform = 'scale(1)';
        });
        btn.addEventListener('mouseleave', () => {
            btn.style.transform = 'scale(1)';
        });
    });
});
