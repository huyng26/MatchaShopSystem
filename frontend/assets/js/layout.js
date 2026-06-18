/**
 * MatchaShop — Shared Layout Manager
 * Injects Sidebar and TopAppBar into admin pages.
 * Active nav is auto-detected via data-page on <body>.
 */

const _NAV_INACTIVE =
  'flex items-center gap-4 px-4 py-3 text-[#f9f9f8]/70 hover:text-[#f9f9f8] hover:bg-[#06440c]/60 rounded-xl font-medium transition-colors';
const _NAV_ACTIVE =
  'flex items-center gap-4 px-4 py-3 bg-[#06440c] text-[#f9f9f8] rounded-xl font-semibold';

const LAYOUT_ROLE_LABELS = {
  admin: 'Admin',
  cashier: 'Cashier',
  delivery_manager: 'Delivery Manager',
  inventory_manager: 'Inventory Manager',
  shipper: 'Shipper',
};

const MATCHA_SHOP_LATITUDE = Number.isFinite(Number(window.MATCHA_SHOP_LATITUDE))
  ? Number(window.MATCHA_SHOP_LATITUDE)
  : 21.006237;
const MATCHA_SHOP_LONGITUDE = Number.isFinite(Number(window.MATCHA_SHOP_LONGITUDE))
  ? Number(window.MATCHA_SHOP_LONGITUDE)
  : 105.843127;

window.MATCHA_SHOP_LATITUDE = MATCHA_SHOP_LATITUDE;
window.MATCHA_SHOP_LONGITUDE = MATCHA_SHOP_LONGITUDE;
window.MATCHA_SHOP_ROUTE_POINT = Object.freeze({
  label: 'Store',
  get latitude() {
    return window.MATCHA_SHOP_LATITUDE;
  },
  get longitude() {
    return window.MATCHA_SHOP_LONGITUDE;
  },
});

const LAYOUT_NOTIFICATION_API_BASE_URL =
  window.MATCHA_API_BASE_URL || 'http://localhost:8000/api/v1';
const LAYOUT_NOTIFICATION_POLL_INTERVAL_MS = 10000;
const LAYOUT_NOTIFICATION_LIMIT = 20;
const LAYOUT_NOTIFICATION_TOAST_DURATION_MS = 5000;

const LAYOUT_NOTIFICATION_TYPE_ICONS = {
  'order.ready_for_delivery': 'local_shipping',
  'delivery.trip_assigned': 'route',
  'delivery.order_failed': 'warning',
  'delivery.cod_discrepancy': 'priority_high',
  'delivery.order_delivered': 'task_alt',
  'delivery.trip_completed': 'done_all',
  'inventory.low_stock': 'inventory_2',
  'product.created': 'add_circle',
  'product.updated': 'edit',
  'product.availability_updated': 'toggle_on',
};

const LAYOUT_NOTIFICATION_SEVERITY_LABELS = {
  info: 'Info',
  warning: 'Warning',
  critical: 'Critical',
};

