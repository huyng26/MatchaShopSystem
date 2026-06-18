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

const MATCHA_PUBLIC_PAGES = new Set([
  'login',
  'register',
  'forgot-password-1',
  'forgot-password-2',
]);

const MATCHA_ROLE_DEFAULT_PAGE = {
  admin: 'dashboard.html',
  cashier: 'POS_menu.html',
  delivery_manager: 'delivery_manage.html',
  inventory_manager: 'inventory_list.html',
  shipper: 'shipper.html',
};

const MATCHA_FILE_PAGE_MAP = {
  'login.html': 'login',
  'register.html': 'register',
  'forgot_password_1.html': 'forgot-password-1',
  'forgot_password_2.html': 'forgot-password-2',
  'dashboard.html': 'dashboard',
  'POS_menu.html': 'pos-menu',
  'POS_payment.html': 'pos-payment',
  'delivery_manage.html': 'delivery-manage',
  'shipper.html': 'shipper',
  'performance.html': 'performance',
  'financial_management.html': 'financial-management',
  'menu.html': 'menu',
  'product_detail.html': 'product-detail',
  'inventory_list.html': 'inventory-list',
  'inventory_detail.html': 'inventory-detail',
  'customer_list.html': 'customer-list',
  'customer_detail.html': 'customer-detail',
  'employee_list.html': 'employee-list',
  'employee_detail.html': 'employee-detail',
  'account_list.html': 'account-list',
  'account_detail.html': 'account-detail',
  'settings.html': 'settings',
};

function getCurrentFrontendPageName() {
  return window.location.pathname.split('/').pop() || 'dashboard.html';
}

function buildFrontendLoginRedirectUrl() {
  const nextPath = `${getCurrentFrontendPageName()}${window.location.search || ''}${window.location.hash || ''}`;
  return `login.html?next=${encodeURIComponent(nextPath)}`;
}

function isSafeFrontendNextPath(value) {
  if (!value) return false;
  if (value.includes('/') || value.includes('\\')) return false;
  return /^[A-Za-z0-9_.-]+\.html([?#].*)?$/.test(value);
}

function getStoredFrontendUser() {
  try {
    return JSON.parse(localStorage.getItem('matcha_user') || 'null');
  } catch (error) {
    return null;
  }
}

function getFrontendUserRole(user = getStoredFrontendUser()) {
  return String(user?.role || '').toLowerCase();
}

function getDataPageFromFrontendPath(value) {
  const pageName = String(value || '').split(/[?#]/)[0];
  return MATCHA_FILE_PAGE_MAP[pageName] || '';
}

function canFrontendRoleAccessPage(role, page) {
  if (!page) return false;
  if (MATCHA_PUBLIC_PAGES.has(page)) return true;

  if (role === 'admin') {
    return !['shipper', 'performance'].includes(page);
  }

  const allowedPagesByRole = {
    cashier: new Set(['pos-menu', 'pos-payment']),
    delivery_manager: new Set(['delivery-manage']),
    inventory_manager: new Set(['inventory-list', 'inventory-detail']),
    shipper: new Set(['shipper', 'performance']),
  };

  return Boolean(allowedPagesByRole[role]?.has(page));
}

function getFrontendDefaultPageForRole(role) {
  return MATCHA_ROLE_DEFAULT_PAGE[role] || 'login.html';
}

function getLoginRedirectTarget(user = getStoredFrontendUser()) {
  const role = getFrontendUserRole(user);
  const next = new URLSearchParams(window.location.search).get('next') || '';
  const nextPage = getDataPageFromFrontendPath(next);

  if (
    isSafeFrontendNextPath(next)
    && nextPage
    && !MATCHA_PUBLIC_PAGES.has(nextPage)
    && canFrontendRoleAccessPage(role, nextPage)
  ) {
    return next;
  }

  return getFrontendDefaultPageForRole(role);
}

function enforceFrontendAuthGuard() {
  const page = document.body?.dataset.page;
  if (!page || MATCHA_PUBLIC_PAGES.has(page)) return false;

  if (!localStorage.getItem('matcha_access_token')) {
    window.location.replace(buildFrontendLoginRedirectUrl());
    return true;
  }

  const role = getFrontendUserRole();
  if (!canFrontendRoleAccessPage(role, page)) {
    window.location.replace(getFrontendDefaultPageForRole(role));
    return true;
  }

  return false;
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
    localStorage.removeItem('matcha_access_token');
    localStorage.removeItem('matcha_refresh_token');
    localStorage.removeItem('matcha_user');
    window.location.href = 'login.html';
  });
  modal.dataset.modalBound = 'true';
}

const MATCHA_API_BASE_URL =
  window.MATCHA_API_BASE_URL || 'http://localhost:8000/api/v1';
const LOGIN_ERROR_MESSAGE = 'Invalid email or password.';

async function requestMatchaApi(path, options = {}) {
  const response = await fetch(`${MATCHA_API_BASE_URL}${path}`, options);

  const payload = await response.json().catch(() => null);
  if (!response.ok || payload?.success === false) {
    throw new Error(payload?.message || 'Request failed');
  }

  return payload?.data ?? payload;
}

function initLogin() {
  const form = document.querySelector('body.page-login form');
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');
  const loginError = document.getElementById('loginEmailError');
  const submitBtn = form?.querySelector('button[type="submit"]');
  const originalSubmitHtml = submitBtn?.innerHTML;

  if (form) {
    form.addEventListener('submit', async (event) => {
      event.preventDefault();

      if (!form.reportValidity()) return;

      const email = String(emailInput?.value || '').trim().toLowerCase();
      const password = String(passwordInput?.value || '');

      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML =
          '<span class="material-symbols-outlined animate-spin">progress_activity</span> Connecting...';
      }

      try {
        const auth = await requestMatchaApi('/auth/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ email, password }),
        });

        if (!auth?.access_token || !auth?.refresh_token || !auth?.user) {
          throw new Error('Login API returned an invalid response');
        }

        loginError?.classList.add('hidden');
        localStorage.setItem('matcha_access_token', auth.access_token);
        localStorage.setItem('matcha_refresh_token', auth.refresh_token);
        localStorage.setItem('matcha_user', JSON.stringify(auth.user));
        window.location.href = getLoginRedirectTarget(auth.user);
      } catch (error) {
        console.error('Login failed:', error);
        if (loginError) {
          loginError.textContent = error.message || LOGIN_ERROR_MESSAGE;
          loginError.classList.remove('hidden');
        }
      } finally {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = originalSubmitHtml;
        }
      }
    });
  }

  [emailInput, passwordInput].forEach((input) => {
    input?.addEventListener('input', () => {
      if (loginError) {
        loginError.textContent = LOGIN_ERROR_MESSAGE;
      }
      loginError?.classList.add('hidden');
    });
  });

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
const POS_CUSTOMER_STORAGE_KEY = 'matcha_pos_customer';
const POS_ORDER_TYPE_STORAGE_KEY = 'matcha_pos_order_type';
const POS_DELIVERY_DETAILS_STORAGE_KEY = 'matcha_pos_delivery_details';
const POS_INSTORE_CUSTOMER_DETAILS_STORAGE_KEY = 'matcha_pos_instore_customer_details';
const POS_STRIPE_CHECKOUT_STORAGE_KEY = 'matcha_pos_stripe_checkout';
const POS_CHECKOUT_RUN_STORAGE_KEY = 'matcha_pos_checkout_run_id';
const POS_STRIPE_POLL_INTERVAL_MS = 2500;
const POS_STRIPE_POLL_MAX_ATTEMPTS = 120;

let POS_TOPPINGS = [];
let POS_MENU_ITEMS = [];
let POS_MENU_SEARCH_QUERY = '';
let POS_PREPARING_DELIVERY_ORDERS = [];
let POS_STRIPE_POLL_TIMEOUT_ID = null;
let POS_STRIPE_POLL_ATTEMPTS = 0;
let POS_INSTORE_CUSTOMER_LOOKUP_TIMEOUT_ID = null;
let POS_INSTORE_CUSTOMER_LOOKUP_SEQUENCE = 0;
let POS_DELIVERY_CUSTOMER_LOOKUP_TIMEOUT_ID = null;
let POS_DELIVERY_CUSTOMER_LOOKUP_SEQUENCE = 0;

const POS_FALLBACK_IMAGE =
  'https://images.unsplash.com/photo-1515823662972-da6a2e4d3002?auto=format&fit=crop&w=900&q=80';

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

function getMatchaApiBaseUrl() {
  return MATCHA_API_BASE_URL;
}

function getMatchaAuthHeaders() {
  const token = localStorage.getItem('matcha_access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function fetchMatchaApi(path, options = {}) {
  const response = await fetch(`${getMatchaApiBaseUrl()}${path}`, {
    ...options,
    headers: {
      ...getMatchaAuthHeaders(),
      ...(options.headers || {}),
    },
  });
  const payload = await response.json().catch(() => null);

  if (!response.ok || payload?.success === false) {
    throw new Error(payload?.message || 'Request failed');
  }

  return payload?.data ?? payload;
}

function getApiListData(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.items)) return data.items;
  return [];
}

function mapProductToPosItem(product) {
  return {
    id: String(product.id),
    category: product.category || 'Menu',
    name: product.name || 'Unnamed Product',
    description: product.description || 'No description available.',
    price: Number(product.selling_price) || 0,
    image: product.image_url || POS_FALLBACK_IMAGE,
  };
}

function isToppingProduct(product) {
  return String(product.category || '').trim().toLowerCase() === 'toppings';
}

function mapProductToPosTopping(product) {
  return {
    id: String(product.id),
    name: product.name || 'Unnamed Topping',
    price: Number(product.selling_price) || 0,
  };
}

function renderPosMenuState(message, type = 'info') {
  const container = document.getElementById('posMenuSections');
  if (!container) return;

  const icon = type === 'error' ? 'error' : type === 'empty' ? 'inventory_2' : 'progress_activity';
  const textClass = type === 'error' ? 'text-error' : 'text-on-surface-variant';
  container.innerHTML = `
    <div class="rounded-2xl bg-surface-container-lowest border border-outline-variant/10 p-10 text-center">
      <span class="material-symbols-outlined ${textClass} text-4xl mb-3">${icon}</span>
      <p class="text-sm font-extrabold ${textClass}">${escapeHtml(message)}</p>
    </div>
  `;
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

function getPosOrderType() {
  return localStorage.getItem(POS_ORDER_TYPE_STORAGE_KEY) === 'delivery' ? 'delivery' : 'instore';
}

function setPosOrderType(orderType) {
  localStorage.setItem(
    POS_ORDER_TYPE_STORAGE_KEY,
    orderType === 'delivery' ? 'delivery' : 'instore'
  );
}

function isPosDeliveryOrder() {
  return getPosOrderType() === 'delivery';
}

function getStoredPosOrderCode() {
  const orderCode = localStorage.getItem(POS_ORDER_CODE_STORAGE_KEY);
  if (orderCode?.startsWith('#ATR-')) {
    localStorage.removeItem(POS_ORDER_CODE_STORAGE_KEY);
    return '';
  }
  return orderCode || '';
}

function getPosOrderCode() {
  return getStoredPosOrderCode() || 'Generated on submit';
}

function createPosCheckoutRunId() {
  if (window.crypto?.randomUUID) {
    return window.crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function getPosCheckoutRunId() {
  return localStorage.getItem(POS_CHECKOUT_RUN_STORAGE_KEY) || '';
}

function startNewPosCheckoutRun() {
  const checkoutRunId = createPosCheckoutRunId();
  localStorage.setItem(POS_CHECKOUT_RUN_STORAGE_KEY, checkoutRunId);
  clearStoredPosStripeCheckout();
  stopPosStripeCheckoutPolling();
  return checkoutRunId;
}

function getPosDeliveryDetails() {
  try {
    return JSON.parse(localStorage.getItem(POS_DELIVERY_DETAILS_STORAGE_KEY)) || {};
  } catch {
    return {};
  }
}

function setPosDeliveryDetails(details) {
  localStorage.setItem(POS_DELIVERY_DETAILS_STORAGE_KEY, JSON.stringify(details || {}));
}

function getPosInstoreCustomerDetails() {
  try {
    return JSON.parse(localStorage.getItem(POS_INSTORE_CUSTOMER_DETAILS_STORAGE_KEY)) || {};
  } catch {
    return {};
  }
}

function setPosInstoreCustomerDetails(details) {
  localStorage.setItem(POS_INSTORE_CUSTOMER_DETAILS_STORAGE_KEY, JSON.stringify(details || {}));
}

function updatePosOrderModeUi() {
  const orderType = getPosOrderType();
  const isDelivery = orderType === 'delivery';
  const title = document.getElementById('posOrderModeTitle');
  const subtitle = document.getElementById('posOrderModeSubtitle');
  const cartTitle = document.getElementById('posCartTitle');

  if (title) {
    title.textContent = isDelivery ? 'Delivery Order' : 'In-shop Order';
  }
  if (subtitle) {
    subtitle.textContent = isDelivery
      ? 'Create a phone order for a remote customer, then collect delivery details at checkout.'
      : 'Select an available item, customize it, then add it to the order.';
  }
  if (cartTitle) {
    cartTitle.textContent = isDelivery ? 'Delivery Order' : 'Current Order';
  }

  document.querySelectorAll('.pos-order-type-button').forEach((button) => {
    const active = button.dataset.posOrderType === orderType;
    button.classList.toggle('bg-secondary', active);
    button.classList.toggle('text-on-secondary', active);
    button.classList.toggle('text-on-surface-variant', !active);
  });
}

function getCartTotal(cart) {
  return cart.reduce((sum, item) => sum + Number(item.totalPrice || 0), 0);
}

function buildCustomizationSummary(item) {
  const toppings = item.toppings || [];
  const parts = [item.iceLevel, item.sugarLevel].filter(Boolean);
  if (toppings.length) {
    parts.push(toppings.map((topping) => topping.name).join(', '));
  }
  if (item.note) {
    parts.push(`Note: ${item.note}`);
  }
  return parts.join(' | ');
}

function buildPosOrderItems(cart) {
  const quantities = new Map();

  cart.forEach((item) => {
    if (item.id) {
      quantities.set(item.id, (quantities.get(item.id) || 0) + 1);
    }

    (item.toppings || []).forEach((topping) => {
      if (topping.id) {
        quantities.set(topping.id, (quantities.get(topping.id) || 0) + 1);
      }
    });
  });

  return Array.from(quantities.entries()).map(([productId, quantity]) => ({
    product_id: productId,
    quantity,
  }));
}

function buildPosOrderNote(cart) {
  const note = cart
    .map((item, index) => `${index + 1}. ${item.name}: ${buildCustomizationSummary(item)}`)
    .join('\n');
  return note || null;
}

function getPosPaymentMethod(value) {
  if (value === 'cod') return 'cod';
  if (value === 'cash') return 'cash';
  if (value === 'card') return 'card';
  return 'bank_transfer';
}

function getPosPaymentLabel(value) {
  if (value === 'cod') return 'COD';
  if (value === 'cash') return 'cash';
  if (value === 'card') return 'card';
  return 'Stripe Checkout QR';
}

function isPosStripeQrPayment(value) {
  return value === 'qr';
}

function getPosStripeCartSignature() {
  const items = buildPosOrderItems(getPosCart())
    .map((item) => ({
      product_id: item.product_id,
      quantity: item.quantity,
    }))
    .sort((left, right) => String(left.product_id).localeCompare(String(right.product_id)));

  return JSON.stringify({
    order_type: getPosOrderType(),
    total: getCartTotal(getPosCart()),
    delivery_details: getPosOrderType() === 'delivery' ? getPosDeliveryDetails() : null,
    instore_customer_details: getPosOrderType() === 'delivery' ? null : getPosInstoreCustomerDetails(),
    items,
  });
}

function getStoredPosStripeCheckout() {
  try {
    return JSON.parse(localStorage.getItem(POS_STRIPE_CHECKOUT_STORAGE_KEY) || 'null');
  } catch {
    return null;
  }
}

function setStoredPosStripeCheckout(checkout) {
  localStorage.setItem(POS_STRIPE_CHECKOUT_STORAGE_KEY, JSON.stringify(checkout || {}));
}

function clearStoredPosStripeCheckout() {
  localStorage.removeItem(POS_STRIPE_CHECKOUT_STORAGE_KEY);
}

function canReuseStoredPosStripeCheckout(checkout) {
  if (!checkout?.stripe_checkout_session_id || !checkout?.checkout_url) return false;
  if (!checkout.checkout_run_id || checkout.checkout_run_id !== getPosCheckoutRunId()) return false;
  if (checkout.cart_signature !== getPosStripeCartSignature()) return false;
  return String(checkout.status || 'pending') === 'pending';
}

function buildPosStripeCheckoutState(session, order) {
  return {
    payment_id: session.payment_id,
    order_id: session.order_id || order?.id,
    order_code: order?.order_code || getPosOrderCode(),
    order_type: order?.order_type || getPosOrderType(),
    stripe_checkout_session_id: session.stripe_checkout_session_id,
    checkout_url: session.checkout_url,
    qr_code_data_url: session.qr_code_data_url,
    expires_at: session.expires_at || null,
    status: session.status || 'pending',
    amount: Number(order?.total_amount || getCartTotal(getPosCart())),
    cart_signature: getPosStripeCartSignature(),
    checkout_run_id: getPosCheckoutRunId(),
    created_at: new Date().toISOString(),
  };
}

function getPosStripeCheckoutFromRedirect(sessionId) {
  const stored = getStoredPosStripeCheckout();
  if (stored?.stripe_checkout_session_id === sessionId) {
    return stored;
  }
  return {
    stripe_checkout_session_id: sessionId,
    order_code: getPosOrderCode(),
    order_type: getPosOrderType(),
    amount: getCartTotal(getPosCart()),
    cart_signature: getPosStripeCartSignature(),
    checkout_run_id: getPosCheckoutRunId(),
    status: 'pending',
  };
}

function setPosPaymentStatus(message = '', type = 'info') {
  const status = document.getElementById('paymentStatus');
  if (!status) return;

  status.textContent = message;
  status.classList.toggle('hidden', !message);
  status.classList.remove('text-error', 'text-secondary', 'text-on-surface-variant');
  status.classList.add(
    type === 'error' ? 'text-error' : type === 'success' ? 'text-secondary' : 'text-on-surface-variant'
  );
}

function buildDeliveryOrderNote(cart, deliveryDetails) {
  return [
    buildPosOrderNote(cart),
    deliveryDetails.note ? `Delivery note: ${deliveryDetails.note}` : '',
  ].filter(Boolean).join('\n\n') || null;
}

function validateDeliveryDetails(details) {
  const missing = [];
  if (!details.customer_name) missing.push('customer name');
  if (!details.customer_phone) missing.push('phone');
  if (!details.delivery_address) missing.push('delivery address');

  if (missing.length) {
    throw new Error(`Delivery order requires ${missing.join(', ')}.`);
  }
}

function validateInstoreCustomerDetails(details) {
  if (details?.customer_phone && !details.customer_name) {
    throw new Error('Customer name is required when the phone number is not found.');
  }
  if (!details?.create_customer_profile) return;
  const missing = [];
  if (!details.customer_phone) missing.push('customer phone');
  if (!details.customer_name) missing.push('customer name');
  if (missing.length) {
    throw new Error(`Creating a loyalty profile requires ${missing.join(', ')}.`);
  }
}

async function submitPosOrder(selectedPayment, checkoutDetails = {}, onStep = () => {}) {
  const cart = getPosCart();
  const items = buildPosOrderItems(cart);
  const orderType = getPosOrderType();
  const deliveryDetails = checkoutDetails?.deliveryDetails || null;
  const instoreCustomerDetails = checkoutDetails?.instoreCustomerDetails || {};

  if (!items.length) {
    throw new Error('No order items selected.');
  }

  if (!localStorage.getItem('matcha_access_token')) {
    throw new Error('Please log in before completing an order.');
  }

  const paymentMethod = getPosPaymentMethod(selectedPayment);
  if (orderType === 'delivery' && paymentMethod === 'cash') {
    throw new Error('Cash register payment is not allowed for delivery orders. Use COD or prepaid QR/card.');
  }

  const payload = {
    order_type: orderType,
    discount_amount: 0,
    items,
  };

  if (orderType === 'delivery') {
    validateDeliveryDetails(deliveryDetails || {});
    payload.customer_name = deliveryDetails.customer_name;
    payload.customer_phone = deliveryDetails.customer_phone;
    payload.delivery_address = deliveryDetails.delivery_address;
    payload.note = buildDeliveryOrderNote(cart, deliveryDetails);
  } else {
    validateInstoreCustomerDetails(instoreCustomerDetails);
    Object.assign(payload, (() => {
      const checkoutPhone = instoreCustomerDetails.customer_phone || '';
      if (!checkoutPhone) return {};
      return {
        customer_name: instoreCustomerDetails.customer_name || null,
        customer_phone: checkoutPhone,
        create_customer_profile: Boolean(instoreCustomerDetails.create_customer_profile),
      };
    })());
    payload.note = buildPosOrderNote(cart);
  }

  onStep('Creating pending order...');
  const order = await fetchMatchaApi('/orders', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  onStep('Starting order preparation...');
  const processingOrder = await fetchMatchaApi(`/orders/${order.id}/start-processing`, {
    method: 'POST',
  });
  const preparedOrder = processingOrder || order;
  const orderId = preparedOrder.id || order.id;

  if (isPosStripeQrPayment(selectedPayment)) {
    onStep('Creating Stripe Checkout QR...');
    const stripeSession = await fetchMatchaApi('/payments/stripe/checkout-session', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        order_id: orderId,
        ready_for_delivery: orderType === 'delivery',
      }),
    });

    return {
      requiresStripeCheckout: true,
      order: preparedOrder,
      stripeSession,
    };
  }

  const amount = Number(preparedOrder.total_amount || order.total_amount || getCartTotal(cart));
  const paymentPayload = {
    order_id: orderId,
    method: paymentMethod,
    amount,
  };

  if (paymentMethod === 'cash') {
    paymentPayload.amount_received = amount;
  }

  onStep(paymentMethod === 'cod' ? 'Creating pending COD payment...' : `Recording ${getPosPaymentLabel(selectedPayment)} payment...`);
  await fetchMatchaApi('/payments', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(paymentPayload),
  });

  if (orderType === 'delivery') {
    return preparedOrder;
  }

  onStep('Completing in-shop order and deducting inventory...');
  const completedOrder = await fetchMatchaApi(`/orders/${orderId}/complete`, {
    method: 'POST',
  });

  return {
    ...preparedOrder,
    ...(completedOrder || {}),
    order_code: preparedOrder.order_code || order.order_code,
  };
}

