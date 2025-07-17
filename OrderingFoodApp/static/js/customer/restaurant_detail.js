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

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.btn-addcart').forEach(btn => {
    btn.addEventListener('click', async () => {
      const itemId = btn.dataset.id;
      // Gửi AJAX thêm vào cart
      const res = await fetch('/customer/cart', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: new URLSearchParams({
          action: 'add',
          item_id: itemId,
          quantity: 1
        })
      });
      if (res.ok) {
        // cho hiệu ứng đã thêm
        btn.classList.add('added');
        // (tuỳ chọn) disable để ko nhấn lại
        // btn.disabled = true;
      } else {
        console.error('Không thêm được vào giỏ hàng');
      }
    });
  });
});

// static/js/customer/restaurant_detail.js
document.addEventListener('DOMContentLoaded', () => {
  const cartCount = document.getElementById('cartCount');

  document.querySelectorAll('.btn-addcart').forEach(btn => {
    // bọc nút trong relative để +1 position chính xác
    btn.style.position = 'relative';

    btn.addEventListener('click', async () => {
      const itemId = btn.dataset.id;
      // 1) Gửi AJAX
      const res = await fetch('/customer/cart', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: new URLSearchParams({
          action:   'add',
          item_id:  itemId,
          quantity: 1
        })
      });

      if (!res.ok) {
        console.error('❌ Thêm giỏ hàng thất bại');
        return;
      }

      // 2) Hiệu ứng nút
      btn.classList.add('added');
      setTimeout(() => btn.classList.remove('added'), 600);

      // 3) +1 animation
      const plus = document.createElement('div');
      plus.textContent = '+1';
      plus.className = 'pop-up-plus';
      // căn giữa ngang, nằm trên btn
      plus.style.left   = '50%';
      plus.style.top    = '10%';
      plus.style.transform = 'translateX(-50%)';
      btn.appendChild(plus);
      // tự remove sau animation
      plus.addEventListener('animationend', () => plus.remove());
    });
  });
});

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.btn-addcart').forEach(btn => {
    btn.addEventListener('click', async e => {
      // ngăn chặn link bọc ngoài (và form submit nếu có)
      e.stopPropagation();
      e.preventDefault();

      const itemId = btn.dataset.id;
      const res = await fetch('/customer/cart', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: new URLSearchParams({
          action: 'add',
          item_id: itemId,
          quantity: 1
        })
      });

      if (res.ok) {
        btn.classList.add('added');
        setTimeout(() => btn.classList.remove('added'), 1000);
      } else {
        console.error('Không thêm được vào giỏ hàng');
      }
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