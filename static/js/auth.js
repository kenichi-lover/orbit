window.currentUser = null;
const currentUserDataEl = document.getElementById('current-user-data');
if (currentUserDataEl) {
  try {
    window.currentUser = JSON.parse(currentUserDataEl.textContent);
  } catch (err) {
    console.error('Failed to parse current user data', err);
  }
}

let authMode = 'login';

function openAuthModal(mode) {
  authMode = mode;
  updateAuthUI();
  document.getElementById('auth-modal')?.classList.add('is-open');
  document.getElementById('auth-error')?.classList.remove('is-visible');
}

function closeAuthModal() {
  document.getElementById('auth-modal')?.classList.remove('is-open');
  document.getElementById('auth-form')?.reset();
}

function switchAuthMode() {
  authMode = authMode === 'login' ? 'register' : 'login';
  updateAuthUI();
  document.getElementById('auth-error')?.classList.remove('is-visible');
}

function updateAuthUI() {
  const title = document.getElementById('auth-title');
  const submitBtn = document.getElementById('auth-submit-btn');
  const switchText = document.getElementById('auth-switch-text');
  const switchBtn = document.getElementById('auth-switch-btn');
  const regFields = document.getElementById('register-fields');

  if (!title || !submitBtn) return;

  if (authMode === 'login') {
    title.textContent = '登录';
    submitBtn.textContent = '登录';
    switchText.textContent = '还没有账号？';
    switchBtn.textContent = '注册';
    if (regFields) regFields.style.display = 'none';
  } else {
    title.textContent = '注册';
    submitBtn.textContent = '注册';
    switchText.textContent = '已有账号？';
    switchBtn.textContent = '登录';
    if (regFields) regFields.style.display = 'flex';
  }
}

function bindAuthTriggers() {
  const loginBtn = document.getElementById('btn-login');
  const registerBtn = document.getElementById('btn-register');
  const logoutBtn = document.getElementById('btn-logout');
  const uploadTrigger = document.getElementById('btn-upload-trigger');
  const closeAuthBtn = document.getElementById('btn-close-auth');
  const switchAuthBtn = document.getElementById('auth-switch-btn');
  const closeUploadBtn = document.getElementById('btn-close-upload');
  const speedSlider = document.getElementById('speed-slider');
  const speedValue = document.getElementById('speed-value');
  const viewSlider = document.getElementById('view-slider');
  const viewValue = document.getElementById('view-value');

  // 统一绑定外部 JS，避免内联事件处理器
  if (loginBtn) loginBtn.addEventListener('click', () => openAuthModal('login'));
  if (registerBtn) registerBtn.addEventListener('click', () => openAuthModal('register'));
  if (logoutBtn) logoutBtn.addEventListener('click', handleLogout);
  if (uploadTrigger) uploadTrigger.addEventListener('click', () => window.openUploadModal?.());
  if (closeAuthBtn) closeAuthBtn.addEventListener('click', closeAuthModal);
  if (switchAuthBtn) switchAuthBtn.addEventListener('click', switchAuthMode);
  if (closeUploadBtn) closeUploadBtn.addEventListener('click', () => window.closeUploadModal?.());

  if (speedSlider && speedValue) {
    speedSlider.addEventListener('input', (e) => {
      speedValue.innerText = `${e.target.value}%`;
    });
  }

  if (viewSlider && viewValue) {
    viewSlider.addEventListener('input', (e) => {
      viewValue.innerText = `${e.target.value}°`;
    });
  }
}

async function handleLogout() {
  try {
    const res = await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' });
    if (res.ok) {
      window.location.reload();
    } else {
      const data = await res.json();
      alert('退出失败：' + (data.detail || '发生错误'));
    }
  } catch (err) {
    alert('网络错误，请重试');
  }
}

function initAuth() {
  const form = document.getElementById('auth-form');
  const modal = document.getElementById('auth-modal');
  if (!form || !modal) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('modal-username')?.value;
    const password = document.getElementById('modal-password')?.value;
    const errorEl = document.getElementById('auth-error');

    let body, url;

    if (authMode === 'login') {
      url = '/api/auth/login';
      body = JSON.stringify({ username, password });
    } else {
      url = '/api/auth/register';
      const email = document.getElementById('modal-email')?.value;
      if (!email) {
        errorEl.textContent = '请输入邮箱';
        errorEl.classList.add('is-visible');
        return;
      }
      body = JSON.stringify({ username, password, email });
    }

    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body,
        credentials: 'include',
      });
      const data = await res.json();

      if (!res.ok) {
        errorEl.textContent = data.detail || '发生错误';
        errorEl.classList.add('is-visible');
      } else {
        window.location.reload();
      }
    } catch {
      errorEl.textContent = '网络错误';
      errorEl.classList.add('is-visible');
    }
  });

  modal.addEventListener('click', (e) => {
    if (e.target === modal) closeAuthModal();
  });
}

initAuth();
bindAuthTriggers();

window.openAuthModal = openAuthModal;
window.closeAuthModal = closeAuthModal;
window.switchAuthMode = switchAuthMode;
window.handleLogout = handleLogout;
