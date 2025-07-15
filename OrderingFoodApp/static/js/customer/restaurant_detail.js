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

function scrollMenu(id, amount) {
        const slider = document.getElementById(id);
        slider.scrollBy({ left: amount, behavior: 'smooth' });
    }

    function updateSliderButtons(sliderId) {
    const slider = document.getElementById(sliderId);
    const prevBtn = slider.parentElement.querySelector('.prev-btn');
    const nextBtn = slider.parentElement.querySelector('.next-btn');

    const maxScrollLeft = slider.scrollWidth - slider.clientWidth;

    // Disable nút khi ở đầu hoặc cuối
    prevBtn.disabled = slider.scrollLeft <= 0;
    nextBtn.disabled = slider.scrollLeft >= maxScrollLeft;

    // Hoặc ẩn nút nếu ít món
    if (slider.scrollWidth <= slider.clientWidth) {
        prevBtn.style.display = 'none';
        nextBtn.style.display = 'none';
    } else {
        prevBtn.style.display = 'inline-flex';
        nextBtn.style.display = 'inline-flex';
    }
    }

    // Gọi khi load và khi scroll
    document.querySelectorAll('[id^=slider-]').forEach(slider => {
        slider.addEventListener('scroll', () => updateSliderButtons(slider.id));
        updateSliderButtons(slider.id);
    });