// ─── Sidebar Template ────────────────────────────────────────────────────────
const SIDEBAR_HTML = `
  <div class="flex items-center gap-3 mb-10 px-2">
    <div class="w-10 h-10 rounded-full bg-[#06440c] flex items-center justify-center overflow-hidden shrink-0">
      <img alt="Hoppers' Matcha Shop Logo" class="w-full h-full object-cover"
        src="https://lh3.googleusercontent.com/aida-public/AB6AXuAXRMPJfgLrAFfB9xLzGUIGMCrcZAR-yQSGNqWTFX9vFRQv4QMXkX4cY5D2ERn3oAAuJGXHblUihyOQlNKg3VZXSwmSuERhdEAYAucZvEdNxam6eCnKauE0fIDaOC9ErE5QlCuozZ6P4YkCI15fn1sopDH0TACLUdkDo0Ykn3yERcrLIrRlQCk8_Lr8PfsLgZ_TnsWMVCgDjGbxOIWyidz2QGyjJ9a05v6jssGYyWHyMzupagZJUtTAKuLyvpvZEFqyp_w1nE_9jh3l" />
    </div>
    <div>
      <h1 class="font-serif text-lg font-bold italic text-[#f9f9f8] leading-tight">Hoppers' Matcha</h1>
      <p class="text-[10px] text-[#f9f9f8]/60 uppercase tracking-widest">Artisan POS</p>
    </div>
  </div>
  <nav class="flex-1 space-y-1" id="sidebar-main-nav">
    <a class="${_NAV_INACTIVE}" data-nav="dashboard" href="dashboard.html">
      <span class="material-symbols-outlined">dashboard</span><span>Dashboard</span>
    </a>
    <a class="${_NAV_INACTIVE}" data-nav="pos-menu" href="POS_menu.html">
      <span class="material-symbols-outlined">local_cafe</span><span>Point of Sale</span>
    </a>
    <a class="${_NAV_INACTIVE}" data-nav="delivery-manage" href="delivery_manage.html">
      <span class="material-symbols-outlined">local_shipping</span><span>Delivery Management</span>
    </a>
    <a class="${_NAV_INACTIVE}" data-nav="shipper" href="shipper.html">
      <span class="material-symbols-outlined">two_wheeler</span><span>Ship</span>
    </a>
    <a class="${_NAV_INACTIVE}" data-nav="performance" href="performance.html">
      <span class="material-symbols-outlined">query_stats</span><span>Performance</span>
    </a>
    <a class="${_NAV_INACTIVE}" data-nav="financial-management" href="financial_management.html">
      <span class="material-symbols-outlined">account_balance</span><span>Financial Management</span>
    </a>
    <a class="${_NAV_INACTIVE}" data-nav="menu" href="menu.html">
      <span class="material-symbols-outlined">eco</span><span>Menu</span>
    </a>
    <a class="${_NAV_INACTIVE}" data-nav="inventory" href="inventory_list.html">
      <span class="material-symbols-outlined">inventory_2</span><span>Inventory</span>
    </a>
    <a class="${_NAV_INACTIVE}" data-nav="customers" href="customer_list.html">
      <span class="material-symbols-outlined">group</span><span>Customers</span>
    </a>
    <a class="${_NAV_INACTIVE}" data-nav="employees" href="employee_list.html">
      <span class="material-symbols-outlined">badge</span><span>Employees</span>
    </a>
    <a class="${_NAV_INACTIVE}" data-nav="account" href="account_list.html">
      <span class="material-symbols-outlined">manage_accounts</span><span>Account</span>
    </a>
  </nav>
  <div class="pt-6 border-t border-[#06440c]/80 space-y-1">
    <a class="${_NAV_INACTIVE}" href="#" id="app-logout-link">
      <span class="material-symbols-outlined">logout</span><span>Log out</span>
    </a>
  </div>
`;

