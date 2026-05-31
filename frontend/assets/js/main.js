/**
 * MatchaShop — shared frontend interactions
 * Page-specific init via data-page on <body>
 */

function togglePasswordVisibility() {
  const passwordInput = document.getElementById('password');
  const toggleIcon = document.getElementById('passwordToggleIcon');
  if (!passwordInput || !toggleIcon) return;

  if (passwordInput.type === 'password') {
    passwordInput.type = 'text';
    toggleIcon.textContent = 'visibility_off';
  } else {
    passwordInput.type = 'password';
    toggleIcon.textContent = 'visibility';
  }
}

function toggleVisibility(id) {
  const input = document.getElementById(id);
  const icon = document.getElementById(id + '-icon');
  if (!input || !icon) return;

  if (input.type === 'password') {
    input.type = 'text';
    icon.textContent = 'visibility_off';
  } else {
    input.type = 'password';
    icon.textContent = 'visibility';
  }
}

function transitionToPassword() {
  const emailState = document.getElementById('state-email');
  const passwordState = document.getElementById('state-password');
  const progressBar = document.getElementById('progress-bar');
  if (!emailState || !passwordState || !progressBar) return;

  emailState.classList.add('opacity-0', '-translate-y-4');

  setTimeout(() => {
    emailState.classList.add('hidden');
    passwordState.classList.remove('hidden');
    progressBar.style.width = '66%';
    passwordState.offsetHeight;
    passwordState.classList.remove('opacity-0', 'translate-y-4');
  }, 500);
}

function handleSuccess() {
  const passwordState = document.getElementById('state-password');
  const successState = document.getElementById('state-success');
  const footer = document.getElementById('card-footer');
  const progressBar = document.getElementById('progress-bar');
  const btn = document.getElementById('final-btn');
  if (!passwordState || !successState || !footer || !progressBar || !btn) return;

  btn.innerHTML =
    '<span class="material-symbols-outlined animate-spin">progress_activity</span> Processing...';
  btn.disabled = true;

  setTimeout(() => {
    passwordState.classList.add('opacity-0', 'translate-y-4');
    footer.classList.add('opacity-0');

    setTimeout(() => {
      passwordState.classList.add('hidden');
      footer.classList.add('hidden');
      successState.classList.remove('hidden');
      progressBar.style.width = '100%';
      successState.offsetHeight;
      successState.classList.remove('opacity-0', 'scale-95');
    }, 500);
  }, 1200);
}

function toggleModal() {
  const modal = document.getElementById('custom-modal');
  const content = document.getElementById('modal-content');
  if (!modal || !content) return;

  if (modal.classList.contains('hidden')) {
    modal.classList.remove('hidden');
    setTimeout(() => {
      content.classList.remove('translate-x-full');
    }, 10);
  } else {
    content.classList.add('translate-x-full');
    setTimeout(() => {
      modal.classList.add('hidden');
    }, 500);
  }
}

function handleComplete() {
  const btn = document.getElementById('payBtn');
  const overlay = document.getElementById('successOverlay');
  const card = document.getElementById('successCard');
  if (!btn || !overlay || !card) return;

  btn.innerHTML =
    '<span class="animate-spin material-symbols-outlined">progress_activity</span> Processing...';
  btn.classList.add('opacity-80', 'cursor-not-allowed');

  setTimeout(() => {
    overlay.classList.remove('opacity-0', 'pointer-events-none');
    card.classList.remove('scale-90');
    card.classList.add('scale-100');
  }, 1200);
}

function resetFlow() {
  window.location.reload();
}

const SHARED_LOGOUT_MODAL_HTML = `
  <div class="logout-modal-root" id="logout-modal" aria-hidden="true">
    <div class="logout-modal-card" role="dialog" aria-modal="true" aria-labelledby="logout-modal-title">
      <h2 class="logout-modal-title" id="logout-modal-title">Confirm Logout</h2>
      <p class="logout-modal-copy">Are you sure you want to log out?</p>
      <div class="logout-modal-actions">
        <button class="logout-cancel-btn" type="button" id="logout-cancel-btn">Cancel</button>
        <button class="logout-confirm-btn" type="button" id="logout-confirm-btn">Yes</button>
      </div>
    </div>
  </div>
`;

