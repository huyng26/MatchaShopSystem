/**
 * MatchaShop — Shared Layout Manager
 * Injects Sidebar and TopAppBar into admin pages.
 * Active nav is auto-detected via data-page on <body>.
 */

const _NAV_INACTIVE =
  'flex items-center gap-4 px-4 py-3 text-[#f9f9f8]/70 hover:text-[#f9f9f8] hover:bg-[#06440c]/60 rounded-xl font-medium transition-colors';
const _NAV_ACTIVE =
  'flex items-center gap-4 px-4 py-3 bg-[#06440c] text-[#f9f9f8] rounded-xl font-semibold';

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
    <a class="${_NAV_INACTIVE}" data-nav="settings" href="settings.html">
      <span class="material-symbols-outlined">settings</span><span>Settings</span>
    </a>
    <a class="${_NAV_INACTIVE}" href="#" id="app-logout-link">
      <span class="material-symbols-outlined">logout</span><span>Log out</span>
    </a>
  </div>
`;

// ─── TopAppBar Template ──────────────────────────────────────────────────────
function buildTopbarHTML(config) {
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
      <button class="hover:bg-surface-container rounded-full p-2.5 transition-all relative">
        <span class="material-symbols-outlined text-[#002c04]">notifications</span>
        <span class="absolute top-2 right-2 w-2 h-2 bg-secondary rounded-full border-2 border-surface"></span>
      </button>
      <div class="h-8 w-px bg-outline-variant/30 mx-1"></div>
      <div class="flex items-center gap-3">
        <div class="text-right">
          <p class="text-xs font-bold text-primary">Admin User</p>
          <p class="text-[10px] text-on-surface-variant">Store Manager</p>
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
  'customer-detail': { activeNav: 'customers',   searchPlaceholder: 'Search customers...',               backUrl: 'customer_list.html' },
  'employee-list':   { activeNav: 'employees',   searchPlaceholder: 'Search employees...',               backUrl: null },
  'employee-detail': { activeNav: 'employees',   searchPlaceholder: 'Search employees...',               backUrl: 'employee_list.html', hideSearch: true },
  'financial-management': { activeNav: 'financial-management', searchPlaceholder: 'Search finance records...', backUrl: null },
  'settings':        { activeNav: 'settings',    searchPlaceholder: 'Search settings...',                backUrl: null },
  'pos-menu':        { activeNav: 'pos-menu',    searchPlaceholder: 'Search menu items...',               backUrl: null },
  'pos-payment':     { activeNav: 'pos-menu',    searchPlaceholder: 'Search payment items...',             backUrl: 'POS_menu.html', hideSearch: true },
  'shipper':         { activeNav: 'shipper',     searchPlaceholder: 'Search assigned trips or stops...',    backUrl: null },
  'delivery-manage': { activeNav: 'delivery-manage', searchPlaceholder: 'Search orders, shippers or routes...', backUrl: null },
};

const LAYOUT_ROLE_DEFAULT_PAGE = {
  admin: 'dashboard.html',
  cashier: 'POS_menu.html',
  delivery_manager: 'dashboard.html',
  inventory_manager: 'inventory_list.html',
  shipper: 'shipper.html',
};

const LAYOUT_NAV_PAGE = {
  dashboard: 'dashboard',
  'pos-menu': 'pos-menu',
  'delivery-manage': 'delivery-manage',
  shipper: 'shipper',
  'financial-management': 'financial-management',
  menu: 'menu',
  inventory: 'inventory-list',
  customers: 'customer-list',
  employees: 'employee-list',
  account: 'account-list',
  settings: 'settings',
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

function canLayoutRoleAccessPage(role, page) {
  if (!PAGE_CONFIG[page]) return false;

  if (role === 'admin') {
    return page !== 'shipper';
  }

  const allowedPagesByRole = {
    cashier: new Set(['pos-menu', 'pos-payment']),
    delivery_manager: new Set(['dashboard', 'delivery-manage']),
    inventory_manager: new Set(['inventory-list', 'inventory-detail']),
    shipper: new Set(['shipper']),
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
  }
}

document.addEventListener('DOMContentLoaded', initLayout);
