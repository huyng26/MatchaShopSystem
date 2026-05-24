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

function initLogin() {
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
        window.location.reload();
      }, 2500);
    }, 1000);
  });
}

function initPosMenu() {
  const searchInput = document.querySelector('input[type="text"]');
  if (!searchInput?.parentElement) return;

  searchInput.addEventListener('focus', () => {
    searchInput.parentElement.classList.add('scale-[1.02]');
  });
  searchInput.addEventListener('blur', () => {
    searchInput.parentElement.classList.remove('scale-[1.02]');
  });
}

function initPosPayment() {
  document.querySelectorAll('input[name="payment"]').forEach((input) => {
    input.addEventListener('change', (e) => {
      const labels = document.querySelectorAll('label > div');
      labels.forEach((l) =>
        l.classList.remove('border-secondary', 'bg-secondary-container/10')
      );
      if (e.target.checked && e.target.nextElementSibling) {
        e.target.nextElementSibling.classList.add(
          'border-secondary',
          'bg-secondary-container/10'
        );
      }
    });
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
  const page = document.body.dataset.page;
  if (page && pageInits[page]) {
    pageInits[page]();
  }
});