function initSharedLogoutConfirmation() {
  if (!document.getElementById('logout-modal')) {
    document.body.insertAdjacentHTML('beforeend', SHARED_LOGOUT_MODAL_HTML);
  }

  const modal = document.getElementById('logout-modal');
  const cancelBtn = document.getElementById('logout-cancel-btn');
  const confirmBtn = document.getElementById('logout-confirm-btn');
  if (!modal || !cancelBtn || !confirmBtn) return;

  const openModal = () => {
    modal.classList.add('is-open');
    modal.setAttribute('aria-hidden', 'false');
    cancelBtn.focus();
  };

  const closeModal = () => {
    modal.classList.remove('is-open');
    modal.setAttribute('aria-hidden', 'true');
  };

  document.querySelectorAll('a, button').forEach((element) => {
    const text = element.textContent.trim().replace(/\s+/g, ' ').toLowerCase();
    const isLogoutControl =
      element.id === 'app-logout-link' || text === 'log out' || text === 'logout';
    if (!isLogoutControl || element.dataset.logoutBound === 'true') return;

    element.addEventListener('click', (event) => {
      event.preventDefault();
      openModal();
    });
    element.dataset.logoutBound = 'true';
  });

  if (modal.dataset.modalBound === 'true') return;

  cancelBtn.addEventListener('click', closeModal);
  modal.addEventListener('click', (event) => {
    if (event.target === modal) closeModal();
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && modal.classList.contains('is-open')) {
      closeModal();
    }
  });
  confirmBtn.addEventListener('click', () => {
    window.location.href = 'login.html';
  });
  modal.dataset.modalBound = 'true';
}

function initLogin() {
  const form = document.querySelector('body.page-login form');
  if (form) {
    form.addEventListener('submit', (event) => {
      event.preventDefault();
      window.location.href = 'dashboard.html';
    });
  }

  document.querySelectorAll('input').forEach((input) => {
    input.addEventListener('focus', () => {
      const label = input.parentElement?.parentElement?.querySelector('label');
      label?.classList.add('text-secondary');
    });
    input.addEventListener('blur', () => {
      const label = input.parentElement?.parentElement?.querySelector('label');
      label?.classList.remove('text-secondary');
    });
  });
}

function initForgotPassword1() {
  document.addEventListener('mousemove', (e) => {
    const moveX = (e.clientX - window.innerWidth / 2) * 0.01;
    const moveY = (e.clientY - window.innerHeight / 2) * 0.01;

    document.querySelectorAll('.blur-\\[120px\\]').forEach((el) => {
      el.style.transform = `translate(${moveX}px, ${moveY}px)`;
    });
  });
}

function initForgotPassword2() {
  const form = document.getElementById('resetForm');
  const overlay = document.getElementById('successOverlay');
  const modal = document.getElementById('successModal');
  if (!form || !overlay || !modal) return;

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const btn = form.querySelector('button[type="submit"]');
    if (!btn) return;

    btn.disabled = true;
    btn.innerHTML =
      '<span class="material-symbols-outlined animate-spin">progress_activity</span> Updating...';

    setTimeout(() => {
      overlay.classList.remove('opacity-0', 'pointer-events-none');
      modal.classList.remove('scale-90');
      modal.classList.add('scale-100');

      setTimeout(() => {
        window.location.href = 'login.html';
      }, 2500);
    }, 1000);
  });
}

function initRegister() {
  const form = document.getElementById('registerForm');
  const error = document.getElementById('registerError');
  const overlay = document.getElementById('registerSuccessOverlay');
  const modal = document.getElementById('registerSuccessModal');
  if (!form || !error || !overlay || !modal) return;

  form.addEventListener('submit', (event) => {
    event.preventDefault();

    const formData = new FormData(form);
    const registrationData = {
      email: formData.get('email'),
      password: formData.get('password'),
      confirmPassword: formData.get('confirmPassword'),
      role: formData.get('role'),
    };

    if (registrationData.password !== registrationData.confirmPassword) {
      error.classList.remove('hidden');
      return;
    }

    error.classList.add('hidden');
    console.log('Register form data:', registrationData);

    const btn = form.querySelector('button[type="submit"]');
    if (btn) {
      btn.disabled = true;
      btn.innerHTML =
        '<span class="material-symbols-outlined animate-spin">progress_activity</span> Registering...';
    }

    setTimeout(() => {
      overlay.classList.remove('opacity-0', 'pointer-events-none');
      modal.classList.remove('scale-90');
      modal.classList.add('scale-100');

      setTimeout(() => {
        window.location.href = 'login.html';
      }, 2500);
    }, 500);
  });
}