// ─── TopAppBar Template ──────────────────────────────────────────────────────
function buildTopbarHTML(config) {
  const roleLabel = LAYOUT_ROLE_LABELS[getLayoutStoredUserRole()] || 'User';
  const backBtn = config.backUrl
    ? `<a class="p-2 hover:bg-surface-container rounded-full transition-colors mr-1" href="${config.backUrl}">
        <span class="material-symbols-outlined text-primary">arrow_back</span>
       </a>`
    : '';
  const searchW = config.backUrl ? 'w-64' : 'w-80';
  const searchBar = config.hideSearch
    ? ''
    : `<div class="flex items-center bg-surface-container rounded-full px-4 py-2.5 ${searchW} gap-2">
        <span class="material-symbols-outlined text-on-surface-variant">search</span>
        <input id="topbar-search"
          class="bg-transparent border-none focus:ring-0 text-sm w-full placeholder-on-surface-variant/60 font-body"
          placeholder="${config.searchPlaceholder}" type="text" />
      </div>`;

  return `
    <div class="flex items-center gap-2">
      ${backBtn}
      ${searchBar}
    </div>
    <div class="flex items-center gap-3">
      <div class="notification-menu" id="notification-menu">
        <button class="notification-trigger" id="notification-trigger" type="button"
          aria-label="Open notifications" aria-haspopup="true" aria-expanded="false">
          <span class="material-symbols-outlined text-[#002c04]">notifications</span>
          <span class="notification-badge" id="notification-badge" hidden>0</span>
        </button>
        <section class="notification-panel" id="notification-panel" aria-label="Notifications" hidden>
          <div class="notification-panel-header">
            <div>
              <p class="notification-panel-title">Notifications</p>
              <p class="notification-panel-subtitle" id="notification-panel-subtitle">Recent operational alerts</p>
            </div>
            <button class="notification-mark-all" id="notification-mark-all" type="button">Mark all read</button>
          </div>
          <div class="notification-list custom-scrollbar" id="notification-list"></div>
        </section>
      </div>
      <div class="h-8 w-px bg-outline-variant/30 mx-1"></div>
      <div class="flex items-center gap-3">
        <div class="text-right">
          <p class="text-xs font-bold text-primary">User</p>
          <p class="text-[10px] text-on-surface-variant">${roleLabel}</p>
        </div>
        <div class="w-10 h-10 rounded-full bg-primary-container overflow-hidden">
          <img alt="Admin Profile" class="w-full h-full object-cover"
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuCtA0CwNVmPDCgOM3RC9uxRzhxpZyGGGaY16JScuZ00A1p_NODZCDDdZ7sFwmnN95zzclkIzLlY-RonKfkPbqPQzCNqZ0O3UQAbqes-uJ1zAP6ovnY5lOozDwUFoCK8WeHavhGdD3ILqQLPlYVOQqXFb5Z1TwjmExnurXRg4YrLQmJwINRtOlHuPDwgJAbiNm29VWflVEj4RZJwT_-o5VrWY7IW4J1dG36R8Do3mgPQT7YUk3GmBhSGHHun9Ihc-epj0VQMReU9RLSa" />
        </div>
      </div>
    </div>
  `;
}

// ─── Page Configuration ──────────────────────────────────────────────────────
const PAGE_CONFIG = {
  'dashboard':       { activeNav: 'dashboard',  searchPlaceholder: 'Search dashboard...',                 backUrl: null },
  'menu':            { activeNav: 'menu',        searchPlaceholder: 'Search menu items...',               backUrl: null },
  'product-detail':  { activeNav: 'menu',        searchPlaceholder: 'Search menu items...',               backUrl: 'menu.html', hideSearch: true },
  'inventory-list':  { activeNav: 'inventory',   searchPlaceholder: 'Search inventory...',                backUrl: null },
  'inventory-detail':{ activeNav: 'inventory',   searchPlaceholder: 'Search inventory...',                backUrl: 'inventory_list.html', hideSearch: true },
  'account-list':    { activeNav: 'account',     searchPlaceholder: 'Search accounts...',                 backUrl: null },
  'account-detail':  { activeNav: 'account',     searchPlaceholder: 'Search accounts...',                 backUrl: 'account_list.html', hideSearch: true },
  'customer-list':   { activeNav: 'customers',   searchPlaceholder: 'Search customers...',               backUrl: null },
  'customer-detail': { activeNav: 'customers',   searchPlaceholder: 'Search customers...',               backUrl: 'customer_list.html', hideSearch: true },
  'employee-list':   { activeNav: 'employees',   searchPlaceholder: 'Search employees...',               backUrl: null },
  'employee-detail': { activeNav: 'employees',   searchPlaceholder: 'Search employees...',               backUrl: 'employee_list.html', hideSearch: true },
  'financial-management': { activeNav: 'financial-management', searchPlaceholder: 'Search finance records...', backUrl: null },
  'settings':        { activeNav: 'settings',    searchPlaceholder: 'Search settings...',                backUrl: null },
  'pos-menu':        { activeNav: 'pos-menu',    searchPlaceholder: 'Search menu items...',               backUrl: null },
  'pos-payment':     { activeNav: 'pos-menu',    searchPlaceholder: 'Search payment items...',             backUrl: 'POS_menu.html', hideSearch: true },
  'shipper':         { activeNav: 'shipper',     searchPlaceholder: 'Search assigned trips or stops...',    backUrl: null },
  'performance':     { activeNav: 'performance', searchPlaceholder: 'Search delivered orders...',           backUrl: null },
  'delivery-manage': { activeNav: 'delivery-manage', searchPlaceholder: 'Search orders, shippers or routes...', backUrl: null },
};

