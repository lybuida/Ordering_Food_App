// restaurants_list.js
document.addEventListener('DOMContentLoaded', function() {
    // Xử lý khi nhập tìm kiếm
    const searchInput = document.querySelector('input[name="search"]');
    if (searchInput) {
        searchInput.addEventListener('keyup', function(e) {
            if (e.key === 'Enter') {
                this.closest('form').submit();
            }
        });
    }

    // Thêm nút xóa tìm kiếm
    const addClearButton = () => {
        if (searchInput.value) {
            if (!document.querySelector('.clear-search')) {
                const clearBtn = document.createElement('button');
                clearBtn.type = 'button';
                clearBtn.className = 'btn clear-search position-absolute end-0 top-0';
                clearBtn.innerHTML = '<i class="fas fa-times"></i>';
                clearBtn.style.zIndex = '10';
                clearBtn.style.right = '40px';
                clearBtn.style.top = '5px';

                clearBtn.addEventListener('click', () => {
                    searchInput.value = '';
                    clearBtn.remove();
                    searchInput.closest('form').submit();
                });

                searchInput.parentNode.insertBefore(clearBtn, searchInput.nextSibling);
            }
        } else {
            const clearBtn = document.querySelector('.clear-search');
            if (clearBtn) clearBtn.remove();
        }
    };

    if (searchInput) {
        searchInput.addEventListener('input', addClearButton);
        addClearButton(); // Khởi tạo ban đầu
    }
});