const POS_CART_STORAGE_KEY = 'matcha_pos_cart';
const POS_ORDER_CODE_STORAGE_KEY = 'matcha_pos_order_code';

const POS_TOPPINGS = [
  { id: 'honey_boba', name: 'Honey Boba', price: 10000 },
  { id: 'sea_salt_cream', name: 'Sea Salt Cream', price: 15000 },
  { id: 'matcha_jelly', name: 'Matcha Jelly', price: 10000 },
  { id: 'oat_milk', name: 'Oat Milk', price: 12000 },
];

const POS_MENU_ITEMS = [
  {
    id: 'ceremonial-latte',
    category: 'Matcha Classics',
    name: 'Ceremonial Grade Latte',
    description: 'Stone-ground ceremonial grade matcha with silky oat milk.',
    price: 75000,
    badge: 'Popular',
    image:
      'https://lh3.googleusercontent.com/aida-public/AB6AXuD38R8L4FSRfpaQOSPtDSgjQvkcfuDFOrwoBfBCaV2cBG9i_nLOsGkkGMkN6witrF9Swu_3vu9Xr3fjKgcprxoBdot5V8dIg-JGuWJk-z4ViK0oXsRlqTWJyyS7Mh-P9SX-FjI6VIw6JKpyvhjoLVn322qOPcSYO3IULjxLtzZ5Gr_yaEjetWdlqKSMh3fxLQ7tpKD_eB_H-CtD5JIickHbQZUFG9tshpZxPMQD4nzPnwgDQ8CLKZkQCLPTRy4Okn8qQR_GyezQGV53',
  },
  {
    id: 'matcha-cream-cheese',
    category: 'Matcha Classics',
    name: 'Matcha Cream Cheese',
    description: 'Deep forest matcha topped with sea salt savory cream.',
    price: 60000,
    image:
      'https://lh3.googleusercontent.com/aida-public/AB6AXuB7lBG6XfDHs6N0iB1e-8JQV_Ih32BF-FEovTrKxMtBdKu4bu7fmgdcyr9viabl-zhXLQ1chV-Ylk8J4pE0zNIykr0wof2lhqY5ijypoZE0fWlzcI47DmgR5zubJvHYbUzYfQgyJ-O3Ub_gE-tVXDhZg_i-WSS6cb8gWmXGkHPQR9YBRCQJAKxstZM0XgNHffsKINPl-R6PM5lDie8twMHkoy4PvkEIZjkK7ss_uek3gVNdopNkTmhK0WzYF0hkTGklCel8nSOULiZq',
  },
  {
    id: 'matcha-pearl-blossom',
    category: 'Matcha Classics',
    name: 'Matcha Pearl Blossom',
    description: 'Traditional whisked tea served over house-made honey boba.',
    price: 55000,
    image:
      'https://lh3.googleusercontent.com/aida-public/AB6AXuCXMdCiTSkhaCj2XfxmnfqhmF5G_8X40ouY3AjKrKU3XTxdUReASJKRkoGqWr3tPP0yhBN3VfsBvvcKWUTiN3aMxj2fzQUQpP_3DWteZjuZeWoq0w79RrgOlu7nTwzqobxpKe_ejKCFz1sa_Q5Jle_ydgcGYjHLR6BwCIGx-j7AO78qNJ16R97quwAqsxSreeKSWLrbWSobk4Tnv_Af64ujPIxdW9aoFwELng3jgbQGlgdsppF8oSzDU6SEkHcWnQGQm86WURWYuXSP',
  },
  {
    id: 'roasted-hojicha',
    category: 'Toasted Notes',
    name: 'Roasted Hojicha',
    description: 'Slow-roasted green tea with earthy, cocoa undertones.',
    price: 65000,
    image:
      'https://lh3.googleusercontent.com/aida-public/AB6AXuC2Kn97Sodrfnwct4UT7Ts_GB-NRMKDR12ubWNEysWSAk7jw9OSC1RNzBivZqIQHF6AQT3LzBazPvAvll5H0Q4OE2tPLIoaISi6rBA9i3VCQfH0grMiWzlAJGIpTIn0LLYQSwDsQD2fV3pcSEskfD2SXvwRXsrB1UFSPBV6Ko6GEW59Q8YbPMeRbP47CbKRmA3s6HcvuRyEij7S1l9qqDBCvcF5xWYPBdPMKMzT5_afcPIzho_yBOSlxhaeCbLSnqIVMQ079QcFqp-s',
  },
];