const LAYOUT_ROLE_DEFAULT_PAGE = {
  admin: 'dashboard.html',
  cashier: 'POS_menu.html',
  delivery_manager: 'delivery_manage.html',
  inventory_manager: 'inventory_list.html',
  shipper: 'shipper.html',
};

const LAYOUT_NAV_PAGE = {
  dashboard: 'dashboard',
  'pos-menu': 'pos-menu',
  'delivery-manage': 'delivery-manage',
  shipper: 'shipper',
  performance: 'performance',
  'financial-management': 'financial-management',
  menu: 'menu',
  inventory: 'inventory-list',
  customers: 'customer-list',
  employees: 'employee-list',
  account: 'account-list',
};

// ─── Frontend Auth Guard ─────────────────────────────────────────────────────
function buildLayoutLoginRedirectUrl() {
  const currentPage = window.location.pathname.split('/').pop() || 'dashboard.html';
  const nextPath = `${currentPage}${window.location.search || ''}${window.location.hash || ''}`;
  return `login.html?next=${encodeURIComponent(nextPath)}`;
}

function getLayoutStoredUserRole() {
  try {
    const user = JSON.parse(localStorage.getItem('matcha_user') || 'null');
    return String(user?.role || '').toLowerCase();
  } catch (error) {
    return '';
  }
}

function getLayoutNotificationAuthHeaders() {
  const token = localStorage.getItem('matcha_access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function hasLayoutNotificationAccessToken() {
  return Boolean(localStorage.getItem('matcha_access_token'));
}

async function requestLayoutNotificationApi(path, options = {}) {
  const response = await fetch(`${LAYOUT_NOTIFICATION_API_BASE_URL}${path}`, {
    ...options,
    headers: {
      ...getLayoutNotificationAuthHeaders(),
      ...(options.headers || {}),
    },
  });
  const payload = await response.json().catch(() => null);

  if (response.status === 401 || response.status === 403) {
    const error = new Error('Notification access expired');
    error.status = response.status;
    throw error;
  }

  if (!response.ok || payload?.success === false) {
    throw new Error(payload?.message || 'Notification request failed');
  }

  return payload?.data ?? payload;
}

function escapeLayoutNotificationHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function formatLayoutNotificationTime(value) {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';

  const diffMs = Date.now() - date.getTime();
  const minuteMs = 60 * 1000;
  const hourMs = 60 * minuteMs;
  const dayMs = 24 * hourMs;

  if (diffMs < minuteMs) return 'Just now';
  if (diffMs < hourMs) return `${Math.max(1, Math.floor(diffMs / minuteMs))}m ago`;
  if (diffMs < dayMs) return `${Math.floor(diffMs / hourMs)}h ago`;

  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  });
}

function getLayoutNotificationIcon(notification) {
  return LAYOUT_NOTIFICATION_TYPE_ICONS[notification?.type] || 'notifications';
}

function getLayoutNotificationSeverityLabel(notification) {
  return LAYOUT_NOTIFICATION_SEVERITY_LABELS[notification?.severity] || 'Info';
}

