document.addEventListener('DOMContentLoaded', () => {
  const totalPriceElem = document.getElementById('totalPrice');
  const cartForm = document.getElementById('cartForm');

  // Tính lại tổng tiền
  function updateTotal() {
    let total = 0;
    document.querySelectorAll('.item-checkbox').forEach(cb => {
      if (cb.checked) total += parseFloat(cb.dataset.subtotal);
    });
    totalPriceElem.textContent = total.toLocaleString('vi-VN') + ' đ';
  }

  // Event delegation trên toàn form
  cartForm.addEventListener('click', async e => {
    // Checkbox món
    if (e.target.matches('.item-checkbox')) {
      updateTotal();
      return;
    }

    // Checkbox shop
    if (e.target.matches('.select-shop')) {
      const shopItems = e.target.closest('.shop-block')
                            .querySelectorAll('.item-checkbox');
      shopItems.forEach(cb => cb.checked = e.target.checked);
      updateTotal();
      return;
    }

    // Checkbox global
    if (e.target.matches('#selectAllGlobal')) {
      const flg = e.target.checked;
      document.querySelectorAll('.item-checkbox, .select-shop')
              .forEach(cb => cb.checked = flg);
      updateTotal();
      return;
    }

    // Tăng/Giảm/Xoá
    if (e.target.matches('.btn-increase, .btn-decrease, .btn-remove')) {
      e.preventDefault();
      const btn = e.target.closest('button');
      const cartItem = btn.closest('.cart-item');
      const itemId = cartItem.dataset.itemId;
      let action;
      if (btn.matches('.btn-increase')) action = 'increase';
      else if (btn.matches('.btn-decrease')) action = 'decrease';
      else action = 'remove';

      const res = await fetch('/customer/cart', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: new URLSearchParams({ action, item_id: itemId })
      });

      // Xử lý kết quả
      if (action === 'remove') {
        cartItem.remove();
        updateTotal();
      } else {
        const data = await res.json();
        if (data.quantity > 0) {
          cartItem.querySelector('.quantity-input').value = data.quantity;
          cartItem.querySelector('.item-checkbox').dataset.subtotal = data.subtotal;
          if (cartItem.querySelector('.item-checkbox').checked) updateTotal();
        } else {
          cartItem.remove();
          updateTotal();
        }
      }
    }
  });
});