function formatVnd(amount) {
  return `${Number(amount || 0).toLocaleString('vi-VN')} VND`;
}

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function getPosCart() {
  try {
    return JSON.parse(localStorage.getItem(POS_CART_STORAGE_KEY)) || [];
  } catch {
    return [];
  }
}

function setPosCart(cart) {
  localStorage.setItem(POS_CART_STORAGE_KEY, JSON.stringify(cart));
}

function getPosOrderCode() {
  let orderCode = localStorage.getItem(POS_ORDER_CODE_STORAGE_KEY);
  if (!orderCode) {
    orderCode = `#ATR-${Date.now().toString().slice(-6)}`;
    localStorage.setItem(POS_ORDER_CODE_STORAGE_KEY, orderCode);
  }
  return orderCode;
}

function getCartTotal(cart) {
  return cart.reduce((sum, item) => sum + item.totalPrice, 0);
}

function buildCustomizationSummary(item) {
  const parts = [item.temperature, item.iceLevel, item.sugarLevel];
  if (item.toppings.length) {
    parts.push(item.toppings.map((topping) => topping.name).join(', '));
  }
  if (item.note) {
    parts.push(`Note: ${item.note}`);
  }
  return parts.join(' | ');
}

function renderPosMenuItems() {
  const container = document.getElementById('posMenuSections');
  if (!container) return;

  const categories = [...new Set(POS_MENU_ITEMS.map((item) => item.category))];
  container.innerHTML = categories
    .map((category) => {
      const items = POS_MENU_ITEMS.filter((item) => item.category === category);
      return `
        <section>
          <div class="flex items-center gap-4 mb-6">
            <h3 class="font-headline text-2xl text-secondary">${escapeHtml(category)}</h3>
            <div class="h-px flex-1 bg-surface-container-highest"></div>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            ${items
              .map(
                (item) => `
                  <button class="group bg-surface-container-lowest rounded-xl p-4 text-left transition-all hover:translate-y-[-4px] hover:shadow-[0_20px_40px_-15px_rgba(0,44,4,0.08)] flex flex-col h-full border border-transparent hover:border-secondary-container/30" data-pos-item-id="${item.id}" type="button">
                    <div class="relative w-full aspect-[4/3] rounded-lg overflow-hidden mb-4 bg-surface-container-low">
                      <img alt="${escapeHtml(item.name)}" class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" src="${item.image}" />
                      ${
                        item.badge
                          ? `<div class="absolute top-2 right-2 bg-secondary text-white text-[10px] font-bold px-2 py-1 rounded-full uppercase tracking-widest shadow-lg">${escapeHtml(item.badge)}</div>`
                          : ''
                      }
                    </div>
                    <h4 class="font-headline text-xl text-primary mb-1">${escapeHtml(item.name)}</h4>
                    <p class="text-sm text-on-surface-variant line-clamp-2 mb-4">${escapeHtml(item.description)}</p>
                    <div class="mt-auto flex justify-between items-center">
                      <span class="text-secondary font-bold text-lg">${formatVnd(item.price)}</span>
                      <div class="w-8 h-8 rounded-full bg-secondary text-white flex items-center justify-center group-hover:scale-110 transition-transform">
                        <span class="material-symbols-outlined text-sm">add</span>
                      </div>
                    </div>
                  </button>
                `
              )
              .join('')}
          </div>
        </section>
      `;
    })
    .join('');
}

