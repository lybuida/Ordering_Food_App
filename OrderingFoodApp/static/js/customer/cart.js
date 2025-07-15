document.addEventListener('DOMContentLoaded', () => {
  const totalPriceElem   = document.getElementById('totalPrice');
  const cartForm         = document.getElementById('cartForm');
  const cartContainer    = document.getElementById('cartContainer');
  const continueUrl   = cartContainer.dataset.continueUrl;


  function updateTotal() {
    let total = 0;
    document.querySelectorAll('.item-checkbox').forEach(cb => {
      if (cb.checked) total += parseFloat(cb.dataset.subtotal);
    });
    totalPriceElem.textContent = total.toLocaleString('vi-VN') + ' đ';
  }

  function cleanEmptyShops() {
    document.querySelectorAll('.shop-block').forEach(shop => {
      if (!shop.querySelector('.cart-item')) shop.remove();
    });
  }

  function checkEmptyCart() {
    // nếu không còn cart-item nào, show empty message
    if (document.querySelectorAll('.cart-item').length === 0) {
      cartContainer.innerHTML = `
        <p class="alert alert-info mt-4">
          Giỏ hàng trống.
          <a href="${continueUrl}" class="text-success">Tiếp tục mua sắm</a>
        </p>`;
    }
  }

  cartForm.addEventListener('click', async e => {
    // tìm xem có phải click lên nút + / – / Xóa không
    const btn = e.target.closest('.btn-increase, .btn-decrease, .btn-remove');
    if (btn) {
      e.preventDefault();
      e.stopPropagation();

      const cartItem = btn.closest('.cart-item');
      const itemId   = cartItem.dataset.itemId;
      const action   = btn.matches('.btn-remove')    ? 'remove'
                       : btn.matches('.btn-increase') ? 'increase'
                       : 'decrease';

      const res = await fetch('/customer/cart', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: new URLSearchParams({ action, item_id: itemId })
      });

      if (action === 'remove') {
        cartItem.remove();
        updateTotal();
        cleanEmptyShops();
        checkEmptyCart();
      } else {
        const data = await res.json();
        if (data.quantity > 0) {
          cartItem.querySelector('.quantity-input').value = data.quantity;
          cartItem.querySelector('.item-checkbox')
                  .dataset.subtotal = data.subtotal;
          if (cartItem.querySelector('.item-checkbox').checked) {
            updateTotal();
          }
        } else {
          cartItem.remove();
          updateTotal();
          cleanEmptyShops();
          checkEmptyCart();
        }
      }
      return;
    }

    // checkbox món
    if (e.target.matches('.item-checkbox')) {
      updateTotal();
      return;
    }
    // checkbox shop
    if (e.target.matches('.select-shop')) {
      const shopItems = e.target.closest('.shop-block')
                            .querySelectorAll('.item-checkbox');
      shopItems.forEach(cb => cb.checked = e.target.checked);
      updateTotal();
      return;
    }
    // checkbox toàn cục
    if (e.target.matches('#selectAllGlobal')) {
      const flg = e.target.checked;
      document.querySelectorAll('.item-checkbox, .select-shop')
              .forEach(cb => cb.checked = flg);
      updateTotal();
      return;
    }
  });
});