function renderPosMenuItems() {
  const container = document.getElementById('posMenuSections');
  if (!container) return;

  const searchQuery = POS_MENU_SEARCH_QUERY.trim().toLowerCase();
  const visibleItems = searchQuery
    ? POS_MENU_ITEMS.filter((item) => [
      item.name,
      item.description,
      item.category,
      formatVnd(item.price),
    ].some((value) => String(value || '').toLowerCase().includes(searchQuery)))
    : POS_MENU_ITEMS;

  if (!POS_MENU_ITEMS.length) {
    renderPosMenuState('No available products found. Add available products in Menu first.', 'empty');
    return;
  }

  if (!visibleItems.length) {
    renderPosMenuState(`No products found for "${POS_MENU_SEARCH_QUERY}".`, 'empty');
    return;
  }

  const productGridClass = getPosCart().length
    ? 'grid grid-cols-2 gap-3 md:grid-cols-3'
    : 'grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-5';
  const categories = [...new Set(visibleItems.map((item) => item.category))];
  container.innerHTML = categories
    .map((category) => {
      const items = visibleItems.filter((item) => item.category === category);
      return `
        <section>
          <div class="flex items-center gap-3 mb-4">
            <h3 class="font-headline text-xl text-secondary">${escapeHtml(category)}</h3>
            <div class="h-px flex-1 bg-surface-container-highest"></div>
          </div>
          <div class="${productGridClass}">
            ${items
              .map(
                (item) => `
                  <button class="group bg-surface-container-lowest rounded-xl p-3 pb-4 text-left transition-all hover:translate-y-[-2px] hover:shadow-[0_16px_32px_-18px_rgba(0,44,4,0.12)] flex flex-col h-full border border-transparent hover:border-secondary-container/30" data-pos-item-id="${item.id}" type="button">
                    <div class="relative w-full aspect-[16/10] rounded-lg overflow-hidden mb-3 bg-surface-container-low">
                      <img alt="${escapeHtml(item.name)}" class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" src="${item.image}" />
                      ${
                        item.badge
                          ? `<div class="absolute top-2 right-2 bg-secondary text-white text-[9px] font-bold px-2 py-0.5 rounded-full uppercase tracking-widest shadow-lg">${escapeHtml(item.badge)}</div>`
                          : ''
                      }
                    </div>
                    <h4 class="font-headline text-base text-primary leading-tight line-clamp-1">${escapeHtml(item.name)}</h4>
                    <p class="mt-1 text-xs text-on-surface-variant mb-3">${escapeHtml(item.description)}</p>
                    <div class="mt-auto flex justify-between items-center">
                      <span class="text-secondary font-bold text-sm">${formatVnd(item.price)}</span>
                      <div class="w-7 h-7 rounded-full bg-secondary text-white flex items-center justify-center group-hover:scale-110 transition-transform">
                        <span class="material-symbols-outlined text-[16px]">add</span>
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

  if (!POS_TOPPINGS.length) {
    container.innerHTML = `
      <div class="rounded-xl bg-surface-container-lowest p-4 text-sm font-bold text-on-surface-variant">
        No toppings available.
      </div>
    `;
    return;
  }

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

function setPosPreparingDeliveryStatus(message = '', type = 'info') {
  const status = document.getElementById('posPreparingDeliveryStatus');
  if (!status) return;

  status.textContent = message;
  status.classList.toggle('hidden', !message);
  status.classList.remove('bg-error/10', 'bg-secondary-container/20', 'bg-surface-container-low', 'text-error', 'text-secondary', 'text-on-surface-variant');
  if (type === 'error') {
    status.classList.add('bg-error/10', 'text-error');
  } else if (type === 'success') {
    status.classList.add('bg-secondary-container/20', 'text-secondary');
  } else {
    status.classList.add('bg-surface-container-low', 'text-on-surface-variant');
  }
}

function formatPosOrderDateTime(value) {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '-';
  return date.toLocaleString('vi-VN', {
    hour: '2-digit',
    minute: '2-digit',
    day: '2-digit',
    month: '2-digit',
  });
}

function buildPosPreparingDeliveryItemsSummary(order) {
  const items = Array.isArray(order?.items) ? order.items : [];
  if (!items.length) return 'No items listed';
  return items
    .map((item) => `${item.quantity || 0}x ${item.product_name || 'Item'}`)
    .join(', ');
}

function setPosPreparingDeliveryDropdownExpanded(expanded) {
  const content = document.getElementById('posPreparingDeliveryContent');
  const toggle = document.getElementById('posPreparingDeliveryToggle');
  const chevron = document.getElementById('posPreparingDeliveryChevron');
  if (!content || !toggle) return;

  content.classList.toggle('hidden', !expanded);
  toggle.setAttribute('aria-expanded', String(expanded));
  chevron?.classList.toggle('rotate-180', expanded);
}

function renderPosPreparingDeliveryOrders() {
  const list = document.getElementById('posPreparingDeliveryList');
  const count = document.getElementById('posPreparingDeliveryCount');
  if (!list || !count) return;

  count.textContent = String(POS_PREPARING_DELIVERY_ORDERS.length);

  if (!POS_PREPARING_DELIVERY_ORDERS.length) {
    list.innerHTML = `
      <div class="rounded-xl bg-surface-container-low p-4 text-sm font-bold text-on-surface-variant">
        No delivery orders are currently in preparation.
      </div>
    `;
    return;
  }

  list.innerHTML = POS_PREPARING_DELIVERY_ORDERS.map(
    (order) => `
      <article class="flex flex-col gap-3 rounded-xl border border-outline-variant/10 bg-surface px-4 py-3 shadow-sm lg:flex-row lg:items-center">
        <div class="grid min-w-0 flex-1 grid-cols-1 gap-3 md:grid-cols-[150px_180px_minmax(0,1fr)_minmax(0,1fr)_120px] md:items-center">
          <div class="min-w-0">
            <p class="truncate font-mono text-xs font-extrabold uppercase tracking-widest text-secondary">${escapeHtml(order.order_code || String(order.id).slice(0, 8))}</p>
            <p class="mt-1 text-xs font-bold text-on-surface-variant">${escapeHtml(formatPosOrderDateTime(order.created_at))}</p>
          </div>
          <div class="min-w-0">
            <h4 class="truncate text-sm font-extrabold text-primary">${escapeHtml(order.customer_name || 'Delivery customer')}</h4>
            <p class="mt-1 truncate text-xs font-bold text-on-surface-variant">${escapeHtml(order.customer_phone || 'No phone')}</p>
          </div>
          <p class="min-w-0 truncate text-sm text-on-surface-variant">${escapeHtml(buildPosPreparingDeliveryItemsSummary(order))}</p>
          <p class="min-w-0 truncate text-xs font-semibold text-on-surface-variant">${escapeHtml(order.delivery_address || 'No delivery address')}</p>
          <div class="text-sm font-extrabold text-secondary md:text-right">${formatVnd(order.total_amount)}</div>
        </div>
        <button class="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-secondary px-4 py-2.5 text-sm font-bold text-white transition-colors hover:bg-secondary/90 disabled:cursor-not-allowed disabled:opacity-60" data-pos-prepared-delivery-id="${escapeHtml(order.id)}" type="button">
          <span class="material-symbols-outlined text-lg">task_alt</span>
          <span class="whitespace-nowrap">Order is prepared</span>
        </button>
      </article>
    `
  ).join('');
}

function renderPosPreparingDeliveryLoading() {
  const list = document.getElementById('posPreparingDeliveryList');
  if (!list) return;

  list.innerHTML = `
    <div class="rounded-xl bg-surface-container-low p-4 text-sm font-bold text-on-surface-variant">
      Loading delivery orders...
    </div>
  `;
}

async function loadPosPreparingDeliveryOrders() {
  const list = document.getElementById('posPreparingDeliveryList');
  if (!list) return;

  setPosPreparingDeliveryStatus('Loading delivery orders in preparation...');
  renderPosPreparingDeliveryLoading();

  try {
    POS_PREPARING_DELIVERY_ORDERS = getApiListData(
      await fetchMatchaApi('/orders?order_type=delivery&status=in_progress')
    );
    renderPosPreparingDeliveryOrders();
    setPosPreparingDeliveryStatus('');
  } catch (error) {
    console.error('Failed to load preparing delivery orders:', error);
    POS_PREPARING_DELIVERY_ORDERS = [];
    renderPosPreparingDeliveryOrders();
    setPosPreparingDeliveryStatus(
      error.message || 'Cannot load delivery orders in preparation.',
      'error'
    );
  }
}

function openPosPreparedDeliveryModal(order) {
  const modal = document.getElementById('posPreparedDeliveryModal');
  const title = document.getElementById('posPreparedDeliveryModalTitle');
  const text = document.getElementById('posPreparedDeliveryModalText');
  if (!modal) return;

  if (title) {
    title.textContent = 'Delivery Order Ready';
  }
  if (text) {
    const orderCode = order?.order_code || order?.id || 'This order';
    text.textContent = `${orderCode} has been sent to Delivery Manager.`;
  }
  modal.classList.remove('hidden');
  modal.classList.add('flex');
}

function closePosPreparedDeliveryModal() {
  const modal = document.getElementById('posPreparedDeliveryModal');
  if (!modal) return;

  modal.classList.add('hidden');
  modal.classList.remove('flex');
}

async function markPosDeliveryOrderPrepared(orderId, button) {
  const order = POS_PREPARING_DELIVERY_ORDERS.find((item) => String(item.id) === String(orderId));
  if (!order) return;

  const originalButtonHtml = button?.innerHTML;
  if (button) {
    button.disabled = true;
    button.innerHTML = '<span class="material-symbols-outlined animate-spin text-lg">progress_activity</span> Sending...';
  }
  setPosPreparingDeliveryStatus(`Sending ${order.order_code || 'delivery order'} to Delivery Manager...`);

  try {
    await fetchMatchaApi(`/orders/${order.id}/ready-for-delivery`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        payment_method: order.payment_status === 'unpaid' ? 'cod' : null,
      }),
    });
    POS_PREPARING_DELIVERY_ORDERS = POS_PREPARING_DELIVERY_ORDERS.filter(
      (item) => String(item.id) !== String(order.id)
    );
    renderPosPreparingDeliveryOrders();
    setPosPreparingDeliveryStatus(`${order.order_code || 'Delivery order'} sent to Delivery Manager.`, 'success');
    openPosPreparedDeliveryModal(order);
  } catch (error) {
    console.error('Failed to mark delivery order prepared:', error);
    setPosPreparingDeliveryStatus(
      error.message || 'Cannot send this order to Delivery Manager.',
      'error'
    );
    if (button) {
      button.disabled = false;
      button.innerHTML = originalButtonHtml;
    }
  }
}