function renderPosToppingOptions() {
  const container = document.getElementById('posToppingOptions');
  if (!container) return;

  container.innerHTML = POS_TOPPINGS.map(
    (topping) => `
      <label class="flex items-center justify-between p-4 bg-surface-container-lowest rounded-xl cursor-pointer hover:bg-surface-container transition-colors">
        <div class="flex items-center gap-3">
          <input class="w-5 h-5 rounded border-outline text-secondary focus:ring-secondary" name="toppings" type="checkbox" value="${topping.id}" />
          <span class="font-bold text-sm text-primary">${escapeHtml(topping.name)}</span>
        </div>
        <span class="text-sm text-secondary">+${formatVnd(topping.price)}</span>
      </label>
    `
  ).join('');
}

function openPosCustomizeModal(itemId) {
  const item = POS_MENU_ITEMS.find((menuItem) => menuItem.id === itemId);
  const modal = document.getElementById('custom-modal');
  const content = document.getElementById('modal-content');
  const form = document.getElementById('posCustomizeForm');
  const productName = document.getElementById('posModalProductName');
  const addBtn = document.getElementById('posAddToCartBtn');
  if (!item || !modal || !content || !form || !productName || !addBtn) return;

  form.reset();
  form.dataset.itemId = item.id;
  productName.textContent = item.name;
  addBtn.textContent = `Add to Order - ${formatVnd(item.price)}`;
  modal.classList.remove('hidden');
  setTimeout(() => {
    content.classList.remove('translate-x-full');
  }, 10);
}

function closePosCustomizeModal() {
  const modal = document.getElementById('custom-modal');
  const content = document.getElementById('modal-content');
  if (!modal || !content) return;

  content.classList.add('translate-x-full');
  setTimeout(() => {
    modal.classList.add('hidden');
  }, 500);
}

function renderPosCart() {
  const cart = getPosCart();
  const panel = document.getElementById('posCartPanel');
  const itemList = document.getElementById('posCartItems');
  const count = document.getElementById('posCartCount');
  const subtotal = document.getElementById('posCartSubtotal');
  const total = document.getElementById('posCartTotal');
  const orderCode = document.getElementById('posOrderCode');
  if (!panel || !itemList || !count || !subtotal || !total || !orderCode) return;

  if (!cart.length) {
    panel.classList.add('hidden');
    panel.classList.remove('flex');
    return;
  }

  const totalAmount = getCartTotal(cart);
  panel.classList.remove('hidden');
  panel.classList.add('flex');
  count.textContent = String(cart.length);
  subtotal.textContent = formatVnd(totalAmount);
  total.textContent = formatVnd(totalAmount);
  orderCode.textContent = `Order ${getPosOrderCode()}`;

  itemList.innerHTML = cart
    .map(
      (item, index) => `
        <article class="group bg-surface-container-lowest p-4 rounded-2xl flex gap-4 transition-all hover:ring-1 hover:ring-secondary/20">
          <div class="w-16 h-16 rounded-xl overflow-hidden shrink-0">
            <img alt="${escapeHtml(item.name)}" class="w-full h-full object-cover" src="${item.image}" />
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex justify-between items-start gap-3 mb-1">
              <h5 class="text-sm font-bold text-primary leading-tight">${escapeHtml(item.name)}</h5>
              <button class="text-on-surface-variant hover:text-error transition-colors" data-pos-remove-index="${index}" type="button">
                <span class="material-symbols-outlined text-lg">close</span>
              </button>
            </div>
            <p class="text-[10px] text-on-surface-variant font-medium mb-3 leading-relaxed">${escapeHtml(buildCustomizationSummary(item))}</p>
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-primary">1 item</span>
              <span class="text-sm font-bold text-secondary">${formatVnd(item.totalPrice)}</span>
            </div>
          </div>
        </article>
      `
    )
    .join('');
}

