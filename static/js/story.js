// 页面专用脚本：渲染叙事时间线，并提供编辑/删除图片能力
window._storyRender = async function renderStoryTimeline(query = "") {
  const container = document.getElementById('story-timeline');
  if (!container) return;

  let images = [];
  try {
    const res = await fetch('/api/images?skip=0&limit=50', { credentials: 'include' });
    const data = await res.json();
    images = data.items || [];
  } catch (err) {
    console.error('Failed to load images for story page', err);
    container.innerHTML = '<p style="color: white; text-align: center;">加载叙事内容失败</p>';
    return;
  }

  if (query) {
    images = images.filter(img =>
      (img.title || '').toLowerCase().includes(query) ||
      (img.url || '').toLowerCase().includes(query) ||
      (img.category || '').toLowerCase().includes(query) ||
      (img.tags || '').toLowerCase().includes(query)
    );
  }

  if (images.length === 0) {
    container.innerHTML = '<p style="color: rgba(255,255,255,0.6); text-align: center;">当前没有可展示的图片。</p>';
    return;
  }

  container.innerHTML = images.map((img, index) => {
    const isEven = index % 2 === 0;
    const tagsList = img.tags ? img.tags.split(',').map(t => t.trim()).filter(Boolean) : ['Photography'];
    const tagsHtml = tagsList.map(t => `<span style="background: rgba(255,255,255,0.1); padding: 4px 12px; border-radius: 20px; font-size: 12px; color: rgba(255,255,255,0.8);">#${t}</span>`).join('');

    // 每次渲染时从 DOM 重新读取当前用户，避免模块加载时序问题导致缓存失效
    let currentUser = null;
    const userDataEl = document.getElementById('current-user-data');
    if (userDataEl) {
      try {
        currentUser = JSON.parse(userDataEl.textContent || 'null');
      } catch (err) {
        console.error('Failed to parse current user data', err);
      }
    }

    // 说明：只有图片作者本人，或者超级管理员，才能看到编辑和删除入口。
    const isSuperuser = !!currentUser && currentUser.is_superuser === true;
    const authorName = img.author_name || img.user_name || null;
    const isOwner = !!currentUser && !!currentUser.username && !!authorName && authorName === currentUser.username;
    const canManage = isOwner || isSuperuser;

    let actionBtnHtml = '';
    let ownershipHintHtml = '';
    if (canManage) {
      actionBtnHtml = `
        <div style="margin-top: 16px; display: flex; gap: 8px; flex-wrap: wrap;">
          <button data-action="edit-story" data-id="${img.id}" style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: white; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 12px;">
            编辑
          </button>
          <button data-action="delete-story" data-id="${img.id}" style="background: rgba(255,50,50,0.8); color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 12px;">
            删除
          </button>
        </div>
      `;
      ownershipHintHtml = `<p style="margin-top: 8px; color: rgba(255,255,255,0.65); font-size: 12px;">你可以管理这张图片</p>`;
    } else if (currentUser && currentUser.username) {
      ownershipHintHtml = `<p style="margin-top: 8px; color: rgba(255,255,255,0.45); font-size: 12px;">这张图片不属于你，暂不可编辑</p>`;
    }

    return `
    <div style="background: rgba(30, 30, 30, 0.6); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; overflow: hidden; display: flex; flex-direction: ${isEven ? 'row' : 'row-reverse'}; gap: 24px; align-items: center; transition: transform 0.3s;" class="story-item" id="story-item-${img.id}">
      <div style="flex: 1;">
        <img src="${img.url}" alt="${img.title}" style="width: 100%; height: 300px; object-fit: cover; border-radius: 12px;" />
      </div>

      <div id="story-view-${img.id}" style="flex: 1; padding: 24px;">
        <h3 style="color: white; font-size: 24px; font-weight: 300; margin-bottom: 12px;">${img.title}</h3>
        <p style="color: rgba(255,255,255,0.6); font-size: 14px; line-height: 1.6;">${img.description || ''}</p>
        <div style="margin-top: 20px; display: flex; gap: 8px; flex-wrap: wrap;">
          <span style="background: rgba(255,255,255,0.1); padding: 4px 12px; border-radius: 20px; font-size: 12px; color: rgba(255,255,255,0.8);">#${img.category || 'Gallery'}</span>
          ${tagsHtml}
        </div>
        ${ownershipHintHtml}
        ${actionBtnHtml}
      </div>

      <div id="story-edit-${img.id}" style="flex: 1; padding: 24px; display: none;">
        <input type="text" id="edit-title-${img.id}" value="${img.title}" style="width: 100%; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.2); color: white; padding: 8px; margin-bottom: 12px; border-radius: 4px;">
        <textarea id="edit-desc-${img.id}" style="width: 100%; height: 100px; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.2); color: white; padding: 8px; margin-bottom: 12px; border-radius: 4px;">${img.description || ''}</textarea>
        <input type="text" id="edit-cat-${img.id}" value="${img.category || 'Gallery'}" style="width: 100%; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.2); color: white; padding: 8px; margin-bottom: 12px; border-radius: 4px;" placeholder="Category">
        <input type="text" id="edit-tags-${img.id}" value="${img.tags || 'Photography'}" style="width: 100%; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.2); color: white; padding: 8px; margin-bottom: 12px; border-radius: 4px;" placeholder="Tags (comma separated)">

        <div style="display: flex; gap: 10px; flex-wrap: wrap;">
          <button data-action="save-story" data-id="${img.id}" style="background: white; color: black; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-weight: bold;">保存</button>
          <button data-action="cancel-edit-story" data-id="${img.id}" style="background: rgba(255,255,255,0.1); color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer;">取消</button>
        </div>
      </div>
    </div>
    `;
  }).join('');
};