async function loadPosMenuProducts() {
  renderPosMenuState('Loading available products...');
  const products = getApiListData(await fetchMatchaApi('/products?is_available=true'));
  POS_TOPPINGS = products.filter(isToppingProduct).map(mapProductToPosTopping);
  POS_MENU_ITEMS = products.filter((product) => !isToppingProduct(product)).map(mapProductToPosItem);
  renderPosMenuItems();
  renderPosToppingOptions();
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
  const mainContent = document.getElementById('posMainContent');
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
    mainContent?.classList.remove('pr-[416px]');
    return;
  }

  const totalAmount = getCartTotal(cart);
  panel.classList.remove('hidden');
  panel.classList.add('flex');
  mainContent?.classList.add('pr-[416px]');
  count.textContent = String(cart.length);
  subtotal.textContent = formatVnd(totalAmount);
  total.textContent = formatVnd(totalAmount);
  const storedOrderCode = getStoredPosOrderCode();
  orderCode.textContent = storedOrderCode ? `Order ${storedOrderCode}` : 'Order Draft';

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

async function initPosMenu() {
  try {
    await loadPosMenuProducts();
  } catch (error) {
    console.error('Failed to load POS products:', error);
    renderPosMenuState('Cannot load products for Point of Sale. Please check the backend server.', 'error');
  }
  await loadPosPreparingDeliveryOrders();

  localStorage.removeItem(POS_CUSTOMER_STORAGE_KEY);
  updatePosOrderModeUi();
  renderPosCart();

  const menuContainer = document.getElementById('posMenuSections');
  const preparingDeliveryToggle = document.getElementById('posPreparingDeliveryToggle');
  const preparingDeliveryList = document.getElementById('posPreparingDeliveryList');
  const preparingDeliveryRefreshBtn = document.getElementById('posRefreshPreparingDeliveryBtn');
  const preparedDeliveryModal = document.getElementById('posPreparedDeliveryModal');
  const preparedDeliveryModalClose = document.getElementById('posPreparedDeliveryModalClose');
  const form = document.getElementById('posCustomizeForm');
  const closeBtn = document.getElementById('posModalCloseBtn');
  const backdrop = document.getElementById('posModalBackdrop');
  const cartItems = document.getElementById('posCartItems');
  const completeBtn = document.getElementById('posCompleteOrderBtn');
  const searchInput = document.getElementById('topbar-search');
  const orderTypeButtons = document.querySelectorAll('.pos-order-type-button');

  orderTypeButtons.forEach((button) => {
    button.addEventListener('click', () => {
      setPosOrderType(button.dataset.posOrderType);
      localStorage.removeItem(POS_INSTORE_CUSTOMER_DETAILS_STORAGE_KEY);
      localStorage.removeItem(POS_DELIVERY_DETAILS_STORAGE_KEY);
      updatePosOrderModeUi();
      renderPosCart();
    });
  });

  menuContainer?.addEventListener('click', (event) => {
    if (!(event.target instanceof Element)) return;
    const itemButton = event.target.closest('[data-pos-item-id]');
    if (!itemButton) return;
    openPosCustomizeModal(itemButton.dataset.posItemId);
  });

  preparingDeliveryToggle?.addEventListener('click', () => {
    const expanded = preparingDeliveryToggle.getAttribute('aria-expanded') === 'true';
    setPosPreparingDeliveryDropdownExpanded(!expanded);
  });

  preparingDeliveryList?.addEventListener('click', (event) => {
    if (!(event.target instanceof Element)) return;
    const preparedButton = event.target.closest('[data-pos-prepared-delivery-id]');
    if (!preparedButton) return;
    markPosDeliveryOrderPrepared(preparedButton.dataset.posPreparedDeliveryId, preparedButton);
  });

  preparingDeliveryRefreshBtn?.addEventListener('click', () => {
    loadPosPreparingDeliveryOrders();
  });

  preparedDeliveryModalClose?.addEventListener('click', closePosPreparedDeliveryModal);
  preparedDeliveryModal?.addEventListener('click', (event) => {
    if (event.target === preparedDeliveryModal) {
      closePosPreparedDeliveryModal();
    }
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
      iceLevel: formData.get('iceLevel'),
      sugarLevel: formData.get('sugarLevel'),
      toppings: selectedToppings,
      note: formData.get('note')?.trim() || '',
    };

    const cart = getPosCart();
    cart.push(cartItem);
    setPosCart(cart);
    renderPosCart();
    renderPosMenuItems();
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
    renderPosMenuItems();
  });

  completeBtn?.addEventListener('click', () => {
    if (!getPosCart().length) return;
    startNewPosCheckoutRun();
    window.location.href = 'POS_payment.html';
  });

  if (searchInput?.parentElement) {
    searchInput.value = POS_MENU_SEARCH_QUERY;
    searchInput.addEventListener('input', () => {
      POS_MENU_SEARCH_QUERY = searchInput.value || '';
      renderPosMenuItems();
    });
    searchInput.addEventListener('focus', () => {
      searchInput.parentElement.classList.add('scale-[1.02]');
    });
    searchInput.addEventListener('blur', () => {
      searchInput.parentElement.classList.remove('scale-[1.02]');
    });
  }
}

function renderPosPaymentMode() {
  const isDelivery = isPosDeliveryOrder();
  const title = document.getElementById('paymentModeTitle');
  const subtitle = document.getElementById('paymentModeSubtitle');
  const orderType = document.getElementById('paymentOrderType');
  const instoreCustomerPanel = document.getElementById('instoreCustomerPanel');
  const deliveryPanel = document.getElementById('deliveryDetailsPanel');
  const paymentOptions = document.querySelectorAll('#paymentMethodGroup label');
  const codInput = document.querySelector('input[name="payment"][value="cod"]');
  const qrInput = document.querySelector('input[name="payment"][value="qr"]');

  if (title) {
    title.textContent = isDelivery ? 'Delivery Checkout' : 'Checkout';
  }
  if (subtitle) {
    subtitle.textContent = isDelivery
      ? 'Review the phone order, confirm delivery details, and choose COD or prepaid payment.'
      : 'Review selected items, resolve customer loyalty, and choose a payment method.';
  }
  if (orderType) {
    orderType.textContent = isDelivery ? 'Delivery' : 'In-shop';
  }
  if (instoreCustomerPanel) {
    instoreCustomerPanel.classList.toggle('hidden', isDelivery);
  }
  if (deliveryPanel) {
    deliveryPanel.classList.toggle('hidden', !isDelivery);
  }

  paymentOptions.forEach((label) => {
    const input = label.querySelector('input[name="payment"]');
    if (!input) return;
    const hidden = isDelivery ? input.value === 'cash' : input.value === 'cod';
    label.classList.toggle('hidden', hidden);
    input.disabled = hidden;
  });

  if (isDelivery && codInput) {
    codInput.checked = true;
  } else if (!isDelivery && qrInput) {
    qrInput.checked = true;
  }
}

function populateInstoreCustomerForm() {
  if (isPosDeliveryOrder()) return;

  const storedDetails = getPosInstoreCustomerDetails();
  const details = {
    create_customer_profile: false,
    ...storedDetails,
    customer_name: storedDetails.customer_name || '',
    customer_phone: storedDetails.customer_phone || '',
  };

  const phoneInput = document.getElementById('instoreCustomerPhone');
  const nameInput = document.getElementById('instoreCustomerName');
  const createProfileInput = document.getElementById('instoreCreateCustomerProfile');

  if (phoneInput && phoneInput.value === '') {
    phoneInput.value = details.customer_phone || '';
  }
  if (nameInput && nameInput.value === '') {
    nameInput.value = details.customer_name || '';
  }
  if (createProfileInput) {
    createProfileInput.checked = Boolean(details.create_customer_profile);
  }

  updateInstoreCustomerNameRequirement();
}

function collectInstoreCustomerForm() {
  const details = {
    customer_phone: document.getElementById('instoreCustomerPhone')?.value.trim() || '',
    customer_name: document.getElementById('instoreCustomerName')?.value.trim() || '',
    create_customer_profile: Boolean(document.getElementById('instoreCreateCustomerProfile')?.checked),
  };
  setPosInstoreCustomerDetails(details);
  return details;
}

function normalizePhoneForLookup(value) {
  return String(value || '').replace(/\D/g, '');
}

function findCustomerByPhone(customers, phone) {
  const targetPhone = normalizePhoneForLookup(phone);
  if (!targetPhone) return null;
  return customers.find((customer) => normalizePhoneForLookup(customer.phone) === targetPhone) || null;
}

function updateInstoreCustomerNameRequirement({ customerFound = false } = {}) {
  if (isPosDeliveryOrder()) return;

  const phoneInput = document.getElementById('instoreCustomerPhone');
  const nameInput = document.getElementById('instoreCustomerName');
  if (!phoneInput || !nameInput) return;

  const hasPhone = Boolean(phoneInput.value.trim());
  nameInput.required = hasPhone && !customerFound;
}

async function lookupInstoreCustomerByPhone(phone, sequence) {
  const phoneInput = document.getElementById('instoreCustomerPhone');
  const nameInput = document.getElementById('instoreCustomerName');
  const createProfileInput = document.getElementById('instoreCreateCustomerProfile');
  if (!phoneInput || !nameInput) return;

  const normalizedPhone = normalizePhoneForLookup(phone);
  if (!normalizedPhone) {
    updateInstoreCustomerNameRequirement({ customerFound: false });
    nameInput.dataset.autofilledCustomerPhone = '';
    return;
  }

  try {
    const customers = getApiListData(
      await fetchMatchaApi(`/customers?q=${encodeURIComponent(phone.trim())}`)
    );
    if (sequence !== POS_INSTORE_CUSTOMER_LOOKUP_SEQUENCE) return;
    if (normalizePhoneForLookup(phoneInput.value) !== normalizedPhone) return;

    const customer = findCustomerByPhone(customers, phone);
    if (customer) {
      nameInput.value = customer.name || '';
      nameInput.dataset.autofilledCustomerPhone = normalizedPhone;
      if (createProfileInput) createProfileInput.checked = false;
      updateInstoreCustomerNameRequirement({ customerFound: true });
    } else {
      if (nameInput.dataset.autofilledCustomerPhone) {
        nameInput.value = '';
      }
      nameInput.dataset.autofilledCustomerPhone = '';
      updateInstoreCustomerNameRequirement({ customerFound: false });
    }

    collectInstoreCustomerForm();
  } catch (error) {
    console.warn('Cannot lookup in-shop customer by phone:', error);
    if (sequence !== POS_INSTORE_CUSTOMER_LOOKUP_SEQUENCE) return;
    updateInstoreCustomerNameRequirement({ customerFound: false });
  }
}

function scheduleInstoreCustomerLookup() {
  const phoneInput = document.getElementById('instoreCustomerPhone');
  const nameInput = document.getElementById('instoreCustomerName');
  if (!phoneInput || !nameInput) return;

  window.clearTimeout(POS_INSTORE_CUSTOMER_LOOKUP_TIMEOUT_ID);
  const phone = phoneInput.value.trim();
  const sequence = POS_INSTORE_CUSTOMER_LOOKUP_SEQUENCE + 1;
  POS_INSTORE_CUSTOMER_LOOKUP_SEQUENCE = sequence;

  if (!phone) {
    if (nameInput.dataset.autofilledCustomerPhone) {
      nameInput.value = '';
    }
    nameInput.dataset.autofilledCustomerPhone = '';
    updateInstoreCustomerNameRequirement({ customerFound: false });
    collectInstoreCustomerForm();
    return;
  }

  updateInstoreCustomerNameRequirement({ customerFound: false });
  POS_INSTORE_CUSTOMER_LOOKUP_TIMEOUT_ID = window.setTimeout(
    () => lookupInstoreCustomerByPhone(phone, sequence),
    300
  );
}

async function resolveInstoreCustomerLookupNow() {
  const phoneInput = document.getElementById('instoreCustomerPhone');
  if (!phoneInput || isPosDeliveryOrder()) return;

  window.clearTimeout(POS_INSTORE_CUSTOMER_LOOKUP_TIMEOUT_ID);
  const phone = phoneInput.value.trim();
  if (!phone) {
    updateInstoreCustomerNameRequirement({ customerFound: false });
    return;
  }

  const sequence = POS_INSTORE_CUSTOMER_LOOKUP_SEQUENCE + 1;
  POS_INSTORE_CUSTOMER_LOOKUP_SEQUENCE = sequence;
  await lookupInstoreCustomerByPhone(phone, sequence);
}

function getDeliveryMapErrorMessage(error) {
  const message = String(error?.message || '');
  const knownMessages = {
    maps_api_key_required: 'Map provider is not configured. Add a Maps API key before resolving delivery addresses.',
    geocoding_timeout: 'Map lookup timed out. Please try resolving the address again.',
    geocoding_provider_error: 'Map provider could not resolve this address right now.',
    geocoding_no_results: 'No map result found for this address. Correct the address or choose a map pin.',
    geocoding_missing_coordinates: 'The map result did not include coordinates. Try a more specific address.',
    geocoding_low_confidence: 'The map result is uncertain. Correct the address or choose a map pin.',
    geocoding_failed: 'Map lookup failed. Correct the address or try again.',
    geocoding_ambiguous_address: 'This address is ambiguous. Add more detail or choose a map pin.',
    unsupported_maps_provider: 'Configured map provider is not supported.',
  };

  return knownMessages[message] || message || 'Cannot resolve this address. Correct it or try again.';
}

function populateDeliveryDetailsForm() {
  if (!isPosDeliveryOrder()) return;

  const storedDetails = getPosDeliveryDetails();
  const details = {
    delivery_address: '',
    note: '',
    ...storedDetails,
    customer_name: storedDetails.customer_name || '',
    customer_phone: storedDetails.customer_phone || '',
  };

  const fieldMap = {
    deliveryCustomerName: 'customer_name',
    deliveryCustomerPhone: 'customer_phone',
    deliveryAddress: 'delivery_address',
    deliveryOrderNote: 'note',
  };

  Object.entries(fieldMap).forEach(([id, key]) => {
    const input = document.getElementById(id);
    if (input && input.value === '') {
      input.value = details[key] || '';
    }
  });

  updateDeliveryCustomerNameRequirement();
}

function collectDeliveryDetailsForm() {
  const details = {
    customer_name: document.getElementById('deliveryCustomerName')?.value.trim() || '',
    customer_phone: document.getElementById('deliveryCustomerPhone')?.value.trim() || '',
    delivery_address: document.getElementById('deliveryAddress')?.value.trim() || '',
    note: document.getElementById('deliveryOrderNote')?.value.trim() || '',
  };
  setPosDeliveryDetails(details);
  return details;
}

function updateDeliveryCustomerNameRequirement() {
  if (!isPosDeliveryOrder()) return;

  const nameInput = document.getElementById('deliveryCustomerName');
  if (nameInput) {
    nameInput.required = true;
  }
}

async function lookupDeliveryCustomerByPhone(phone, sequence) {
  const phoneInput = document.getElementById('deliveryCustomerPhone');
  const nameInput = document.getElementById('deliveryCustomerName');
  if (!phoneInput || !nameInput) return;

  const normalizedPhone = normalizePhoneForLookup(phone);
  if (!normalizedPhone) {
    nameInput.dataset.autofilledCustomerPhone = '';
    updateDeliveryCustomerNameRequirement();
    return;
  }

  try {
    const customers = getApiListData(
      await fetchMatchaApi(`/customers?q=${encodeURIComponent(phone.trim())}`)
    );
    if (sequence !== POS_DELIVERY_CUSTOMER_LOOKUP_SEQUENCE) return;
    if (normalizePhoneForLookup(phoneInput.value) !== normalizedPhone) return;

    const customer = findCustomerByPhone(customers, phone);
    if (customer) {
      nameInput.value = customer.name || '';
      nameInput.dataset.autofilledCustomerPhone = normalizedPhone;
    } else if (nameInput.dataset.autofilledCustomerPhone) {
      nameInput.value = '';
      nameInput.dataset.autofilledCustomerPhone = '';
    } else {
      nameInput.dataset.autofilledCustomerPhone = '';
    }

    updateDeliveryCustomerNameRequirement();
    collectDeliveryDetailsForm();
  } catch (error) {
    console.warn('Cannot lookup delivery customer by phone:', error);
    if (sequence !== POS_DELIVERY_CUSTOMER_LOOKUP_SEQUENCE) return;
    updateDeliveryCustomerNameRequirement();
  }
}