function initPosMenu() {
  renderPosMenuItems();
  renderPosToppingOptions();
  renderPosCart();

  const menuContainer = document.getElementById('posMenuSections');
  const form = document.getElementById('posCustomizeForm');
  const closeBtn = document.getElementById('posModalCloseBtn');
  const backdrop = document.getElementById('posModalBackdrop');
  const cartItems = document.getElementById('posCartItems');
  const completeBtn = document.getElementById('posCompleteOrderBtn');
  const searchInput = document.getElementById('topbar-search');

  menuContainer?.addEventListener('click', (event) => {
    if (!(event.target instanceof Element)) return;
    const itemButton = event.target.closest('[data-pos-item-id]');
    if (!itemButton) return;
    openPosCustomizeModal(itemButton.dataset.posItemId);
  });

  closeBtn?.addEventListener('click', closePosCustomizeModal);
  backdrop?.addEventListener('click', closePosCustomizeModal);

  form?.addEventListener('submit', (event) => {
    event.preventDefault();
    const item = POS_MENU_ITEMS.find((menuItem) => menuItem.id === form.dataset.itemId);
    if (!item) return;

    const formData = new FormData(form);
    const selectedToppings = formData
      .getAll('toppings')
      .map((id) => POS_TOPPINGS.find((topping) => topping.id === id))
      .filter(Boolean);
    const toppingsTotal = selectedToppings.reduce((sum, topping) => sum + topping.price, 0);
    const cartItem = {
      cartId: `${item.id}-${Date.now()}`,
      id: item.id,
      name: item.name,
      image: item.image,
      basePrice: item.price,
      totalPrice: item.price + toppingsTotal,
      temperature: formData.get('temperature'),
      iceLevel: formData.get('iceLevel'),
      sugarLevel: formData.get('sugarLevel'),
      toppings: selectedToppings,
      note: formData.get('note')?.trim() || '',
    };

    const cart = getPosCart();
    cart.push(cartItem);
    setPosCart(cart);
    getPosOrderCode();
    renderPosCart();
    closePosCustomizeModal();
  });

  cartItems?.addEventListener('click', (event) => {
    if (!(event.target instanceof Element)) return;
    const removeButton = event.target.closest('[data-pos-remove-index]');
    if (!removeButton) return;

    const cart = getPosCart();
    cart.splice(Number(removeButton.dataset.posRemoveIndex), 1);
    setPosCart(cart);
    renderPosCart();
  });

  completeBtn?.addEventListener('click', () => {
    if (!getPosCart().length) return;
    window.location.href = 'POS_payment.html';
  });

  if (searchInput?.parentElement) {
    searchInput.addEventListener('focus', () => {
      searchInput.parentElement.classList.add('scale-[1.02]');
    });
    searchInput.addEventListener('blur', () => {
      searchInput.parentElement.classList.remove('scale-[1.02]');
    });
  }
}

function renderPosPaymentOrder() {
  const cart = getPosCart();
  const itemList = document.getElementById('paymentItemList');
  const emptyState = document.getElementById('paymentEmptyState');
  const subtotal = document.getElementById('paymentSubtotal');
  const total = document.getElementById('paymentTotal');
  const orderCode = document.getElementById('paymentOrderCode');
  const payBtn = document.getElementById('payBtn');
  if (!itemList || !emptyState || !subtotal || !total || !orderCode || !payBtn) return;

  const totalAmount = getCartTotal(cart);
  orderCode.textContent = getPosOrderCode();
  subtotal.textContent = formatVnd(totalAmount);
  total.textContent = formatVnd(totalAmount);
  payBtn.disabled = !cart.length;

  if (!cart.length) {
    itemList.innerHTML = '';
    emptyState.classList.remove('hidden');
    return;
  }

  emptyState.classList.add('hidden');
  itemList.innerHTML = cart
    .map(
      (item) => `
        <article class="p-6 flex items-center gap-5">
          <div class="w-20 h-20 rounded-xl overflow-hidden flex-shrink-0 bg-surface-container-low">
            <img alt="${escapeHtml(item.name)}" class="w-full h-full object-cover" src="${item.image}" />
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex justify-between gap-6">
              <div>
                <h3 class="font-headline text-xl text-primary">${escapeHtml(item.name)}</h3>
                <p class="text-sm text-on-surface-variant leading-relaxed mt-1">${escapeHtml(buildCustomizationSummary(item))}</p>
              </div>
              <div class="text-right shrink-0">
                <p class="text-xs text-on-surface-variant mb-1">Base ${formatVnd(item.basePrice)}</p>
                <p class="font-bold text-secondary text-lg">${formatVnd(item.totalPrice)}</p>
              </div>
            </div>
          </div>
        </article>
      `
    )
    .join('');
}

