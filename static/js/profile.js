(function () {
  'use strict';

  const profileRoot = document.getElementById('profile-root');
  const profileUsername = profileRoot?.dataset.username || '';
  const profileUserIdFromRoot = parseInt(profileRoot?.dataset.userId || '0', 10);
  const profileUserId = Number.isFinite(profileUserIdFromRoot) && profileUserIdFromRoot > 0
    ? profileUserIdFromRoot
    : Number(window.currentUser?.id || 0);
  const avatarInput = document.getElementById('avatar-upload-input');
  const avatarStatus = document.getElementById('avatar-status');
  const timeline = document.getElementById('activity-timeline');

  function escapeHtml(value) {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  async function loadProfileGallery() {
    const gallery = document.getElementById('user-gallery');
    const emptyState = document.getElementById('profile-empty');
    const statTotal = document.getElementById('stat-total');
    const statCategories = document.getElementById('stat-categories');
    const statLatest = document.getElementById('stat-latest');

    if (!gallery) return;

    if (!profileUserId) {
      gallery.innerHTML = '';
      if (emptyState) {
        emptyState.style.display = 'block';
        emptyState.textContent = '未能识别当前用户，无法加载作品。';
      }
      return;
    }

    try {
      const res = await fetch(
        `/api/images?author_id=${encodeURIComponent(profileUserId)}&limit=12`,
        { credentials: 'include' }
      );
      if (!res.ok) throw new Error('加载失败');
      const data = await res.json();
      const items = data.items || [];

      gallery.innerHTML = '';
      emptyState.style.display = items.length ? 'none' : 'block';

      statTotal.textContent = data.total ?? 0;
      const categories = new Set(items.map(item => item.category).filter(Boolean));
      statCategories.textContent = categories.size;
      const latest = items[0];
      statLatest.textContent = latest ? latest.title || '已上传' : '—';

      if (timeline) {
        timeline.innerHTML = '';
        if (items.length) {
          items.slice(0, 6).forEach((item) => {
            const date = item.created_at ? new Date(item.created_at) : null;
            const label = date
              ? date.toLocaleString('zh-CN', {
                  month: 'short',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                })
              : '刚刚';
            const mediaUrl = item.thumbnail_url || item.url || '/static/images/placeholder.jpg';
            const li = document.createElement('li');
            li.className = 'timeline-item';
            li.innerHTML = `
              <span class="timeline-dot"></span>
              <div style="display:flex; gap:12px; align-items:center; width:100%;">
                <img src="${escapeHtml(mediaUrl)}" alt="${escapeHtml(item.title || '用户作品')}" style="width:72px;height:72px;object-fit:cover;border-radius:10px;border:1px solid rgba(255,255,255,0.15);" />
                <div>
                  <strong>${escapeHtml(item.title || '未命名作品')}</strong>
                  <p>${escapeHtml(label)} · ${escapeHtml(item.category || 'Gallery')}</p>
                </div>
              </div>
            `;
            timeline.appendChild(li);
          });
        } else {
          timeline.innerHTML =
            '<li class="timeline-item"><span class="timeline-dot"></span>' +
            '<div><strong>还没有动态</strong>' +
            '<p>上传第一张照片后，最新活动会出现在这里。</p></div></li>';
        }
      }

      items.forEach((item) => {
        const card = document.createElement('article');
        card.className = 'profile-card';
        card.innerHTML = `
          <a href="/photo/${item.id}" class="profile-card-link">
            <img src="${item.url || '/static/images/placeholder.jpg'}" alt="${escapeHtml(item.title || '用户作品')}" />
          </a>
          <div class="profile-card-body">
            <h3>${escapeHtml(item.title || '未命名作品')}</h3>
            <p>${escapeHtml(item.description || '这张照片还没有写简介。')}</p>
            <div class="profile-meta">
              <span class="profile-chip">${escapeHtml(item.category || 'Gallery')}</span>
              ${item.tags && Array.isArray(item.tags) && item.tags.length
                ? `<span class="profile-chip">${escapeHtml(item.tags.map(t => `#${t}`).join(' '))}</span>`
                : ''}
            </div>
          </div>
        `;
        gallery.appendChild(card);
      });
    } catch (error) {
      console.error(error);
      gallery.innerHTML = '';
      emptyState.style.display = 'block';
      emptyState.textContent = '作品列表暂时无法加载。';
    }
  }

  async function uploadAvatar(file) {
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);

    avatarStatus.textContent = '正在上传头像...';
    try {
      const res = await fetch('/api/users/me/avatar', {
        method: 'POST',
        credentials: 'include',
        body: formData,
      });
      const payload = await res.json();
      if (!res.ok) throw new Error(payload.detail || '上传失败');

      const avatarImg = document.querySelector('.profile-avatar img');
      if (avatarImg) {
        avatarImg.src = payload.avatar_url;
      } else {
        const avatarContainer = document.querySelector('.profile-avatar');
        avatarContainer.innerHTML =
          `<img src="${payload.avatar_url}" alt="头像" />`;
      }
      avatarStatus.textContent = '头像已更新。';
    } catch (error) {
      console.error(error);
      avatarStatus.textContent = error.message || '头像上传失败。';
    }
  }

  // 绑定事件监听器
  avatarInput?.addEventListener('change', (event) => {
    const file = event.target.files?.[0];
    if (file) uploadAvatar(file);
  });

  document.getElementById('profile-upload-btn')?.addEventListener('click', () => {
    document.getElementById('btn-upload-trigger')?.click();
  });

  loadProfileGallery();
})();