function scheduleDeliveryCustomerLookup() {
  const phoneInput = document.getElementById('deliveryCustomerPhone');
  const nameInput = document.getElementById('deliveryCustomerName');
  if (!phoneInput || !nameInput) return;

  window.clearTimeout(POS_DELIVERY_CUSTOMER_LOOKUP_TIMEOUT_ID);
  const phone = phoneInput.value.trim();
  const sequence = POS_DELIVERY_CUSTOMER_LOOKUP_SEQUENCE + 1;
  POS_DELIVERY_CUSTOMER_LOOKUP_SEQUENCE = sequence;

  if (!phone) {
    if (nameInput.dataset.autofilledCustomerPhone) {
      nameInput.value = '';
    }
    nameInput.dataset.autofilledCustomerPhone = '';
    updateDeliveryCustomerNameRequirement();
    collectDeliveryDetailsForm();
    return;
  }

  updateDeliveryCustomerNameRequirement();
  POS_DELIVERY_CUSTOMER_LOOKUP_TIMEOUT_ID = window.setTimeout(
    () => lookupDeliveryCustomerByPhone(phone, sequence),
    300
  );
}

async function resolveDeliveryCustomerLookupNow() {
  const phoneInput = document.getElementById('deliveryCustomerPhone');
  if (!phoneInput || !isPosDeliveryOrder()) return;

  window.clearTimeout(POS_DELIVERY_CUSTOMER_LOOKUP_TIMEOUT_ID);
  const phone = phoneInput.value.trim();
  if (!phone) {
    updateDeliveryCustomerNameRequirement();
    return;
  }

  const sequence = POS_DELIVERY_CUSTOMER_LOOKUP_SEQUENCE + 1;
  POS_DELIVERY_CUSTOMER_LOOKUP_SEQUENCE = sequence;
  await lookupDeliveryCustomerByPhone(phone, sequence);
}