function normalizeLayoutNotificationActionUrl(actionUrl) {
  const value = String(actionUrl || '').trim();
  if (!value) return '';
  if (/^https?:\/\//i.test(value)) return '';
  if (value.includes('/') || value.includes('\\')) return '';
  if (!/^[A-Za-z0-9_.-]+\.html([?#].*)?$/.test(value)) return '';
  return value;
}

function renderLayoutNotificationItem(notification) {
  const unreadClass = notification.read_at ? '' : ' is-unread';
  const severity = escapeLayoutNotificationHtml(notification.severity || 'info');
  const title = escapeLayoutNotificationHtml(notification.title || 'Notification');
  const message = escapeLayoutNotificationHtml(notification.message || '');
  const time = escapeLayoutNotificationHtml(formatLayoutNotificationTime(notification.created_at));
  const typeLabel = escapeLayoutNotificationHtml(getLayoutNotificationSeverityLabel(notification));
  const icon = escapeLayoutNotificationHtml(getLayoutNotificationIcon(notification));

  return `
    <button class="notification-item${unreadClass}" type="button"
      data-notification-id="${escapeLayoutNotificationHtml(notification.id)}">
      <span class="notification-item-icon notification-item-icon--${severity}">
        <span class="material-symbols-outlined">${icon}</span>
      </span>
      <span class="notification-item-body">
        <span class="notification-item-meta">
          <span>${typeLabel}</span>
          <span>${time}</span>
        </span>
        <span class="notification-item-title">${title}</span>
        <span class="notification-item-message">${message}</span>
      </span>
    </button>
  `;
}

function renderLayoutNotificationList(listEl, notifications, stateText = '') {
  if (!listEl) return;

  if (stateText) {
    listEl.innerHTML = `<div class="notification-empty">${escapeLayoutNotificationHtml(stateText)}</div>`;
    return;
  }

  if (!notifications.length) {
    listEl.innerHTML = `
      <div class="notification-empty">
        <span class="material-symbols-outlined">notifications_off</span>
        <span>No notifications yet</span>
      </div>
    `;
    return;
  }

  listEl.innerHTML = notifications.map(renderLayoutNotificationItem).join('');
}

function updateLayoutNotificationBadge(badgeEl, subtitleEl, count) {
  const unreadCount = Number(count) || 0;
  if (badgeEl) {
    if (unreadCount <= 0) {
      badgeEl.hidden = true;
      badgeEl.textContent = '0';
    } else {
      badgeEl.hidden = false;
      badgeEl.textContent = unreadCount > 99 ? '99+' : String(unreadCount);
    }
  }

  if (subtitleEl) {
    subtitleEl.textContent =
      unreadCount > 0
        ? `${unreadCount} unread notification${unreadCount === 1 ? '' : 's'}`
        : 'Recent operational alerts';
  }
}

function ensureLayoutNotificationToastContainer() {
  let container = document.getElementById('notification-toast-stack');
  if (container) return container;

  container = document.createElement('div');
  container.className = 'notification-toast-stack';
  container.id = 'notification-toast-stack';
  container.setAttribute('aria-live', 'polite');
  container.setAttribute('aria-atomic', 'false');
  document.body.appendChild(container);
  return container;
}

function rememberLayoutNotificationIds(state, notifications) {
  notifications.forEach((notification) => {
    if (notification?.id) {
      state.seenNotificationIds.add(String(notification.id));
    }
  });
}

function showLayoutNotificationToast(container, notification, onActivate) {
  if (!container || !notification?.id) return;

  const severity = escapeLayoutNotificationHtml(notification.severity || 'info');
  const icon = escapeLayoutNotificationHtml(getLayoutNotificationIcon(notification));
  const severityLabel = escapeLayoutNotificationHtml(
    getLayoutNotificationSeverityLabel(notification),
  );
  const title = escapeLayoutNotificationHtml(notification.title || 'Notification');
  const message = escapeLayoutNotificationHtml(notification.message || '');
  const time = escapeLayoutNotificationHtml(
    formatLayoutNotificationTime(notification.created_at),
  );

  const toast = document.createElement('button');
  toast.className = `notification-toast notification-toast--${severity}`;
  toast.type = 'button';
  toast.dataset.notificationId = String(notification.id);
  toast.innerHTML = `
    <span class="notification-toast-icon">
      <span class="material-symbols-outlined">${icon}</span>
    </span>
    <span class="notification-toast-body">
      <span class="notification-toast-meta">
        <span>${severityLabel}</span>
        <span>${time}</span>
      </span>
      <span class="notification-toast-title">${title}</span>
      <span class="notification-toast-message">${message}</span>
    </span>
  `;

  let closing = false;
  const closeToast = () => {
    if (closing) return;
    closing = true;
    toast.classList.remove('is-visible');
    toast.classList.add('is-leaving');
    window.setTimeout(() => {
      toast.remove();
    }, 260);
  };

  const hideTimer = window.setTimeout(closeToast, LAYOUT_NOTIFICATION_TOAST_DURATION_MS);

  toast.addEventListener('click', () => {
    window.clearTimeout(hideTimer);
    closeToast();
    onActivate(notification);
  });

  container.prepend(toast);
  window.requestAnimationFrame(() => {
    toast.classList.add('is-visible');
  });
}

function stopLayoutNotificationPolling(state) {
  if (state.pollTimer) {
    window.clearInterval(state.pollTimer);
    state.pollTimer = null;
  }
  state.stopped = true;
}

function initLayoutNotifications() {
  const menu = document.getElementById('notification-menu');
  const trigger = document.getElementById('notification-trigger');
  const panel = document.getElementById('notification-panel');
  const badge = document.getElementById('notification-badge');
  const list = document.getElementById('notification-list');
  const markAll = document.getElementById('notification-mark-all');
  const subtitle = document.getElementById('notification-panel-subtitle');

  if (!menu || !trigger || !panel || !badge || !list || !markAll) return;

  const state = {
    isOpen: false,
    isPolling: false,
    isCheckingNew: false,
    isLoadingList: false,
    pollTimer: null,
    stopped: false,
    notifications: [],
    seenNotificationIds: new Set(),
    baselineReady: false,
    toastContainer: ensureLayoutNotificationToastContainer(),
  };

  const handleApiError = (error) => {
    if (error?.status === 401 || error?.status === 403) {
      stopLayoutNotificationPolling(state);
      return;
    }
    console.error('Notification API failed:', error);
  };

  const activateNotification = async (notification, options = {}) => {
    if (!notification?.id || !hasLayoutNotificationAccessToken()) return;

    const actionUrl = normalizeLayoutNotificationActionUrl(notification.action_url);
    try {
      await requestLayoutNotificationApi(`/notifications/${notification.id}/read`, {
        method: 'POST',
      });
      await refreshCount({ checkNew: false });
      if (actionUrl) {
        window.location.href = actionUrl;
        return;
      }
      if (options.refreshList) {
        await refreshList();
      }
    } catch (error) {
      handleApiError(error);
    }
  };

  const handleIncomingUnreadNotifications = (
    notifications,
    { showToasts = true } = {},
  ) => {
    const unreadNotifications = notifications.filter(
      (notification) => notification?.id && !notification.read_at,
    );
    const newNotifications = unreadNotifications.filter(
      (notification) =>
        notification?.id && !state.seenNotificationIds.has(String(notification.id)),
    );

    rememberLayoutNotificationIds(state, unreadNotifications);

    if (!state.baselineReady) {
      state.baselineReady = true;
      return;
    }

    if (showToasts && newNotifications.length) {
      [...newNotifications].reverse().forEach((notification) => {
        showLayoutNotificationToast(
          state.toastContainer,
          notification,
          activateNotification,
        );
      });
    }
  };

  const checkNewUnreadNotifications = async ({ showToasts = true } = {}) => {
    if (state.stopped || state.isCheckingNew || !hasLayoutNotificationAccessToken()) return;
    if (document.hidden) return;

    state.isCheckingNew = true;
    try {
      const data = await requestLayoutNotificationApi(
        `/notifications?unread_only=true&limit=${LAYOUT_NOTIFICATION_LIMIT}`,
      );
      handleIncomingUnreadNotifications(Array.isArray(data) ? data : [], {
        showToasts,
      });
    } catch (error) {
      handleApiError(error);
    } finally {
      state.isCheckingNew = false;
    }
  };

  const refreshCount = async ({ checkNew = true } = {}) => {
    if (state.stopped || state.isPolling || !hasLayoutNotificationAccessToken()) return;
    if (document.hidden) return;

    state.isPolling = true;
    try {
      const data = await requestLayoutNotificationApi('/notifications/unread-count');
      updateLayoutNotificationBadge(badge, subtitle, data?.unread_count);
      if (checkNew) {
        await checkNewUnreadNotifications({ showToasts: true });
      }
    } catch (error) {
      handleApiError(error);
    } finally {
      state.isPolling = false;
    }
  };

  const refreshList = async () => {
    if (state.stopped || state.isLoadingList || !hasLayoutNotificationAccessToken()) return;

    state.isLoadingList = true;
    if (!state.notifications.length) {
      renderLayoutNotificationList(list, [], 'Loading notifications...');
    }

    try {
      const data = await requestLayoutNotificationApi(
        `/notifications?unread_only=false&limit=${LAYOUT_NOTIFICATION_LIMIT}`,
      );
      state.notifications = Array.isArray(data) ? data : [];
      handleIncomingUnreadNotifications(state.notifications, {
        showToasts: true,
      });
      rememberLayoutNotificationIds(state, state.notifications);
      renderLayoutNotificationList(list, state.notifications);
    } catch (error) {
      handleApiError(error);
      if (error?.status !== 401 && error?.status !== 403) {
        renderLayoutNotificationList(list, [], 'Unable to load notifications.');
      }
    } finally {
      state.isLoadingList = false;
    }
  };

  if (!window.__matchaNotificationFetchPatched) {
    const originalFetch = window.fetch.bind(window);
    window.fetch = async (input, options = {}) => {
      const response = await originalFetch(input, options);
      const requestUrl = typeof input === 'string' ? input : input?.url || '';
      const requestMethod = String(options.method || input?.method || 'GET').toUpperCase();
      const isMutatingRequest = !['GET', 'HEAD', 'OPTIONS'].includes(requestMethod);
      const isAppApiRequest = requestUrl.includes('/api/v1/');
      const isNotificationRequest = requestUrl.includes('/notifications');

      if (
        isMutatingRequest &&
        isAppApiRequest &&
        !isNotificationRequest &&
        hasLayoutNotificationAccessToken()
      ) {
        window.setTimeout(() => {
          refreshCount({ checkNew: true });
        }, 500);
      }

      return response;
    };
    window.__matchaNotificationFetchPatched = true;
  }

  const openPanel = async () => {
    state.isOpen = true;
    panel.hidden = false;
    trigger.setAttribute('aria-expanded', 'true');
    await refreshList();
  };

  const closePanel = () => {
    state.isOpen = false;
    panel.hidden = true;
    trigger.setAttribute('aria-expanded', 'false');
  };

  trigger.addEventListener('click', async () => {
    if (state.isOpen) {
      closePanel();
      return;
    }
    await openPanel();
  });

  markAll.addEventListener('click', async () => {
    if (!hasLayoutNotificationAccessToken()) return;
    markAll.disabled = true;
    try {
      await requestLayoutNotificationApi('/notifications/read-all', { method: 'POST' });
      state.notifications = state.notifications.map((notification) => ({
        ...notification,
        read_at: notification.read_at || new Date().toISOString(),
      }));
      rememberLayoutNotificationIds(state, state.notifications);
      renderLayoutNotificationList(list, state.notifications);
      updateLayoutNotificationBadge(badge, subtitle, 0);
    } catch (error) {
      handleApiError(error);
    } finally {
      markAll.disabled = false;
    }
  });

  list.addEventListener('click', async (event) => {
    const item = event.target.closest('[data-notification-id]');
    if (!item || !hasLayoutNotificationAccessToken()) return;

    const notificationId = item.dataset.notificationId;
    const notification = state.notifications.find(
      (current) => String(current.id) === String(notificationId),
    );
    const actionUrl = normalizeLayoutNotificationActionUrl(notification?.action_url);

    item.disabled = true;
    await activateNotification(
      notification || { id: notificationId, action_url: actionUrl },
      { refreshList: true },
    );
    if (document.body.contains(item)) {
      item.disabled = false;
    }
  });

  document.addEventListener('click', (event) => {
    if (!state.isOpen || menu.contains(event.target)) return;
    closePanel();
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && state.isOpen) {
      closePanel();
      trigger.focus();
    }
  });

  document.addEventListener('visibilitychange', async () => {
    if (state.stopped || document.hidden) return;
    await refreshCount();
    if (state.isOpen) {
      await refreshList();
    }
  });

  if (!hasLayoutNotificationAccessToken()) return;

  refreshCount();
  state.pollTimer = window.setInterval(async () => {
    await refreshCount();
    if (state.isOpen) {
      await refreshList();
    }
  }, LAYOUT_NOTIFICATION_POLL_INTERVAL_MS);
}

function canLayoutRoleAccessPage(role, page) {
  if (!PAGE_CONFIG[page]) return false;

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

function getLayoutDefaultPageForRole(role) {
  return LAYOUT_ROLE_DEFAULT_PAGE[role] || 'login.html';
}

function enforceLayoutAuthGuard() {
  const page = document.body.dataset.page;
  const isInternalPage = Boolean(PAGE_CONFIG[page]);
  const hasAccessToken = Boolean(localStorage.getItem('matcha_access_token'));
  const role = getLayoutStoredUserRole();

  if (isInternalPage && !hasAccessToken) {
    window.location.replace(buildLayoutLoginRedirectUrl());
    return true;
  }

  if (isInternalPage && !canLayoutRoleAccessPage(role, page)) {
    window.location.replace(getLayoutDefaultPageForRole(role));
    return true;
  }

  return false;
}

enforceLayoutAuthGuard();

// ─── Init ────────────────────────────────────────────────────────────────────
function initLayout() {
  if (enforceLayoutAuthGuard()) return;

  const page   = document.body.dataset.page;
  const config = PAGE_CONFIG[page];
  if (!config) return;

  // Inject Sidebar
  const sidebar = document.getElementById('app-sidebar');
  if (sidebar) {
    sidebar.innerHTML = SIDEBAR_HTML;
    const role = getLayoutStoredUserRole();

    sidebar.querySelectorAll('[data-nav]').forEach((link) => {
      const nav = link.dataset.nav;
      const navPage = LAYOUT_NAV_PAGE[nav];
      if (navPage && !canLayoutRoleAccessPage(role, navPage)) {
        link.remove();
      }
    });

    // Highlight active nav link
    const activeLink = sidebar.querySelector(`[data-nav="${config.activeNav}"]`);
    if (activeLink) {
      activeLink.className = _NAV_ACTIVE;
    }
  }

  // Inject TopAppBar
  const topbar = document.getElementById('app-topbar');
  if (topbar) {
    topbar.innerHTML = buildTopbarHTML(config);
    initLayoutNotifications();
  }
}

document.addEventListener('DOMContentLoaded', initLayout);