function initPosPayment() {
  renderPosPaymentOrder();

  const payBtn = document.getElementById('payBtn');
  const overlay = document.getElementById('successOverlay');
  const card = document.getElementById('successCard');
  const successText = document.getElementById('successPaymentText');
  const newOrderBtn = document.getElementById('newOrderBtn');

  payBtn?.addEventListener('click', () => {
    const selectedPayment = document.querySelector('input[name="payment"]:checked')?.value;
    if (!getPosCart().length || !overlay || !card) return;

    payBtn.disabled = true;
    payBtn.innerHTML =
      '<span class="material-symbols-outlined animate-spin">progress_activity</span> Processing...';

    setTimeout(() => {
      const label =
        selectedPayment === 'cash'
          ? 'cash'
          : selectedPayment === 'card'
            ? 'credit card'
            : 'QR';
      if (successText) {
        successText.textContent = `${getPosOrderCode()} completed successfully by ${label} payment.`;
      }
      overlay.classList.remove('opacity-0', 'pointer-events-none');
      card.classList.remove('scale-90');
      card.classList.add('scale-100');
    }, 800);
  });

  newOrderBtn?.addEventListener('click', () => {
    localStorage.removeItem(POS_CART_STORAGE_KEY);
    localStorage.removeItem(POS_ORDER_CODE_STORAGE_KEY);
    window.location.href = 'POS_menu.html';
  });
}

function initDeliveryManage() {
  document.querySelectorAll('nav a').forEach((link) => {
    link.addEventListener('click', () => {
      document.querySelectorAll('nav a').forEach((l) => {
        l.className =
          'flex items-center gap-4 text-on-primary-container hover:bg-on-primary-fixed-variant/20 rounded-full px-6 py-3 transition-all duration-200';
      });
      link.className =
        'flex items-center gap-4 bg-secondary-container text-on-secondary-container rounded-full px-6 py-3 font-bold active:scale-95 transition-all duration-150';
    });
  });

  const searchInput = document.querySelector('input[type="text"]');
  if (!searchInput?.parentElement) return;

  searchInput.addEventListener('focus', () => {
    searchInput.parentElement.classList.add('scale-105');
  });
  searchInput.addEventListener('blur', () => {
    searchInput.parentElement.classList.remove('scale-105');
  });
}

function initShipper() {
  document.querySelectorAll('.status-btn').forEach((btn) => {
    btn.addEventListener('click', function () {
      const originalContent = this.innerHTML;

      this.style.transform = 'scale(0.95)';
      setTimeout(() => {
        this.style.transform = 'scale(1)';
        this.innerHTML =
          '<span class="material-symbols-outlined">check_circle</span> <span>Updated!</span>';
        this.classList.add('ring-2', 'ring-secondary', 'ring-offset-2');
      }, 150);

      setTimeout(() => {
        this.innerHTML = originalContent;
        this.classList.remove('ring-2', 'ring-secondary', 'ring-offset-2');
      }, 2000);
    });
  });

  const cards = document.querySelectorAll(
    '.bg-surface-container-lowest.cursor-pointer'
  );
  cards.forEach((card) => {
    card.addEventListener('click', function () {
      cards.forEach((c) => c.classList.remove('ring-2', 'ring-secondary'));
      this.classList.add('ring-2', 'ring-secondary');
    });
  });
}

const pageInits = {
  login: initLogin,
  'forgot-password-1': initForgotPassword1,
  'forgot-password-2': initForgotPassword2,
  register: initRegister,
  'pos-menu': initPosMenu,
  'pos-payment': initPosPayment,
  'delivery-manage': initDeliveryManage,
  shipper: initShipper,
};

Object.assign(window, {
  togglePasswordVisibility,
  toggleVisibility,
  transitionToPassword,
  handleSuccess,
  toggleModal,
  handleComplete,
  resetFlow,
});

document.addEventListener('DOMContentLoaded', () => {
  initSharedLogoutConfirmation();

  const page = document.body.dataset.page;
  if (page && pageInits[page]) {
    pageInits[page]();
  }
});
