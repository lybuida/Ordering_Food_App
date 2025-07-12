function addToCartAnimation(button, itemId) {
    const img = document.querySelector('.img-fluid'); // Ảnh món ăn
    const cartIcon = document.querySelector('#cartIcon'); // Icon giỏ hàng trên navbar

    // Clone hình ảnh
    const flyingImg = img.cloneNode(true);
    flyingImg.style.position = 'absolute';
    flyingImg.style.zIndex = 1000;
    flyingImg.style.width = img.offsetWidth + 'px';
    flyingImg.style.height = img.offsetHeight + 'px';

    // Vị trí ban đầu (đã tính scroll)
    const imgRect = img.getBoundingClientRect();
    flyingImg.style.top = window.scrollY + imgRect.top + 'px';
    flyingImg.style.left = window.scrollX + imgRect.left + 'px';
    document.body.appendChild(flyingImg);

    // Vị trí giỏ hàng (đã tính scroll)
    const cartRect = cartIcon.getBoundingClientRect();
    const deltaX = (window.scrollX + cartRect.left + cartRect.width / 2) - (window.scrollX + imgRect.left + imgRect.width / 2);
    const deltaY = (window.scrollY + cartRect.top + cartRect.height / 2) - (window.scrollY + imgRect.top + imgRect.height / 2);

    // Animate
    flyingImg.animate([
        { transform: 'translate(0, 0) scale(1)', opacity: 1 },
        { transform: `translate(${deltaX}px, ${deltaY}px) scale(0.1)`, opacity: 0.5 }
    ], {
        duration: 800,
        easing: 'ease-in-out'
    }).onfinish = function () {
        flyingImg.remove();

        // Gọi API thêm món vào giỏ hàng (AJAX)
        fetch('/customer/cart', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({
                action: 'add',
                item_id: itemId,
                quantity: document.getElementById('quantityInput').value
            })
        }).then(response => {
            if (response.ok) {
                console.log('Đã thêm vào giỏ hàng!');
            }
        });
    };
}