function editStory(id) {
  const viewEl = document.getElementById(`story-view-${id}`);
  const editEl = document.getElementById(`story-edit-${id}`);
  if (viewEl) viewEl.style.display = 'none';
  if (editEl) editEl.style.display = 'block';
}

function cancelEditStory(id) {
  const viewEl = document.getElementById(`story-view-${id}`);
  const editEl = document.getElementById(`story-edit-${id}`);
  if (viewEl) viewEl.style.display = 'block';
  if (editEl) editEl.style.display = 'none';
}

async function saveStory(id) {
  const title = document.getElementById(`edit-title-${id}`)?.value || '';
  const description = document.getElementById(`edit-desc-${id}`)?.value || '';
  const category = document.getElementById(`edit-cat-${id}`)?.value || '';
  const tagsStr = document.getElementById(`edit-tags-${id}`)?.value || '';

  try {
    const res = await fetch(`/api/images/${id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, description, category, tags: tagsStr }),
      credentials: 'include',
    });

    if (res.ok) {
      window._storyRender && window._storyRender();
    } else {
      const error = await res.json().catch(() => ({}));
      alert(error.detail || '保存失败');
    }
  } catch (err) {
    alert('网络错误');
  }
}

async function deleteStory(id) {
  if (!confirm('确定要删除此图片吗？')) return;

  try {
    const res = await fetch(`/api/images/${id}?hard=true`, {
      method: 'DELETE',
      credentials: 'include',
    });

    if (res.ok) {
      window._storyRender && window._storyRender();
    } else {
      const error = await res.json().catch(() => ({}));
      alert(error.detail || '删除失败');
    }
  } catch (err) {
    alert('网络错误');
  }
}

function handleStoryAction(event) {
  const btn = event.target.closest('[data-action]');
  if (!btn) return;

  const action = btn.getAttribute('data-action');
  const id = btn.getAttribute('data-id');
  if (!id) return;

  switch (action) {
    case 'edit-story':
      editStory(id);
      break;
    case 'cancel-edit-story':
      cancelEditStory(id);
      break;
    case 'save-story':
      saveStory(id);
      break;
    case 'delete-story':
      deleteStory(id);
      break;
    default:
      break;
  }
}

async function loadStoryTimeline() {
  const container = document.getElementById('story-timeline');
  if (!container) return;
  container.addEventListener('click', handleStoryAction);
  await window._storyRender();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', loadStoryTimeline);
} else {
  loadStoryTimeline();
}