function renderPosPaymentOrder() {
  const cart = getPosCart();
  const itemList = document.getElementById('paymentItemList');
  const emptyState = document.getElementById('paymentEmptyState');
  const subtotal = document.getElementById('paymentSubtotal');
  const total = document.getElementById('paymentTotal');
  const orderCode = document.getElementById('paymentOrderCode');
  const customerName = document.getElementById('paymentCustomerName');
  const payBtn = document.getElementById('payBtn');
  if (!itemList || !emptyState || !subtotal || !total || !payBtn) return;

  renderPosPaymentMode();
  populateInstoreCustomerForm();
  populateDeliveryDetailsForm();

  const totalAmount = getCartTotal(cart);
  if (orderCode) {
    orderCode.textContent = getPosOrderCode();
  }
  if (customerName) {
    const deliveryDetails = getPosDeliveryDetails();
    const instoreDetails = getPosInstoreCustomerDetails();
    customerName.textContent = isPosDeliveryOrder()
      ? (deliveryDetails.customer_name || 'Phone customer')
      : instoreDetails.customer_phone
        ? `${instoreDetails.customer_name || 'Phone lookup'} - ${instoreDetails.customer_phone}`
        : 'Walk-in customer';
  }
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

function setStripeQrStatus(message = '', type = 'info') {
  const status = document.getElementById('stripeQrStatus');
  if (!status) return;

  status.textContent = message;
  status.classList.remove(
    'bg-error/10',
    'bg-secondary-container/20',
    'bg-surface-container-low',
    'text-error',
    'text-secondary',
    'text-on-surface-variant'
  );

  if (type === 'error') {
    status.classList.add('bg-error/10', 'text-error');
  } else if (type === 'success') {
    status.classList.add('bg-secondary-container/20', 'text-secondary');
  } else {
    status.classList.add('bg-surface-container-low', 'text-on-surface-variant');
  }
}

function openPosStripeQrModal(checkout) {
  const modal = document.getElementById('stripeQrModal');
  const card = document.getElementById('stripeQrCard');
  const image = document.getElementById('stripeQrImage');
  const openLink = document.getElementById('stripeQrOpenLink');
  const sessionText = document.getElementById('stripeQrSessionId');
  const orderCode = document.getElementById('stripeQrOrderCode');
  const amount = document.getElementById('stripeQrAmount');
  if (!modal || !card) return;

  if (image) {
    if (checkout.qr_code_data_url) {
      image.src = checkout.qr_code_data_url;
      image.closest('.aspect-square')?.classList.remove('hidden');
    } else {
      image.removeAttribute('src');
      image.closest('.aspect-square')?.classList.add('hidden');
    }
  }
  if (openLink) {
    if (checkout.checkout_url) {
      openLink.href = checkout.checkout_url;
      openLink.classList.remove('pointer-events-none', 'opacity-50');
      openLink.removeAttribute('aria-disabled');
    } else {
      openLink.href = '#';
      openLink.classList.add('pointer-events-none', 'opacity-50');
      openLink.setAttribute('aria-disabled', 'true');
    }
  }
  if (sessionText) {
    sessionText.textContent = checkout.stripe_checkout_session_id || 'Session pending';
  }
  if (orderCode) {
    orderCode.textContent = checkout.order_code || checkout.order_id || '-';
  }
  if (amount) {
    amount.textContent = formatVnd(checkout.amount || getCartTotal(getPosCart()));
  }

  modal.classList.remove('opacity-0', 'pointer-events-none');
  modal.setAttribute('aria-hidden', 'false');
  card.classList.remove('scale-95');
  card.classList.add('scale-100');
}

function closePosStripeQrModal() {
  const modal = document.getElementById('stripeQrModal');
  const card = document.getElementById('stripeQrCard');
  if (!modal || !card) return;

  modal.classList.add('opacity-0', 'pointer-events-none');
  modal.setAttribute('aria-hidden', 'true');
  card.classList.add('scale-95');
  card.classList.remove('scale-100');
}

function stopPosStripeCheckoutPolling() {
  if (POS_STRIPE_POLL_TIMEOUT_ID !== null) {
    window.clearTimeout(POS_STRIPE_POLL_TIMEOUT_ID);
    POS_STRIPE_POLL_TIMEOUT_ID = null;
  }
  POS_STRIPE_POLL_ATTEMPTS = 0;
}

function isPosStripeCheckoutSuccessful(status) {
  return status?.payment_status === 'success' && status?.order_payment_status === 'paid';
}

function isPosStripeCheckoutTerminal(status) {
  return status?.payment_status === 'failed' || status?.payment_status === 'cancelled';
}

function getStripeSuccessTitle(status) {
  if (status?.order_status === 'completed') return 'Order Completed';
  if (status?.order_status === 'ready_for_delivery') return 'Order Ready for Delivery';
  return 'Payment Confirmed';
}

function getStripeSuccessText(status, checkout) {
  const orderCode = checkout?.order_code || status?.order_id || 'Order';
  if (status?.order_status === 'completed') {
    return `${orderCode} was paid by Stripe Checkout and completed.`;
  }
  if (status?.order_status === 'ready_for_delivery') {
    return `${orderCode} was paid and sent to Delivery Manager.`;
  }
  return `${orderCode} was paid by Stripe Checkout.`;
}

function showPosPaymentSuccess(title, message) {
  const overlay = document.getElementById('successOverlay');
  const card = document.getElementById('successCard');
  const successTitle = document.getElementById('successTitle');
  const successText = document.getElementById('successPaymentText');
  if (!overlay || !card) return;

  if (successTitle) successTitle.textContent = title;
  if (successText) successText.textContent = message;
  overlay.classList.remove('opacity-0', 'pointer-events-none');
  card.classList.remove('scale-90');
  card.classList.add('scale-100');
}

function setPayButtonWaitingForStripe() {
  const payBtn = document.getElementById('payBtn');
  if (!payBtn) return;

  payBtn.disabled = true;
  payBtn.innerHTML =
    '<span class="material-symbols-outlined animate-spin">progress_activity</span> Waiting for Stripe...';
}

async function fetchPosStripeCheckoutStatus(sessionId) {
  return await fetchMatchaApi(
    `/payments/stripe/checkout-session/${encodeURIComponent(sessionId)}/status`
  );
}

function updateStoredPosStripeCheckoutStatus(checkout, status) {
  const nextCheckout = {
    ...checkout,
    payment_status: status.payment_status,
    order_status: status.order_status,
    order_payment_status: status.order_payment_status,
    paid_at: status.paid_at || null,
    completed_at: status.completed_at || null,
    status: status.payment_status || checkout.status,
  };
  setStoredPosStripeCheckout(nextCheckout);
  return nextCheckout;
}

async function checkPosStripeCheckoutStatus(checkout, { scheduleNext = true } = {}) {
  const sessionId = checkout?.stripe_checkout_session_id;
  if (!sessionId) return null;

  try {
    const status = await fetchPosStripeCheckoutStatus(sessionId);
    const nextCheckout = updateStoredPosStripeCheckoutStatus(checkout, status);

    if (isPosStripeCheckoutSuccessful(status)) {
      stopPosStripeCheckoutPolling();
      setStripeQrStatus('Payment confirmed by Stripe webhook.', 'success');
      setPosPaymentStatus('Payment confirmed by Stripe.', 'success');
      closePosStripeQrModal();
      clearStoredPosStripeCheckout();
      showPosPaymentSuccess(
        getStripeSuccessTitle(status),
        getStripeSuccessText(status, nextCheckout)
      );
      return status;
    }

    if (isPosStripeCheckoutTerminal(status)) {
      stopPosStripeCheckoutPolling();
      setStripeQrStatus('Stripe marked this checkout as failed or cancelled.', 'error');
      setPosPaymentStatus('Stripe payment failed or was cancelled.', 'error');
      return status;
    }

    setStripeQrStatus('Waiting for Stripe webhook confirmation...');
    setPosPaymentStatus('Waiting for Stripe payment confirmation...');

    if (scheduleNext) {
      POS_STRIPE_POLL_ATTEMPTS += 1;
      if (POS_STRIPE_POLL_ATTEMPTS < POS_STRIPE_POLL_MAX_ATTEMPTS) {
        POS_STRIPE_POLL_TIMEOUT_ID = window.setTimeout(
          () => checkPosStripeCheckoutStatus(nextCheckout),
          POS_STRIPE_POLL_INTERVAL_MS
        );
      } else {
        setStripeQrStatus('Still waiting for payment confirmation. Check again when Stripe finishes processing.');
        setPosPaymentStatus('Still waiting for Stripe confirmation.');
      }
    }

    return status;
  } catch (error) {
    console.error('Failed to check Stripe checkout status:', error);
    setStripeQrStatus(error.message || 'Cannot check Stripe status right now.', 'error');
    setPosPaymentStatus(error.message || 'Cannot check Stripe status right now.', 'error');
    if (scheduleNext) {
      POS_STRIPE_POLL_ATTEMPTS += 1;
      if (POS_STRIPE_POLL_ATTEMPTS < POS_STRIPE_POLL_MAX_ATTEMPTS) {
        POS_STRIPE_POLL_TIMEOUT_ID = window.setTimeout(
          () => checkPosStripeCheckoutStatus(checkout),
          POS_STRIPE_POLL_INTERVAL_MS
        );
      }
    }
    return null;
  }
}

function startPosStripeCheckoutPolling(checkout, { immediate = true } = {}) {
  stopPosStripeCheckoutPolling();
  setPayButtonWaitingForStripe();
  openPosStripeQrModal(checkout);
  setStripeQrStatus('Waiting for Stripe payment confirmation...');
  setPosPaymentStatus('Waiting for Stripe payment confirmation...');

  if (immediate) {
    checkPosStripeCheckoutStatus(checkout);
  } else {
    POS_STRIPE_POLL_TIMEOUT_ID = window.setTimeout(
      () => checkPosStripeCheckoutStatus(checkout),
      POS_STRIPE_POLL_INTERVAL_MS
    );
  }
}

function handlePosStripeCheckoutRedirect() {
  const params = new URLSearchParams(window.location.search);
  const stripeState = params.get('stripe');
  const sessionId = params.get('session_id');
  if (!stripeState) return false;

  const stored = getStoredPosStripeCheckout();
  const checkout = sessionId
    ? getPosStripeCheckoutFromRedirect(sessionId)
    : stored;

  if (stripeState === 'success' && sessionId) {
    openPosStripeQrModal(checkout);
    setStripeQrStatus('Stripe returned successfully. Confirming webhook status...');
    startPosStripeCheckoutPolling(checkout);
  } else if (stripeState === 'cancelled') {
    if (checkout?.stripe_checkout_session_id) {
      openPosStripeQrModal(checkout);
      setStripeQrStatus('Stripe checkout was cancelled in the browser. The session may still be pending.', 'error');
      startPosStripeCheckoutPolling(checkout);
    } else {
      setPosPaymentStatus('Stripe checkout was cancelled.', 'error');
    }
  }

  window.history.replaceState({}, document.title, window.location.pathname);
  return true;
}

function initPosPayment() {
  renderPosPaymentOrder();

  const payBtn = document.getElementById('payBtn');
  const newOrderBtn = document.getElementById('newOrderBtn');
  const paymentOrderCode = document.getElementById('paymentOrderCode');
  const stripeQrCloseBtn = document.getElementById('stripeQrCloseBtn');
  const stripeQrCheckStatusBtn = document.getElementById('stripeQrCheckStatusBtn');
  const instoreCustomerPhoneInput = document.getElementById('instoreCustomerPhone');
  const instoreCustomerNameInput = document.getElementById('instoreCustomerName');
  const instoreCreateCustomerProfileInput = document.getElementById('instoreCreateCustomerProfile');
  const deliveryCustomerPhoneInput = document.getElementById('deliveryCustomerPhone');
  const deliveryCustomerNameInput = document.getElementById('deliveryCustomerName');
  const deliveryAddressInput = document.getElementById('deliveryAddress');
  const deliveryOrderNoteInput = document.getElementById('deliveryOrderNote');
  const originalPayBtnHtml = payBtn?.innerHTML;
  const handledStripeRedirect = handlePosStripeCheckoutRedirect();

  if (!handledStripeRedirect) {
    const storedCheckout = getStoredPosStripeCheckout();
    if (canReuseStoredPosStripeCheckout(storedCheckout)) {
      startPosStripeCheckoutPolling(storedCheckout, { immediate: false });
    }
  }

  stripeQrCloseBtn?.addEventListener('click', closePosStripeQrModal);
  instoreCustomerPhoneInput?.addEventListener('input', scheduleInstoreCustomerLookup);
  instoreCustomerPhoneInput?.addEventListener('blur', scheduleInstoreCustomerLookup);
  instoreCustomerNameInput?.addEventListener('input', () => {
    instoreCustomerNameInput.dataset.autofilledCustomerPhone = '';
    collectInstoreCustomerForm();
  });
  instoreCreateCustomerProfileInput?.addEventListener('change', collectInstoreCustomerForm);
  if (instoreCustomerPhoneInput?.value.trim()) {
    scheduleInstoreCustomerLookup();
  }
  deliveryCustomerPhoneInput?.addEventListener('input', scheduleDeliveryCustomerLookup);
  deliveryCustomerPhoneInput?.addEventListener('blur', scheduleDeliveryCustomerLookup);
  deliveryCustomerNameInput?.addEventListener('input', () => {
    deliveryCustomerNameInput.dataset.autofilledCustomerPhone = '';
    collectDeliveryDetailsForm();
  });
  deliveryAddressInput?.addEventListener('input', collectDeliveryDetailsForm);
  deliveryOrderNoteInput?.addEventListener('input', collectDeliveryDetailsForm);
  if (deliveryCustomerPhoneInput?.value.trim()) {
    scheduleDeliveryCustomerLookup();
  }
  stripeQrCheckStatusBtn?.addEventListener('click', async () => {
    const checkout = getStoredPosStripeCheckout();
    if (!checkout?.stripe_checkout_session_id) return;
    stripeQrCheckStatusBtn.disabled = true;
    stripeQrCheckStatusBtn.innerHTML =
      '<span class="material-symbols-outlined animate-spin">progress_activity</span> Checking...';
    await checkPosStripeCheckoutStatus(checkout, { scheduleNext: false });
    stripeQrCheckStatusBtn.disabled = false;
    stripeQrCheckStatusBtn.innerHTML =
      '<span class="material-symbols-outlined">sync</span> Check Status';
  });

  payBtn?.addEventListener('click', async () => {
    const selectedPayment = document.querySelector('input[name="payment"]:checked')?.value;
    if (!getPosCart().length) return;

    const isDelivery = isPosDeliveryOrder();
    if (isDelivery) {
      await resolveDeliveryCustomerLookupNow();
    } else {
      await resolveInstoreCustomerLookupNow();
    }
    const deliveryDetails = isDelivery ? collectDeliveryDetailsForm() : null;
    const instoreCustomerDetails = isDelivery ? null : collectInstoreCustomerForm();

    if (isPosStripeQrPayment(selectedPayment)) {
      const storedCheckout = getStoredPosStripeCheckout();
      if (canReuseStoredPosStripeCheckout(storedCheckout)) {
        startPosStripeCheckoutPolling(storedCheckout);
        return;
      }
    }

    payBtn.disabled = true;
    payBtn.innerHTML =
      '<span class="material-symbols-outlined animate-spin">progress_activity</span> Processing...';
    setPosPaymentStatus(isDelivery ? 'Creating delivery order...' : 'Creating in-shop order...');

    try {
      const completedOrder = await submitPosOrder(
        selectedPayment,
        { deliveryDetails, instoreCustomerDetails },
        setPosPaymentStatus
      );

      if (completedOrder?.requiresStripeCheckout) {
        const checkout = buildPosStripeCheckoutState(
          completedOrder.stripeSession,
          completedOrder.order
        );
        setStoredPosStripeCheckout(checkout);
        if (paymentOrderCode) {
          paymentOrderCode.textContent = checkout.order_code || checkout.order_id;
        }
        startPosStripeCheckoutPolling(checkout, { immediate: false });
        return;
      }

      const orderCode = completedOrder.order_code || completedOrder.id || getPosOrderCode();
      localStorage.setItem(POS_ORDER_CODE_STORAGE_KEY, orderCode);

      if (paymentOrderCode) {
        paymentOrderCode.textContent = orderCode;
      }
      setPosPaymentStatus(
        isDelivery
          ? 'Delivery order created and kept in preparation.'
          : 'Order completed successfully.',
        'success'
      );
      showPosPaymentSuccess(
        isDelivery ? 'Order In Preparation' : 'Order Completed',
        isDelivery
          ? `${orderCode} delivery order created with ${getPosPaymentLabel(selectedPayment)} and kept in preparation.`
          : `${orderCode} completed successfully by ${getPosPaymentLabel(selectedPayment)}.`
      );
    } catch (error) {
      console.error('Failed to complete POS order:', error);
      setPosPaymentStatus(
        isDelivery
          ? getDeliveryMapErrorMessage(error)
          : error.message || 'Cannot complete order. Please check the backend server.',
        'error'
      );
      payBtn.disabled = false;
      payBtn.innerHTML = originalPayBtnHtml;
    }
  });

  newOrderBtn?.addEventListener('click', () => {
    localStorage.removeItem(POS_CART_STORAGE_KEY);
    localStorage.removeItem(POS_ORDER_CODE_STORAGE_KEY);
    localStorage.removeItem(POS_CUSTOMER_STORAGE_KEY);
    localStorage.removeItem(POS_DELIVERY_DETAILS_STORAGE_KEY);
    localStorage.removeItem(POS_INSTORE_CUSTOMER_DETAILS_STORAGE_KEY);
    localStorage.removeItem(POS_ORDER_TYPE_STORAGE_KEY);
    localStorage.removeItem(POS_CHECKOUT_RUN_STORAGE_KEY);
    clearStoredPosStripeCheckout();
    stopPosStripeCheckoutPolling();
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
  const tripList = document.getElementById('shipper-trip-list');
  const stopList = document.getElementById('shipper-stop-list');
  const statusMessage = document.getElementById('shipper-status');
  const tripFilter = document.getElementById('shipper-trip-filter');
  const refreshButton = document.getElementById('shipper-refresh');
  const startTripButton = document.getElementById('shipper-start-trip');
  const trackLocationButton = document.getElementById('shipper-track-location');
  const sendLocationButton = document.getElementById('shipper-send-location');
  const useCurrentLocationButton = document.getElementById('shipper-use-current-location');
  const latitudeInput = document.getElementById('shipper-latitude');
  const longitudeInput = document.getElementById('shipper-longitude');
  const locationLast = document.getElementById('shipper-location-last');
  const stopModal = document.getElementById('shipper-stop-modal');
  const stopForm = document.getElementById('shipper-stop-form');
  const stopFormStatus = document.getElementById('shipper-stop-form-status');
  const codField = document.getElementById('shipper-cod-field');
  const failedField = document.getElementById('shipper-failed-field');
  const codCollectedInput = document.getElementById('shipper-cod-collected');
  const failedReasonInput = document.getElementById('shipper-failed-reason');
  const stopNoteInput = document.getElementById('shipper-stop-note');
  const routeMapPanel = document.getElementById('shipper-route-map-panel');
  const searchInput = document.getElementById('topbar-search');
  const performanceMonthInput = document.getElementById('shipper-performance-month');
  const performanceRefreshButton = document.getElementById('shipper-performance-refresh');
  const performanceStatus = document.getElementById('shipper-performance-status');
  const hasPerformancePanel = Boolean(document.getElementById('shipper-perf-total-trips'));

  if (!tripList || !stopList) return;

  const state = {
    trips: [],
    selectedTrip: null,
    selectedStop: null,
    performance: null,
    stopAction: 'delivered',
    isSendingLocation: false,
    isTrackingLocation: false,
    locationTimerId: null,
    searchQuery: '',
  };
  const SHIPPER_LOCATION_UPDATE_INTERVAL_SECONDS = 30;

  const getCurrentShipperMonth = () => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  };

  if (hasPerformancePanel && performanceMonthInput && !performanceMonthInput.value) {
    performanceMonthInput.value = getCurrentShipperMonth();
  }

  const tripStatusMeta = {
    pending_dispatch: { label: 'Pending dispatch', className: 'bg-tertiary-fixed text-on-tertiary-fixed-variant' },
    assigned: { label: 'Assigned', className: 'bg-secondary-container/30 text-secondary' },
    in_transit: { label: 'In transit', className: 'bg-primary/10 text-primary' },
    completed: { label: 'Completed', className: 'bg-surface-container-high text-on-surface' },
    reconciled: { label: 'Reconciled', className: 'bg-secondary text-on-secondary' },
    cancelled: { label: 'Cancelled', className: 'bg-error-container/30 text-error' },
  };

  const stopStatusMeta = {
    assigned: { label: 'Assigned', className: 'bg-secondary-container/30 text-secondary' },
    delivered: { label: 'Delivered', className: 'bg-secondary text-on-secondary' },
    failed: { label: 'Failed', className: 'bg-error-container/40 text-error' },
  };

  const setText = (id, value) => {
    const element = document.getElementById(id);
    if (element) element.textContent = value;
  };

  const setStatus = (message = '', type = 'info') => {
    if (!statusMessage) return;
    statusMessage.textContent = message;
    statusMessage.className = `rounded-xl px-4 py-3 text-sm font-bold ${
      type === 'error'
        ? 'bg-error-container/30 text-error'
        : type === 'success'
          ? 'bg-secondary-container/30 text-secondary'
          : 'bg-surface-container-low text-on-surface-variant'
    }`;
    statusMessage.classList.toggle('hidden', !message);
  };

  const setStopFormStatus = (message = '', type = 'info') => {
    if (!stopFormStatus) return;
    stopFormStatus.textContent = message;
    stopFormStatus.className = `text-sm font-bold ${
      type === 'error' ? 'text-error' : type === 'success' ? 'text-secondary' : 'text-on-surface-variant'
    }`;
    stopFormStatus.classList.toggle('hidden', !message);
  };

  const setPerformanceStatus = (message = '', type = 'info') => {
    if (!performanceStatus) return;
    performanceStatus.textContent = message;
    performanceStatus.className = `rounded-xl px-4 py-3 text-sm font-bold ${
      type === 'error'
        ? 'bg-error-container/30 text-error'
        : type === 'success'
          ? 'bg-secondary-container/30 text-secondary'
          : 'bg-surface-container-low text-on-surface-variant'
    }`;
    performanceStatus.classList.toggle('hidden', !message);
  };

  const getBadge = (value, source = tripStatusMeta) => {
    const key = String(value || '').toLowerCase();
    const meta = source[key] || { label: formatShipperLabel(key), className: 'bg-surface-container-high text-on-surface-variant' };
    return `<span class="inline-flex rounded-full px-3 py-1 text-xs font-bold ${meta.className}">${escapeHtml(meta.label)}</span>`;
  };

  const formatShipperLabel = (value) => String(value || '-')
    .split('_')
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ') || '-';

  const formatShipperDateTime = (value) => {
    if (!value) return '-';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    return date.toLocaleString('vi-VN', {
      hour: '2-digit',
      minute: '2-digit',
      day: '2-digit',
      month: '2-digit',
    });
  };

  const formatShipperNumber = (value, digits = 0) => Number(value || 0).toLocaleString('vi-VN', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });

  const formatShipperPerformanceMinutes = (value) => {
    const minutes = Number(value || 0);
    if (!minutes) return '0 min';
    if (minutes < 60) return `${formatShipperNumber(minutes, 2)} min`;
    const hours = Math.floor(minutes / 60);
    const remainder = Math.round(minutes % 60);
    return `${hours}h ${remainder}m`;
  };

  const buildShipperMapUrl = (latitude, longitude) => {
    if (latitude === null || latitude === undefined || longitude === null || longitude === undefined) return '';
    return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${latitude},${longitude}`)}`;
  };

  const SHOP_ROUTE_POINT = window.MATCHA_SHOP_ROUTE_POINT;
  const shipperRouteMaps = new Map();

  const isValidRouteCoordinate = (latitude, longitude) => Number.isFinite(Number(latitude)) && Number.isFinite(Number(longitude));

  const getRouteMapStatusClass = (status) => {
    if (status === 'delivered') return 'delivered';
    if (status === 'failed') return 'failed';
    return 'assigned';
  };

  const getTripRoutePoints = (trip) => {
    const allStops = [...(trip?.orders || [])].sort((first, second) => Number(first.stop_order || 0) - Number(second.stop_order || 0));
    const stops = allStops
      .filter((stop) => isValidRouteCoordinate(stop.delivery_latitude, stop.delivery_longitude))
      .map((stop) => ({
        kind: 'stop',
        label: `${stop.stop_order}. ${stop.order_code}`,
        subtitle: stop.delivery_address || 'Delivery stop',
        stopOrder: stop.stop_order,
        status: getRouteMapStatusClass(stop.status),
        latitude: Number(stop.delivery_latitude),
        longitude: Number(stop.delivery_longitude),
      }));

    return {
      missingCount: allStops.length - stops.length,
      points: [
        { ...SHOP_ROUTE_POINT, kind: 'store', status: 'store', stopOrder: 'S', subtitle: 'Shop pickup point' },
        ...stops,
      ],
      stopCount: allStops.length,
      mappedStopCount: stops.length,
    };
  };

  const buildRouteMapHtml = (trip, mapId = 'shipper-route-leaflet-map', buttonId = 'shipper-route-map-expand') => {
    if (!trip) {
      return '<p class="rounded-xl bg-surface-container-low p-4 text-sm font-bold text-on-surface-variant">Select a trip to see the route map.</p>';
    }

    const route = getTripRoutePoints(trip);
    const missingCount = route.missingCount;

    if (!route.mappedStopCount) {
      return '<p class="rounded-xl bg-surface-container-low p-4 text-sm font-bold text-on-surface-variant">No mapped stops are available for this trip.</p>';
    }

    return `
      <div class="trip-map-shell">
        <div id="${mapId}" class="trip-map-canvas" role="button" tabindex="0" aria-label="Open Vietnam route map"></div>
        <button id="${buttonId}" class="trip-map-expand" type="button">
          <span class="material-symbols-outlined text-[16px]">open_in_full</span>
          Open large map
        </button>
      </div>
      <div class="delivery-route-map__legend">
        <span>${route.mappedStopCount}/${route.stopCount} mapped stops</span>
        <span class="delivery-route-map__legend-items">
          <span class="delivery-route-map__legend-item"><span class="delivery-route-map__legend-dot delivery-route-map__legend-dot--store"></span>Store</span>
          <span class="delivery-route-map__legend-item"><span class="delivery-route-map__legend-dot"></span>Pending</span>
          <span class="delivery-route-map__legend-item"><span class="delivery-route-map__legend-dot delivery-route-map__legend-dot--done"></span>Delivered</span>
          <span class="delivery-route-map__legend-item"><span class="delivery-route-map__legend-dot delivery-route-map__legend-dot--failed"></span>Failed</span>
        </span>
      </div>
      ${missingCount ? `<p class="delivery-route-map__notice">${missingCount} stop${missingCount === 1 ? '' : 's'} missing coordinates.</p>` : ''}
    `;
  };

  const createRouteIcon = (point) => {
    const iconClass = point.kind === 'store' ? 'store' : point.status;
    return L.divIcon({
      className: '',
      html: `<div class="trip-map-marker trip-map-marker--${iconClass}"><span>${escapeHtml(point.stopOrder)}</span></div>`,
      iconAnchor: [17, 34],
      iconSize: [34, 34],
      popupAnchor: [0, -32],
    });
  };

  const renderTripLeafletMap = (trip, mapId, { large = false } = {}) => {
    const container = document.getElementById(mapId);
    if (!container) return;
    if (!window.L) {
      container.innerHTML = '<div class="trip-map-fallback">Cannot load the Vietnam map library. Check your network connection.</div>';
      return;
    }

    if (shipperRouteMaps.has(mapId)) {
      shipperRouteMaps.get(mapId).remove();
      shipperRouteMaps.delete(mapId);
    }

    const points = getTripRoutePoints(trip).points;
    const map = L.map(mapId, {
      attributionControl: large,
      dragging: large,
      scrollWheelZoom: large,
      doubleClickZoom: large,
      boxZoom: large,
      keyboard: large,
      tap: large,
      zoomControl: large,
    });
    shipperRouteMaps.set(mapId, map);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(map);

    points.forEach((point) => {
      L.marker([point.latitude, point.longitude], { icon: createRouteIcon(point) })
        .bindPopup(`<b>${escapeHtml(point.label)}</b><br>${escapeHtml(point.subtitle || '')}<br>${point.latitude.toFixed(6)}, ${point.longitude.toFixed(6)}`)
        .addTo(map);
    });

    points.slice(0, -1).forEach((point, index) => {
      const destination = points[index + 1];
      const color = destination.status === 'failed'
        ? '#ba1a1a'
        : destination.status === 'assigned'
          ? '#7a8478'
          : '#496648';
      L.polyline(
        [[point.latitude, point.longitude], [destination.latitude, destination.longitude]],
        {
          color,
          dashArray: destination.status === 'assigned' ? '8 10' : null,
          opacity: destination.status === 'assigned' ? 0.55 : 0.95,
          weight: large ? 5 : 4,
        }
      ).addTo(map);
    });

    const bounds = L.latLngBounds(points.map((point) => [point.latitude, point.longitude]));
    if (points.length === 1) {
      map.setView([points[0].latitude, points[0].longitude], 12);
    } else {
      map.fitBounds(bounds.pad(0.24), { maxZoom: large ? 15 : 13 });
    }

    if (!large) {
      map.on('click', () => openRouteMapModal(trip));
    }

    setTimeout(() => map.invalidateSize(), 0);
  };

  const ensureRouteMapModal = () => {
    let modal = document.getElementById('shipper-route-map-modal');
    if (modal) return modal;

    document.body.insertAdjacentHTML('beforeend', `
      <div id="shipper-route-map-modal" class="trip-map-modal" aria-hidden="true">
        <div class="trip-map-modal__dialog" role="dialog" aria-modal="true" aria-labelledby="shipper-route-map-modal-title">
          <div class="trip-map-modal__header">
            <div>
              <h2 id="shipper-route-map-modal-title" class="trip-map-modal__title">Vietnam Route Map</h2>
              <p id="shipper-route-map-modal-subtitle" class="trip-map-modal__subtitle"></p>
            </div>
            <button class="trip-map-modal__close" type="button" data-close-trip-map>
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
          <div id="shipper-route-map-modal-canvas" class="trip-map-canvas trip-map-canvas--large"></div>
        </div>
      </div>
    `);

    modal = document.getElementById('shipper-route-map-modal');
    modal.addEventListener('click', (event) => {
      if (event.target === modal || event.target.closest('[data-close-trip-map]')) {
        modal.classList.remove('is-open');
        modal.setAttribute('aria-hidden', 'true');
      }
    });
    return modal;
  };

  const openRouteMapModal = (trip) => {
    const modal = ensureRouteMapModal();
    document.getElementById('shipper-route-map-modal-title').textContent = `${trip?.trip_code || 'Trip'} - Vietnam Route Map`;
    document.getElementById('shipper-route-map-modal-subtitle').textContent = 'Store and delivery stops are plotted by latitude and longitude.';
    modal.classList.add('is-open');
    modal.setAttribute('aria-hidden', 'false');
    setTimeout(() => renderTripLeafletMap(trip, 'shipper-route-map-modal-canvas', { large: true }), 0);
  };

  const renderRouteMap = () => {
    if (!routeMapPanel) return;
    routeMapPanel.innerHTML = buildRouteMapHtml(state.selectedTrip);
    renderTripLeafletMap(state.selectedTrip, 'shipper-route-leaflet-map');
    document.getElementById('shipper-route-map-expand')?.addEventListener('click', () => openRouteMapModal(state.selectedTrip));
    document.getElementById('shipper-route-leaflet-map')?.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        openRouteMapModal(state.selectedTrip);
      }
    });
  };

  const hasCapturedLocation = () => latitudeInput?.value !== '' && longitudeInput?.value !== '';
  const isSelectedTripInTransit = () => state.selectedTrip?.status === 'in_transit';

  const formatShipperRoute = (trip) => {
    if (!trip) return '-';
    const distance = trip.total_distance_km !== null && trip.total_distance_km !== undefined
      ? `${Number(trip.total_distance_km).toFixed(1)} km`
      : '';
    const duration = trip.total_duration_minutes !== null && trip.total_duration_minutes !== undefined
      ? `${Number(trip.total_duration_minutes)} min`
      : '';
    return [distance, duration].filter(Boolean).join(' / ') || '-';
  };

  const formatShipperLeg = (stop) => {
    const distance = stop.distance_from_previous_km !== null && stop.distance_from_previous_km !== undefined
      ? `${Number(stop.distance_from_previous_km).toFixed(1)} km`
      : '';
    const duration = stop.duration_from_previous_minutes !== null && stop.duration_from_previous_minutes !== undefined
      ? `${Number(stop.duration_from_previous_minutes)} min`
      : '';
    return [distance, duration].filter(Boolean).join(' / ');
  };

  const getStartTripButtonContent = (trip) => {
    const status = trip?.status;
    if (status === 'assigned') {
      return {
        icon: 'play_arrow',
        label: 'Start Trip',
      };
    }
    if (status === 'in_transit') {
      return {
        icon: 'local_shipping',
        label: 'In Transit',
      };
    }
    if (status === 'completed') {
      return {
        icon: 'task_alt',
        label: 'Completed',
      };
    }
    if (status === 'reconciled') {
      return {
        icon: 'verified',
        label: 'Reconciled',
      };
    }
    return {
      icon: 'block',
      label: trip ? formatShipperLabel(status) : 'Select Trip',
    };
  };

  const stopLocationTracking = () => {
    if (state.locationTimerId) {
      clearInterval(state.locationTimerId);
      state.locationTimerId = null;
    }
    state.isTrackingLocation = false;
  };

  const renderLocationStatus = () => {
    if (!locationLast) return;
    const latestLocation = state.selectedTrip?.latest_location;
    const latestMapUrl = latestLocation
      ? buildShipperMapUrl(latestLocation.latitude, latestLocation.longitude)
      : '';
    const capturedMapUrl = hasCapturedLocation()
      ? buildShipperMapUrl(latitudeInput.value, longitudeInput.value)
      : '';

    const trackingLabel = isSelectedTripInTransit()
      ? state.isTrackingLocation
        ? `Auto updates every ${SHIPPER_LOCATION_UPDATE_INTERVAL_SECONDS}s`
        : 'Auto tracking is off'
      : 'Tracking starts after the trip is in transit';

    if (latestLocation) {
      locationLast.innerHTML = `
        <div class="flex flex-wrap items-center justify-between gap-3">
          <span>${escapeHtml(trackingLabel)}. Last sent ${escapeHtml(formatShipperDateTime(latestLocation.recorded_at))}</span>
          <a class="inline-flex items-center gap-1 rounded-full bg-surface-container-high px-3 py-2 text-xs font-bold text-primary hover:bg-surface-container-highest" href="${latestMapUrl}" target="_blank" rel="noreferrer">
            <span class="material-symbols-outlined text-[16px]">map</span>
            Open map
          </a>
        </div>
      `;
      return;
    }

    if (hasCapturedLocation()) {
      locationLast.innerHTML = `
        <div class="flex flex-wrap items-center justify-between gap-3">
          <span>${escapeHtml(trackingLabel)}. Device location captured.</span>
          <a class="inline-flex items-center gap-1 rounded-full bg-surface-container-high px-3 py-2 text-xs font-bold text-primary hover:bg-surface-container-highest" href="${capturedMapUrl}" target="_blank" rel="noreferrer">
            <span class="material-symbols-outlined text-[16px]">map</span>
            Preview
          </a>
        </div>
      `;
      return;
    }

    locationLast.textContent = trackingLabel;
  };

  const getVisibleTrips = () => {
    const filter = tripFilter?.value || 'active';
    const query = state.searchQuery.trim().toLowerCase();
    const filterTrip = (trip) => {
      if (!query) return true;
      const searchableValues = [
        trip.trip_code,
        trip.id,
        trip.status,
        trip.expected_cod_amount,
        trip.total_distance_km,
        trip.total_duration_minutes,
        ...(trip.orders || []).flatMap((stop) => [
          stop.order_code,
          stop.delivery_address,
          stop.customer_name,
          stop.customer_phone,
          stop.status,
          stop.amount_to_collect,
        ]),
      ];
      return searchableValues.some((value) => String(value ?? '').toLowerCase().includes(query));
    };
    if (filter === 'all') return state.trips.filter(filterTrip);
    if (filter === 'active') {
      return state.trips.filter((trip) => ['assigned', 'in_transit'].includes(trip.status)).filter(filterTrip);
    }
    return state.trips.filter((trip) => trip.status === filter).filter(filterTrip);
  };

  const getStops = () => state.selectedTrip?.orders || [];

  const syncSelectedTripIntoList = () => {
    if (!state.selectedTrip) return;
    const index = state.trips.findIndex((trip) => trip.id === state.selectedTrip.id);
    if (index >= 0) {
      state.trips[index] = {
        ...state.trips[index],
        ...state.selectedTrip,
      };
    }
  };

  const getVisibleStops = () => {
    const stops = getStops();
    const query = state.searchQuery.trim().toLowerCase();
    if (!query) return stops;
    return stops.filter((stop) => [
      stop.order_code,
      stop.delivery_address,
      stop.customer_name,
      stop.customer_phone,
      stop.status,
      stop.payment_method,
      stop.payment_status,
      stop.amount_to_collect,
      stop.cod_collected,
      stop.note,
      stop.failed_reason,
    ].some((value) => String(value ?? '').toLowerCase().includes(query)));
  };

  const renderStats = () => {
    const activeTrips = state.trips.filter((trip) => ['assigned', 'in_transit'].includes(trip.status));
    const stopsLeft = getStops().filter((stop) => stop.status === 'assigned').length;
    const selectedOpenCod = getStops()
      .filter((stop) => stop.status === 'assigned')
      .reduce((sum, stop) => sum + Number(stop.amount_to_collect || 0), 0);
    const codToCollect = state.selectedTrip?.orders
      ? selectedOpenCod
      : activeTrips.reduce((sum, trip) => sum + Number(trip.expected_cod_amount || 0), 0);

    setText('shipper-stat-assigned', state.trips.filter((trip) => trip.status === 'assigned').length);
    setText('shipper-stat-transit', state.trips.filter((trip) => trip.status === 'in_transit').length);
    setText('shipper-stat-stops', stopsLeft);
    setText('shipper-stat-cod', formatVnd(codToCollect));
  };

  const renderPerformance = () => {
    const performance = state.performance || {};
    const deliveredOrders = Number(performance.delivered_orders || 0);
    const failedOrders = Number(performance.failed_orders || 0);

    setText('shipper-perf-total-trips', formatShipperNumber(performance.total_trips || 0));
    setText('shipper-perf-completed-trips', formatShipperNumber(performance.completed_trips || 0));
    setText('shipper-perf-success-rate', `${formatShipperNumber(performance.success_rate || 0, 2)}%`);
    setText('shipper-perf-orders', `${formatShipperNumber(deliveredOrders)} / ${formatShipperNumber(failedOrders)}`);
    setText('shipper-perf-distance', `${formatShipperNumber(performance.planned_distance_km || 0, 3)} km`);
    setText('shipper-perf-average', formatShipperPerformanceMinutes(performance.average_delivery_minutes || 0));
  };

  const renderTrips = () => {
    const visibleTrips = getVisibleTrips();
    setText('shipper-trip-count', `${visibleTrips.length}`);

    if (!visibleTrips.length) {
      tripList.innerHTML = `<p class="rounded-xl bg-surface-container-low p-4 text-sm font-bold text-on-surface-variant">${state.searchQuery ? 'No trips match your search.' : 'No trips found for this filter.'}</p>`;
      return;
    }

    tripList.innerHTML = visibleTrips.map((trip) => {
      const isSelected = state.selectedTrip?.id === trip.id;
      return `
        <button class="shipper-trip-card w-full rounded-xl border p-4 text-left transition-colors ${
          isSelected
            ? 'border-secondary bg-secondary-container/20'
            : 'border-outline-variant/30 bg-surface-container-low hover:bg-surface-container-high'
        }" type="button" data-trip-id="${escapeHtml(trip.id)}">
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <p class="break-words text-sm font-bold text-primary">${escapeHtml(trip.trip_code)}</p>
              <p class="mt-1 font-mono text-[11px] text-on-surface-variant">${escapeHtml(String(trip.id || '').slice(0, 8))}</p>
            </div>
            ${getBadge(trip.status)}
          </div>
          <div class="mt-4 flex items-center justify-between gap-3 text-xs text-on-surface-variant">
            <span>${escapeHtml(formatShipperDateTime(trip.created_at))}</span>
            <b class="text-primary">${escapeHtml(formatVnd(trip.expected_cod_amount))}</b>
          </div>
        </button>
      `;
    }).join('');
  };

  const renderCurrentStop = () => {
    const currentStop = getStops().find((stop) => stop.status === 'assigned');
    const container = document.getElementById('shipper-current-stop');
    if (!container) return;

    if (!state.selectedTrip) {
      container.innerHTML = 'Select a stop to prepare delivery update.';
      return;
    }

    if (!currentStop) {
      container.innerHTML = 'No assigned stops left on this trip.';
      return;
    }

    container.innerHTML = `
      <p class="text-xs font-bold uppercase tracking-widest text-on-primary/70">Next stop</p>
      <p class="mt-2 text-base font-bold text-on-primary">${escapeHtml(currentStop.stop_order)}. ${escapeHtml(currentStop.order_code)}</p>
      <p class="mt-2 text-sm text-on-primary/80">${escapeHtml(currentStop.delivery_address || '-')}</p>
      <p class="mt-3 text-sm font-bold text-on-primary">${escapeHtml(formatVnd(currentStop.amount_to_collect))} COD</p>
    `;
  };

  const renderTripDetail = () => {
    const trip = state.selectedTrip;
    const canStart = trip?.status === 'assigned';
    const canSendLocation = trip?.status === 'in_transit';
    const canUseLocation = Boolean(canSendLocation && navigator.geolocation);
    if (!canSendLocation && state.isTrackingLocation) stopLocationTracking();

    setText('shipper-trip-title', trip ? trip.trip_code : 'Trip Detail');
    setText('shipper-trip-subtitle', trip ? `Created ${formatShipperDateTime(trip.created_at)}` : 'Select an assigned trip to start shipping.');
    setText('shipper-trip-cod', formatVnd(trip?.expected_cod_amount || 0));
    setText('shipper-trip-started', trip?.started_at ? formatShipperDateTime(trip.started_at) : 'Not started');
    setText('shipper-trip-route', formatShipperRoute(trip));
    setText('shipper-stop-count', `${getStops().length} stop${getStops().length === 1 ? '' : 's'}`);

    const statusContainer = document.getElementById('shipper-trip-status');
    if (statusContainer) statusContainer.innerHTML = trip ? getBadge(trip.status) : '-';

    if (startTripButton) {
      const buttonContent = getStartTripButtonContent(trip);
      startTripButton.disabled = !canStart;
      startTripButton.innerHTML = `
        <span class="material-symbols-outlined text-[18px]">${buttonContent.icon}</span>
        ${escapeHtml(buttonContent.label)}
      `;
    }
    if (trackLocationButton) {
      trackLocationButton.disabled = !canUseLocation;
      trackLocationButton.innerHTML = `
        <span class="material-symbols-outlined text-[18px]">${state.isTrackingLocation ? 'location_on' : 'location_searching'}</span>
        ${state.isTrackingLocation ? 'Tracking On' : 'Enable Tracking'}
      `;
    }
    if (useCurrentLocationButton) useCurrentLocationButton.disabled = !canUseLocation;
    if (sendLocationButton) sendLocationButton.disabled = !canSendLocation || !hasCapturedLocation() || state.isSendingLocation;

    renderStops();
    renderCurrentStop();
    renderLocationStatus();
    renderRouteMap();
    renderStats();
  };

  const renderStops = () => {
    const trip = state.selectedTrip;
    const allStops = getStops();
    const stops = getVisibleStops();

    if (!trip) {
      stopList.innerHTML = '<p class="rounded-xl bg-surface-container-low p-4 text-sm font-bold text-on-surface-variant">Select a trip to see stops.</p>';
      return;
    }

    if (!allStops.length) {
      stopList.innerHTML = '<p class="rounded-xl bg-surface-container-low p-4 text-sm font-bold text-on-surface-variant">No stops found for this trip.</p>';
      return;
    }

    if (!stops.length) {
      stopList.innerHTML = '<p class="rounded-xl bg-surface-container-low p-4 text-sm font-bold text-on-surface-variant">No stops match your search.</p>';
      return;
    }

    const canUpdateStops = trip.status === 'in_transit';
    stopList.innerHTML = stops.map((stop) => {
      const canUpdate = canUpdateStops && stop.status === 'assigned';
      const mapsUrl = buildShipperMapUrl(stop.delivery_latitude, stop.delivery_longitude);
      const legSummary = formatShipperLeg(stop);
      return `
        <article class="rounded-xl border border-outline-variant/30 bg-surface-container-low p-4">
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div class="min-w-0 flex-1">
              <div class="flex flex-wrap items-center gap-2">
                <p class="font-bold text-primary">${escapeHtml(stop.stop_order)}. ${escapeHtml(stop.order_code)}</p>
                ${getBadge(stop.status, stopStatusMeta)}
              </div>
              <p class="mt-2 line-clamp-2 text-sm text-on-surface-variant">${escapeHtml(stop.delivery_address || '-')}</p>
              <div class="mt-3 grid grid-cols-1 gap-2 text-xs text-on-surface-variant sm:grid-cols-3">
                <span><b class="text-on-surface">Customer:</b> ${escapeHtml(stop.customer_name || 'Phone customer')}</span>
                <span><b class="text-on-surface">Phone:</b> ${escapeHtml(stop.customer_phone || '-')}</span>
                <span><b class="text-on-surface">COD:</b> ${escapeHtml(formatVnd(stop.amount_to_collect))}</span>
              </div>
              ${legSummary ? `<p class="mt-2 text-xs font-bold text-on-surface-variant">Leg from previous stop: ${escapeHtml(legSummary)}</p>` : ''}
              ${stop.failed_reason ? `<p class="mt-3 text-xs font-bold text-error">${escapeHtml(stop.failed_reason)}</p>` : ''}
              ${stop.note ? `<p class="mt-2 text-xs text-on-surface-variant">${escapeHtml(stop.note)}</p>` : ''}
            </div>
            <div class="flex shrink-0 flex-wrap justify-end gap-2">
              ${mapsUrl ? `
                <a class="inline-flex items-center gap-1 rounded-full bg-surface-container-high px-3 py-2 text-xs font-bold text-primary hover:bg-surface-container-highest" href="${mapsUrl}" target="_blank" rel="noreferrer">
                  <span class="material-symbols-outlined text-[16px]">directions</span>
                  Route
                </a>
              ` : ''}
              <button class="shipper-stop-delivered inline-flex items-center gap-1 rounded-full bg-secondary px-3 py-2 text-xs font-bold text-on-secondary hover:bg-secondary/90 disabled:cursor-not-allowed disabled:opacity-50" type="button" data-order-id="${escapeHtml(stop.order_id)}" ${canUpdate ? '' : 'disabled'}>
                <span class="material-symbols-outlined text-[16px]">done_all</span>
                Delivered
              </button>
              <button class="shipper-stop-failed inline-flex items-center gap-1 rounded-full bg-error-container/40 px-3 py-2 text-xs font-bold text-error hover:bg-error-container/60 disabled:cursor-not-allowed disabled:opacity-50" type="button" data-order-id="${escapeHtml(stop.order_id)}" ${canUpdate ? '' : 'disabled'}>
                <span class="material-symbols-outlined text-[16px]">report</span>
                Failed
              </button>
            </div>
          </div>
          <div class="mt-3 flex flex-wrap items-center justify-between gap-2 text-xs text-on-surface-variant">
            <span>Payment: ${escapeHtml(formatShipperLabel(stop.payment_method || stop.payment_status))}</span>
            <span>Collected: ${escapeHtml(formatVnd(stop.cod_collected))}</span>
          </div>
        </article>
      `;
    }).join('');
  };

  const loadTrips = async ({ keepSelectedTrip = true } = {}) => {
    setStatus('Loading assigned trips...');
    try {
      state.trips = getApiListData(await fetchMatchaApi('/shipper/trips'));
      const selectedId = state.selectedTrip?.id;
      if (keepSelectedTrip && selectedId && state.trips.some((trip) => trip.id === selectedId)) {
        state.selectedTrip = await fetchMatchaApi(`/shipper/trips/${encodeURIComponent(selectedId)}`);
      } else if (state.trips.length) {
        const firstActive = state.trips.find((trip) => ['assigned', 'in_transit'].includes(trip.status)) || state.trips[0];
        state.selectedTrip = await fetchMatchaApi(`/shipper/trips/${encodeURIComponent(firstActive.id)}`);
      } else {
        state.selectedTrip = null;
      }
      syncSelectedTripIntoList();
      if (!isSelectedTripInTransit()) stopLocationTracking();
      renderTrips();
      renderTripDetail();
      setStatus(`Loaded ${state.trips.length} assigned trip${state.trips.length === 1 ? '' : 's'}.`, 'success');
    } catch (error) {
      console.error('Failed to load shipper trips:', error);
      state.trips = [];
      state.selectedTrip = null;
      renderTrips();
      renderTripDetail();
      setStatus(error.message || 'Cannot load assigned trips. Please sign in as a shipper.', 'error');
    }
  };

  const loadShipperPerformance = async ({ silent = false } = {}) => {
    const month = performanceMonthInput?.value || getCurrentShipperMonth();
    if (!silent) setPerformanceStatus('Loading monthly performance...');

    try {
      state.performance = await fetchMatchaApi(`/shipper/performance?month=${encodeURIComponent(month)}`);
      renderPerformance();
      setPerformanceStatus(
        silent ? '' : `Performance loaded for ${state.performance.month || month}.`,
        silent ? 'info' : 'success'
      );
    } catch (error) {
      console.error('Failed to load shipper performance:', error);
      state.performance = null;
      renderPerformance();
      setPerformanceStatus(error.message || 'Cannot load monthly performance.', 'error');
    }
  };

  const selectTrip = async (tripId) => {
    if (!tripId) return;
    setStatus('Loading trip detail...');
    try {
      state.selectedTrip = await fetchMatchaApi(`/shipper/trips/${encodeURIComponent(tripId)}`);
      syncSelectedTripIntoList();
      if (!isSelectedTripInTransit()) stopLocationTracking();
      renderTrips();
      renderTripDetail();
      setStatus('Trip detail loaded.', 'success');
    } catch (error) {
      console.error('Failed to load shipper trip detail:', error);
      setStatus(error.message || 'Cannot load trip detail.', 'error');
    }
  };

  const startSelectedTrip = async () => {
    if (!state.selectedTrip) return;
    startTripButton.disabled = true;
    setStatus('Starting trip...');
    try {
      state.selectedTrip = await fetchMatchaApi(`/shipper/trips/${encodeURIComponent(state.selectedTrip.id)}/start`, {
        method: 'POST',
      });
      await loadTrips({ keepSelectedTrip: true });
      setStatus('Trip started. Requesting device location...', 'success');
      startLocationTracking();
    } catch (error) {
      console.error('Failed to start shipper trip:', error);
      renderTripDetail();
      setStatus(error.message || 'Cannot start trip.', 'error');
    }
  };

  const updateLocation = async () => {
    if (!state.selectedTrip) return;
    if (!isSelectedTripInTransit()) {
      setStatus('Start the assigned trip before sending location.', 'error');
      renderTripDetail();
      return;
    }
    if (state.isSendingLocation) return;
    const latitude = latitudeInput?.value;
    const longitude = longitudeInput?.value;
    if (latitude === '' || longitude === '') {
      setStatus('Capture the device location before sending it.', 'error');
      return;
    }

    state.isSendingLocation = true;
    sendLocationButton.disabled = true;
    setStatus('Updating location...');
    try {
      await fetchMatchaApi(`/shipper/trips/${encodeURIComponent(state.selectedTrip.id)}/location`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          latitude: Number(latitude),
          longitude: Number(longitude),
        }),
      });
      if (state.selectedTrip) {
        state.selectedTrip = await fetchMatchaApi(`/shipper/trips/${encodeURIComponent(state.selectedTrip.id)}`);
      }
      setStatus('Location updated.', 'success');
    } catch (error) {
      console.error('Failed to update shipper location:', error);
      setStatus(error.message || 'Cannot update location.', 'error');
    } finally {
      state.isSendingLocation = false;
      if (!isSelectedTripInTransit()) stopLocationTracking();
      renderTripDetail();
    }
  };

  const captureCurrentLocation = ({ sendAfterCapture = false } = {}) => {
    if (!isSelectedTripInTransit()) {
      setStatus('Start the assigned trip before capturing delivery location.', 'error');
      renderTripDetail();
      return;
    }
    if (!navigator.geolocation) {
      setStatus('Browser geolocation is not available.', 'error');
      return;
    }
    setStatus('Requesting device location...');
    useCurrentLocationButton.disabled = true;
    navigator.geolocation.getCurrentPosition(
      (position) => {
        if (latitudeInput) latitudeInput.value = position.coords.latitude.toFixed(7);
        if (longitudeInput) longitudeInput.value = position.coords.longitude.toFixed(7);
        renderLocationStatus();
        renderTripDetail();
        if (sendAfterCapture) {
          updateLocation();
          return;
        }
        setStatus('Device location captured. Send it when the trip is in transit.', 'success');
      },
      (error) => {
        stopLocationTracking();
        setStatus(error.message || 'Cannot get current location.', 'error');
        renderTripDetail();
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
    setTimeout(() => {
      useCurrentLocationButton.disabled = false;
    }, 1000);
  };

  const startLocationTracking = () => {
    if (!isSelectedTripInTransit()) {
      setStatus('Start the assigned trip before enabling location tracking.', 'error');
      renderTripDetail();
      return;
    }
    if (!navigator.geolocation) {
      setStatus('Browser geolocation is not available.', 'error');
      return;
    }
    if (state.locationTimerId) clearInterval(state.locationTimerId);
    state.isTrackingLocation = true;
    renderTripDetail();
    captureCurrentLocation({ sendAfterCapture: true });
    state.locationTimerId = setInterval(() => {
      if (!isSelectedTripInTransit()) {
        stopLocationTracking();
        renderTripDetail();
        return;
      }
      captureCurrentLocation({ sendAfterCapture: true });
    }, SHIPPER_LOCATION_UPDATE_INTERVAL_SECONDS * 1000);
  };

  const openStopModal = (orderId, action) => {
    const stop = getStops().find((item) => item.order_id === orderId);
    if (!stop || !stopModal) return;

    state.selectedStop = stop;
    state.stopAction = action;
    setStopFormStatus('');

    const isDelivered = action === 'delivered';
    document.getElementById('shipper-stop-modal-title').textContent = isDelivered ? 'Mark Delivered' : 'Mark Failed';
    document.getElementById('shipper-stop-modal-subtitle').textContent = `${stop.stop_order}. ${stop.order_code}`;
    codField?.classList.toggle('hidden', !isDelivered);
    failedField?.classList.toggle('hidden', isDelivered);
    if (codCollectedInput) codCollectedInput.value = isDelivered ? Number(stop.amount_to_collect || 0) : '';
    if (failedReasonInput) failedReasonInput.value = '';
    if (stopNoteInput) stopNoteInput.value = '';

    stopModal.classList.remove('hidden');
    stopModal.classList.add('flex');
    setTimeout(() => {
      (isDelivered ? codCollectedInput : failedReasonInput)?.focus();
    }, 0);
  };

  const closeStopModal = () => {
    stopModal?.classList.add('hidden');
    stopModal?.classList.remove('flex');
    state.selectedStop = null;
    state.stopAction = 'delivered';
    stopForm?.reset();
    setStopFormStatus('');
  };

  const submitStopUpdate = async (event) => {
    event.preventDefault();
    if (!state.selectedTrip || !state.selectedStop) return;

    const isDelivered = state.stopAction === 'delivered';
    if (state.selectedTrip.status !== 'in_transit') {
      setStopFormStatus('Trip must be in transit before updating stops.', 'error');
      return;
    }
    if (!isDelivered && !failedReasonInput?.value.trim()) {
      setStopFormStatus('Failed reason is required.', 'error');
      return;
    }
    if (isDelivered) {
      const expectedCod = Number(state.selectedStop.amount_to_collect || 0);
      const collectedCod = Number(codCollectedInput?.value || 0);
      if (collectedCod !== expectedCod) {
        setStopFormStatus(`COD collected must be ${formatVnd(expectedCod)} for this stop.`, 'error');
        return;
      }
    }

    const endpoint = isDelivered
      ? `/shipper/trips/${encodeURIComponent(state.selectedTrip.id)}/orders/${encodeURIComponent(state.selectedStop.order_id)}/delivered`
      : `/shipper/trips/${encodeURIComponent(state.selectedTrip.id)}/orders/${encodeURIComponent(state.selectedStop.order_id)}/failed`;
    const payload = isDelivered
      ? {
          cod_collected: Number(codCollectedInput?.value || 0),
          note: stopNoteInput?.value.trim() || null,
        }
      : {
          failed_reason: failedReasonInput?.value.trim(),
          note: stopNoteInput?.value.trim() || null,
        };

    const submitButton = document.getElementById('shipper-submit-stop');
    const originalText = submitButton?.textContent || 'Save Update';
    if (submitButton) {
      submitButton.disabled = true;
      submitButton.textContent = 'Saving...';
    }
    setStopFormStatus('Saving stop update...');
    try {
      state.selectedTrip = await fetchMatchaApi(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      closeStopModal();
      await loadTrips({ keepSelectedTrip: true });
      if (hasPerformancePanel) await loadShipperPerformance({ silent: true });
      setStatus(isDelivered ? 'Order marked delivered.' : 'Order marked failed.', 'success');
    } catch (error) {
      console.error('Failed to update shipper stop:', error);
      setStopFormStatus(error.message || 'Cannot update stop.', 'error');
    } finally {
      if (submitButton) {
        submitButton.disabled = false;
        submitButton.textContent = originalText;
      }
    }
  };

  tripList.addEventListener('click', (event) => {
    const card = event.target.closest('.shipper-trip-card');
    if (card) selectTrip(card.dataset.tripId);
  });

  stopList.addEventListener('click', (event) => {
    const deliveredButton = event.target.closest('.shipper-stop-delivered');
    const failedButton = event.target.closest('.shipper-stop-failed');
    if (deliveredButton) openStopModal(deliveredButton.dataset.orderId, 'delivered');
    if (failedButton) openStopModal(failedButton.dataset.orderId, 'failed');
  });

  refreshButton?.addEventListener('click', () => {
    loadTrips();
    if (hasPerformancePanel) loadShipperPerformance();
  });
  performanceRefreshButton?.addEventListener('click', () => loadShipperPerformance());
  performanceMonthInput?.addEventListener('change', () => loadShipperPerformance());
  searchInput?.addEventListener('input', () => {
    state.searchQuery = searchInput.value || '';
    renderTrips();
    renderStops();
  });
  searchInput?.addEventListener('focus', () => {
    searchInput.parentElement?.classList.add('scale-[1.02]');
  });
  searchInput?.addEventListener('blur', () => {
    searchInput.parentElement?.classList.remove('scale-[1.02]');
  });
  tripFilter?.addEventListener('change', () => {
    renderTrips();
    renderStats();
  });
  startTripButton?.addEventListener('click', startSelectedTrip);
  trackLocationButton?.addEventListener('click', startLocationTracking);
  sendLocationButton?.addEventListener('click', updateLocation);
  useCurrentLocationButton?.addEventListener('click', () => captureCurrentLocation());
  stopForm?.addEventListener('submit', submitStopUpdate);
  document.getElementById('shipper-close-stop-modal')?.addEventListener('click', closeStopModal);
  document.getElementById('shipper-cancel-stop-modal')?.addEventListener('click', closeStopModal);
  stopModal?.addEventListener('click', (event) => {
    if (event.target === stopModal) closeStopModal();
  });

  if (hasPerformancePanel) renderPerformance();
  loadTrips();
  if (hasPerformancePanel) loadShipperPerformance();
}

const FINANCE_STATE = {
  month: '',
  summary: null,
  expenses: [],
  records: [],
  recordPage: 1,
  expensePage: 1,
  searchQuery: '',
};

const FINANCE_RECORD_PAGE_SIZE = 5;
const FINANCE_EXPENSE_PAGE_SIZE = 5;

function getCurrentFinanceMonth() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
}

function getFinanceMonthStart(month) {
  return `${month || getCurrentFinanceMonth()}-01`;
}

function formatFinanceMonth(value) {
  if (!value) return '-';
  const date = new Date(`${String(value).slice(0, 7)}-01T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
}

function formatFinanceDate(value) {
  if (!value) return '-';
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function formatFinanceLabel(value) {
  return String(value || '')
    .split('_')
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ') || '-';
}

function setFinanceText(id, value) {
  const element = document.getElementById(id);
  if (element) element.textContent = value;
}

function setFinanceStatus(message = '', type = 'info') {
  const status = document.getElementById('finance-status');
  if (!status) return;

  status.textContent = message;
  status.classList.toggle('hidden', !message);
  status.classList.remove('text-error', 'text-secondary', 'text-on-surface-variant');
  status.classList.add(
    type === 'error' ? 'text-error' : type === 'success' ? 'text-secondary' : 'text-on-surface-variant'
  );
}

function setFinanceFormStatus(message = '', type = 'info') {
  const status = document.getElementById('finance-form-status');
  if (!status) return;

  status.textContent = message;
  status.classList.toggle('hidden', !message);
  status.classList.remove('text-error', 'text-secondary', 'text-on-surface-variant');
  status.classList.add(
    type === 'error' ? 'text-error' : type === 'success' ? 'text-secondary' : 'text-on-surface-variant'
  );
}

function renderFinanceSummary(summary) {
  setFinanceText('finance-revenue', formatVnd(summary?.revenue || 0));
  setFinanceText('finance-material-cost', formatVnd(summary?.material_cost || 0));
  setFinanceText('finance-operating-expense', formatVnd(summary?.operating_expense || 0));
  setFinanceText('finance-net-profit', formatVnd(summary?.net_profit || 0));
}

function normalizeFinanceSearchText(value) {
  return String(value ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();
}

function matchesFinanceSearch(values) {
  const query = normalizeFinanceSearchText(FINANCE_STATE.searchQuery);
  if (!query) return true;
  return values.some((value) => normalizeFinanceSearchText(value).includes(query));
}

function getVisibleFinanceExpenses() {
  return FINANCE_STATE.expenses.filter((expense) => matchesFinanceSearch([
    expense.id,
    expense.category,
    formatFinanceLabel(expense.category),
    expense.description,
    expense.amount,
    formatVnd(expense.amount),
    expense.expense_month,
    formatFinanceMonth(expense.expense_month),
    expense.invoice_photo_url,
  ]));
}

function getVisibleFinanceRecords() {
  return FINANCE_STATE.records.filter((record) => matchesFinanceSearch([
    record.id,
    record.record_type,
    formatFinanceLabel(record.record_type),
    record.source_type,
    formatFinanceLabel(record.source_type),
    record.source_id,
    record.amount,
    formatVnd(record.amount),
    record.record_date,
    formatFinanceDate(record.record_date),
    record.locked ? 'locked' : 'open',
  ]));
}

function getFinanceExpenseTotalPages(expenseCount) {
  return Math.max(1, Math.ceil(expenseCount / FINANCE_EXPENSE_PAGE_SIZE));
}

function updateFinanceExpensePagination(expenseCount) {
  const pagination = document.getElementById('finance-expense-pagination');
  const previousButton = document.getElementById('finance-expense-prev');
  const nextButton = document.getElementById('finance-expense-next');
  const pageLabel = document.getElementById('finance-expense-page-label');
  if (!pagination || !previousButton || !nextButton || !pageLabel) return;

  const totalPages = getFinanceExpenseTotalPages(expenseCount);
  const hasMultiplePages = totalPages > 1;
  pagination.classList.toggle('hidden', !hasMultiplePages);
  pagination.classList.toggle('flex', hasMultiplePages);
  previousButton.disabled = FINANCE_STATE.expensePage <= 1;
  nextButton.disabled = FINANCE_STATE.expensePage >= totalPages;
  pageLabel.textContent = `Page ${FINANCE_STATE.expensePage} of ${totalPages}`;
}

function renderFinanceExpenses(expenses) {
  const body = document.getElementById('finance-expenses-body');
  if (!body) return;

  if (!expenses.length) {
    FINANCE_STATE.expensePage = 1;
    setFinanceText('finance-expense-count', 'Showing 0 of 0 expenses');
    updateFinanceExpensePagination(0);
    body.innerHTML = `
      <tr>
        <td class="px-6 py-8 text-center text-sm font-bold text-on-surface-variant" colspan="6">${FINANCE_STATE.searchQuery ? 'No expenses match your search.' : 'No expenses found for this month.'}</td>
      </tr>
    `;
    return;
  }

  const totalPages = getFinanceExpenseTotalPages(expenses.length);
  FINANCE_STATE.expensePage = Math.min(Math.max(FINANCE_STATE.expensePage, 1), totalPages);
  const startIndex = (FINANCE_STATE.expensePage - 1) * FINANCE_EXPENSE_PAGE_SIZE;
  const pageExpenses = expenses.slice(startIndex, startIndex + FINANCE_EXPENSE_PAGE_SIZE);
  const endIndex = startIndex + pageExpenses.length;
  setFinanceText(
    'finance-expense-count',
    `Showing ${startIndex + 1}-${endIndex} of ${expenses.length} expense${expenses.length === 1 ? '' : 's'}`
  );
  updateFinanceExpensePagination(expenses.length);

  body.innerHTML = pageExpenses
    .map(
      (expense) => `
        <tr>
          <td class="font-mono text-xs font-bold text-secondary">${escapeHtml(String(expense.id).slice(0, 8))}</td>
          <td><span class="text-xs font-extrabold uppercase text-primary">${escapeHtml(formatFinanceLabel(expense.category))}</span></td>
          <td><b class="text-primary">${escapeHtml(expense.description)}</b></td>
          <td class="text-right font-extrabold text-primary">${formatVnd(expense.amount)}</td>
          <td>${escapeHtml(formatFinanceMonth(expense.expense_month))}</td>
          <td>${
            expense.invoice_photo_url
              ? `<a class="font-bold text-secondary hover:text-primary" href="${escapeHtml(expense.invoice_photo_url)}" target="_blank" rel="noreferrer">Open</a>`
              : '<span class="text-on-surface-variant">-</span>'
          }</td>
        </tr>
      `
    )
    .join('');
}

function getFinanceRecordTotalPages(recordCount) {
  return Math.max(1, Math.ceil(recordCount / FINANCE_RECORD_PAGE_SIZE));
}

function updateFinanceRecordPagination(recordCount) {
  const pagination = document.getElementById('finance-record-pagination');
  const previousButton = document.getElementById('finance-record-prev');
  const nextButton = document.getElementById('finance-record-next');
  const pageLabel = document.getElementById('finance-record-page-label');
  if (!pagination || !previousButton || !nextButton || !pageLabel) return;

  const totalPages = getFinanceRecordTotalPages(recordCount);
  const hasMultiplePages = totalPages > 1;
  pagination.classList.toggle('hidden', !hasMultiplePages);
  pagination.classList.toggle('flex', hasMultiplePages);
  previousButton.disabled = FINANCE_STATE.recordPage <= 1;
  nextButton.disabled = FINANCE_STATE.recordPage >= totalPages;
  pageLabel.textContent = `Page ${FINANCE_STATE.recordPage} of ${totalPages}`;
}

function renderFinanceRecords(records) {
  const body = document.getElementById('finance-records-body');
  if (!body) return;

  if (!records.length) {
    FINANCE_STATE.recordPage = 1;
    setFinanceText('finance-record-count', 'Showing 0 of 0 records');
    updateFinanceRecordPagination(0);
    body.innerHTML = `
      <tr>
        <td class="px-6 py-8 text-center text-sm font-bold text-on-surface-variant" colspan="6">${FINANCE_STATE.searchQuery ? 'No financial records match your search.' : 'No financial records found for this month.'}</td>
      </tr>
    `;
    return;
  }

  const totalPages = getFinanceRecordTotalPages(records.length);
  FINANCE_STATE.recordPage = Math.min(Math.max(FINANCE_STATE.recordPage, 1), totalPages);
  const startIndex = (FINANCE_STATE.recordPage - 1) * FINANCE_RECORD_PAGE_SIZE;
  const pageRecords = records.slice(startIndex, startIndex + FINANCE_RECORD_PAGE_SIZE);
  const endIndex = startIndex + pageRecords.length;
  setFinanceText(
    'finance-record-count',
    `Showing ${startIndex + 1}-${endIndex} of ${records.length} record${records.length === 1 ? '' : 's'}`
  );
  updateFinanceRecordPagination(records.length);

  body.innerHTML = pageRecords
    .map(
      (record) => `
        <tr>
          <td class="font-mono text-xs font-bold text-secondary">${escapeHtml(String(record.id).slice(0, 8))}</td>
          <td><span class="text-xs font-extrabold uppercase text-secondary">${escapeHtml(formatFinanceLabel(record.record_type))}</span></td>
          <td>
            <b class="text-primary">${escapeHtml(formatFinanceLabel(record.source_type))}</b>
            <p class="font-mono text-xs text-on-surface-variant">${escapeHtml(String(record.source_id).slice(0, 8))}</p>
          </td>
          <td class="text-right font-extrabold text-primary">${formatVnd(record.amount)}</td>
          <td>${escapeHtml(formatFinanceDate(record.record_date))}</td>
          <td><span class="rounded-full ${record.locked ? 'bg-primary/10 text-primary' : 'bg-surface-container text-on-surface-variant'} px-3 py-1 text-xs font-extrabold uppercase">${record.locked ? 'Locked' : 'Open'}</span></td>
        </tr>
      `
    )
    .join('');
}

function renderFinanceBreakdown(expenses) {
  const list = document.getElementById('finance-breakdown-list');
  if (!list) return;

  const totals = expenses.reduce((acc, expense) => {
    const category = expense.category || 'other';
    acc[category] = (acc[category] || 0) + Number(expense.amount || 0);
    return acc;
  }, {});
  const total = Object.values(totals).reduce((sum, value) => sum + value, 0);
  setFinanceText('finance-breakdown-total', formatVnd(total));

  if (!total) {
    list.innerHTML = `<p class="text-sm font-bold text-on-surface-variant">${FINANCE_STATE.searchQuery ? 'No expense categories match your search.' : 'No expenses for this month.'}</p>`;
    return;
  }

  list.innerHTML = Object.entries(totals)
    .sort((a, b) => b[1] - a[1])
    .map(([category, amount]) => {
      const percent = Math.round((amount / total) * 100);
      return `
        <div>
          <div class="mb-2 flex items-center justify-between text-sm">
            <span class="font-bold text-on-surface-variant">${escapeHtml(formatFinanceLabel(category))}</span>
            <b class="text-primary">${percent}%</b>
          </div>
          <div class="h-2 rounded-full bg-surface-container">
            <div class="h-2 rounded-full bg-secondary" style="width: ${percent}%"></div>
          </div>
          <p class="mt-1 text-xs font-bold text-primary">${formatVnd(amount)}</p>
        </div>
      `;
    })
    .join('');
}

function renderFinancePage() {
  const visibleExpenses = getVisibleFinanceExpenses();
  const visibleRecords = getVisibleFinanceRecords();
  renderFinanceSummary(FINANCE_STATE.summary || {});
  renderFinanceExpenses(visibleExpenses);
  renderFinanceRecords(visibleRecords);
  renderFinanceBreakdown(visibleExpenses);
}

function renderFinanceLoading() {
  setFinanceStatus('Loading finance data...');
  renderFinanceSummary({});
  setFinanceText('finance-expense-count', 'Loading expenses...');
  FINANCE_STATE.expensePage = 1;
  updateFinanceExpensePagination(0);
  setFinanceText('finance-record-count', 'Loading records...');
  FINANCE_STATE.recordPage = 1;
  updateFinanceRecordPagination(0);
  const expenseBody = document.getElementById('finance-expenses-body');
  const recordBody = document.getElementById('finance-records-body');
  if (expenseBody) {
    expenseBody.innerHTML = `
      <tr>
        <td class="px-6 py-8 text-center text-sm font-bold text-on-surface-variant" colspan="6">Loading expenses...</td>
      </tr>
    `;
  }
  if (recordBody) {
    recordBody.innerHTML = `
      <tr>
        <td class="px-6 py-8 text-center text-sm font-bold text-on-surface-variant" colspan="6">Loading records...</td>
      </tr>
    `;
  }
}

async function loadFinanceData(month = FINANCE_STATE.month) {
  const selectedMonth = month || getCurrentFinanceMonth();
  FINANCE_STATE.month = selectedMonth;
  renderFinanceLoading();

  try {
    const [summary, expenses, records] = await Promise.all([
      fetchMatchaApi(`/finance/summary?month=${encodeURIComponent(selectedMonth)}`),
      fetchMatchaApi(`/finance/expenses?month=${encodeURIComponent(selectedMonth)}`),
      fetchMatchaApi(`/finance/records?month=${encodeURIComponent(selectedMonth)}`),
    ]);
    FINANCE_STATE.summary = summary || {};
    FINANCE_STATE.expenses = getApiListData(expenses);
    FINANCE_STATE.records = getApiListData(records);
    FINANCE_STATE.expensePage = 1;
    FINANCE_STATE.recordPage = 1;
    renderFinancePage();
    setFinanceStatus(`Loaded ${formatFinanceMonth(selectedMonth)} finance data.`, 'success');
  } catch (error) {
    console.error('Failed to load finance data:', error);
    FINANCE_STATE.summary = {};
    FINANCE_STATE.expenses = [];
    FINANCE_STATE.records = [];
    FINANCE_STATE.expensePage = 1;
    FINANCE_STATE.recordPage = 1;
    renderFinancePage();
    setFinanceStatus(error.message || 'Cannot load finance data. Please check the backend server.', 'error');
  }
}

function downloadFinanceCsv() {
  const rows = [
    ['section', 'id', 'type_or_category', 'source_or_description', 'amount', 'date'],
    ...FINANCE_STATE.records.map((record) => [
      'record',
      record.id,
      record.record_type,
      record.source_type,
      record.amount,
      record.record_date,
    ]),
    ...FINANCE_STATE.expenses.map((expense) => [
      'expense',
      expense.id,
      expense.category,
      expense.description,
      expense.amount,
      expense.expense_month,
    ]),
  ];
  const csv = rows
    .map((row) => row.map((value) => `"${String(value ?? '').replace(/"/g, '""')}"`).join(','))
    .join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `finance-${FINANCE_STATE.month || getCurrentFinanceMonth()}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

async function initFinancialManagement() {
  const periodInput = document.getElementById('finance-period');
  const expenseDateInput = document.getElementById('finance-expense-date');
  const refreshBtn = document.getElementById('finance-refresh-btn');
  const expenseForm = document.getElementById('finance-expense-form');
  const saveExpenseBtn = document.getElementById('finance-save-expense-btn');
  const exportBtn = document.getElementById('finance-export-btn');
  const recordPrevBtn = document.getElementById('finance-record-prev');
  const recordNextBtn = document.getElementById('finance-record-next');
  const expensePrevBtn = document.getElementById('finance-expense-prev');
  const expenseNextBtn = document.getElementById('finance-expense-next');
  const searchInput = document.getElementById('topbar-search');

  const initialMonth = getCurrentFinanceMonth();
  if (periodInput) periodInput.value = initialMonth;
  if (expenseDateInput) expenseDateInput.value = getFinanceMonthStart(initialMonth);

  periodInput?.addEventListener('change', () => {
    const month = periodInput.value || getCurrentFinanceMonth();
    if (expenseDateInput) expenseDateInput.value = getFinanceMonthStart(month);
  });

  refreshBtn?.addEventListener('click', () => {
    loadFinanceData(periodInput?.value || getCurrentFinanceMonth());
  });

  expenseForm?.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!expenseForm.reportValidity()) return;

    const formData = new FormData(expenseForm);
    const payload = {
      category: String(formData.get('category') || '').trim(),
      description: String(formData.get('description') || '').trim(),
      amount: Number(formData.get('amount')),
      expense_month: String(formData.get('expense_month') || ''),
      invoice_photo_url: String(formData.get('invoice_photo_url') || '').trim() || null,
    };

    saveExpenseBtn.disabled = true;
    setFinanceFormStatus('Saving expense...');
    try {
      await fetchMatchaApi('/finance/expenses', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });
      expenseForm.reset();
      const month = periodInput?.value || getCurrentFinanceMonth();
      if (expenseDateInput) expenseDateInput.value = getFinanceMonthStart(month);
      setFinanceFormStatus('Expense created successfully.', 'success');
      await loadFinanceData(month);
    } catch (error) {
      console.error('Failed to create expense:', error);
      setFinanceFormStatus(error.message || 'Cannot create expense.', 'error');
    } finally {
      saveExpenseBtn.disabled = false;
    }
  });

  exportBtn?.addEventListener('click', downloadFinanceCsv);
  searchInput?.addEventListener('input', () => {
    FINANCE_STATE.searchQuery = searchInput.value || '';
    FINANCE_STATE.expensePage = 1;
    FINANCE_STATE.recordPage = 1;
    renderFinancePage();
  });
  searchInput?.addEventListener('focus', () => {
    searchInput.parentElement?.classList.add('scale-[1.02]');
  });
  searchInput?.addEventListener('blur', () => {
    searchInput.parentElement?.classList.remove('scale-[1.02]');
  });
  expensePrevBtn?.addEventListener('click', () => {
    if (FINANCE_STATE.expensePage <= 1) return;
    FINANCE_STATE.expensePage -= 1;
    renderFinanceExpenses(getVisibleFinanceExpenses());
  });
  expenseNextBtn?.addEventListener('click', () => {
    if (FINANCE_STATE.expensePage >= getFinanceExpenseTotalPages(getVisibleFinanceExpenses().length)) return;
    FINANCE_STATE.expensePage += 1;
    renderFinanceExpenses(getVisibleFinanceExpenses());
  });
  recordPrevBtn?.addEventListener('click', () => {
    if (FINANCE_STATE.recordPage <= 1) return;
    FINANCE_STATE.recordPage -= 1;
    renderFinanceRecords(getVisibleFinanceRecords());
  });
  recordNextBtn?.addEventListener('click', () => {
    if (FINANCE_STATE.recordPage >= getFinanceRecordTotalPages(getVisibleFinanceRecords().length)) return;
    FINANCE_STATE.recordPage += 1;
    renderFinanceRecords(getVisibleFinanceRecords());
  });

  await loadFinanceData(initialMonth);
}

const pageInits = {
  login: initLogin,
  'forgot-password-1': initForgotPassword1,
  'forgot-password-2': initForgotPassword2,
  register: initRegister,
  'pos-menu': initPosMenu,
  'pos-payment': initPosPayment,
  'delivery-manage': initDeliveryManage,
  'financial-management': initFinancialManagement,
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
  if (enforceFrontendAuthGuard()) return;

  initSharedLogoutConfirmation();

  const page = document.body.dataset.page;
  if (page && pageInits[page]) {
    pageInits[page]();
  }
});
