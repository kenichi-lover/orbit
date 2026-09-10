/**
 * 页面专用脚本：渲染叙事时间线
 * 优化内容：
 * 1. 增加 XSS 防护 (escapeHtml)
 * 2. 性能优化：将用户数据读取移至循环外
 * 3. 代码健壮性增强
 */

// XSS 防护工具函数：转义 HTML 特殊字符
function escapeHtml(unsafe) {
    if (unsafe === null || unsafe === undefined) return "";
    return String(unsafe)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

let storyPage = 1;
const PAGE_SIZE = 20;

window._storyRender = async function renderStoryTimeline(query = "", page = 1) {
    const container = document.getElementById('story-timeline');
    const pageContainer = document.getElementById('story-pagination');
    if (!container) return;

    storyPage = page;
    const skip = (page - 1) * PAGE_SIZE;

    let images = [];
    let total = 0;
    try {
        const res = await fetch(`/api/images?skip=${skip}&limit=${PAGE_SIZE}`, {
            credentials: 'include'
        });
        const data = await res.json();
        images = data.items || [];
        total = data.total || 0;
    } catch (err) {
        console.error('Failed to load images for story page', err);
        container.innerHTML = '<p style="color: white; text-align: center;">加载叙事内容失败</p>';
        if (pageContainer) pageContainer.innerHTML = '';
        return;
    }

    // 搜索过滤逻辑
    if (query) {
        const lowerQuery = query.toLowerCase();
        images = images.filter(img =>
            (img.title || '').toLowerCase().includes(lowerQuery) ||
            (img.url || '').toLowerCase().includes(lowerQuery) ||
            (img.category || '').toLowerCase().includes(lowerQuery) ||
            (img.tags || '').toLowerCase().includes(lowerQuery)
        );
        // 搜索时重新从第一页开始渲染
        if (page !== 1) {
            renderStoryTimeline(query, 1);
            return;
        }
    }

    if (images.length === 0 && total === 0) {
        container.innerHTML = '<p style="color: rgba(255,255,255,0.6); text-align: center;">当前没有可展示的图片。</p>';
        if (pageContainer) pageContainer.innerHTML = '';
        return;
    }

    if (images.length === 0 && total > 0) {
        container.innerHTML = '<p style="color: rgba(255,255,255,0.6); text-align: center;">该页暂无数据。</p>';
        renderPagination(pageContainer, page, total, PAGE_SIZE);
        return;
    }

    // --- 性能优化：在循环外只读取一次当前用户数据 ---
    let currentUser = window.currentUser || window.readCurrentUser?.() || null;
    if (!currentUser) {
        try {
            const userDataEl = document.getElementById('current-user-data') || document.getElementById('user-data');
            if (userDataEl) {
                const raw = userDataEl.textContent?.trim();
                currentUser = raw && raw !== 'null' && raw !== 'undefined' ? JSON.parse(raw) : null;
            }
        } catch (err) {
            console.error('Failed to parse current user data', err);
        }
    }
    // ----------------------------------------------

    container.innerHTML = images.map((img, index) => {
        const isEven = index % 2 === 0;

        // 处理标签：分割、去空、转义
        const tagsList = (Array.isArray(img.tags) ? img.tags : (typeof img.tags === 'string' ? img.tags.split(',') : []))
            .map(t => escapeHtml(String(t).trim()))
            .filter(Boolean);
        
        const tagsHtml = tagsList.map(t => 
            `<span style="background: rgba(255,255,255,0.1); padding: 4px 12px; border-radius: 20px; font-size: 12px; color: rgba(255,255,255,0.8);">#${t}</span>`
        ).join('');

        // 权限校验（使用循环外的 currentUser）
        const isSuperuser = !!currentUser && currentUser.is_superuser === true;
        const authorName = img.author_name || null;
        const isOwner = !!currentUser && !!currentUser.username && !!authorName && authorName === currentUser.username;
        const canManage = isOwner || isSuperuser;

        let actionBtnHtml = '';
        let ownershipHintHtml = '';

        if (canManage) {
            actionBtnHtml = `
                <div style="margin-top: 16px; display: flex; gap: 8px; flex-wrap: wrap;">
                    <button data-action="edit-story" data-id="${img.id}" style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: white; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 12px;">编辑</button>
                    <button data-action="delete-story" data-id="${img.id}" style="background: rgba(255,50,50,0.8); color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 12px;">删除</button>
                </div>
            `;
            ownershipHintHtml = `<p style="margin-top: 8px; color: rgba(255,255,255,0.65); font-size: 12px;">你可以管理这张图片</p>`;
        } else if (currentUser && currentUser.username) {
            ownershipHintHtml = `<p style="margin-top: 8px; color: rgba(255,255,255,0.45); font-size: 12px;">这张图片不属于你，暂不可编辑</p>`;
        }

        // 数据转义：防止 XSS 攻击
        const safeTitle = escapeHtml(img.title);
        const safeDesc = escapeHtml(img.description || '');
        const safeCat = escapeHtml(img.category || 'Gallery');
        const safeTagsStr = Array.isArray(img.tags) ? img.tags.join(', ') : (img.tags || 'Photography');

        return `
            <div style="background: rgba(30, 30, 30, 0.6); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; overflow: hidden; display: flex; flex-direction: ${isEven ? 'row' : 'row-reverse'}; gap: 24px; align-items: center; transition: transform 0.3s;" class="story-item" id="story-item-${img.id}">
                <div style="flex: 1;">
                    <img src="${escapeHtml(img.url)}" alt="${safeTitle}" style="width: 100%; height: 300px; object-fit: cover; border-radius: 12px;" />
                </div>
                
                <!-- 展示视图 -->
                <div id="story-view-${img.id}" style="flex: 1; padding: 24px;">
                    <h3 style="color: white; font-size: 24px; font-weight: 300; margin-bottom: 12px;">${safeTitle}</h3>
                    <p style="color: rgba(255,255,255,0.6); font-size: 14px; line-height: 1.6;">${safeDesc}</p>
                    <div style="margin-top: 20px; display: flex; gap: 8px; flex-wrap: wrap;">
                        <span style="background: rgba(255,255,255,0.1); padding: 4px 12px; border-radius: 20px; font-size: 12px; color: rgba(255,255,255,0.8);">#${safeCat}</span>
                        ${tagsHtml}
                    </div>
                    ${ownershipHintHtml}
                    ${actionBtnHtml}
                </div>

                <!-- 编辑视图 -->
                <div id="story-edit-${img.id}" style="flex: 1; padding: 24px; display: none;">
                    <input type="text" id="edit-title-${img.id}" value="${safeTitle}" style="width: 100%; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.2); color: white; padding: 8px; margin-bottom: 12px; border-radius: 4px;" placeholder="标题">
                    <textarea id="edit-desc-${img.id}" style="width: 100%; height: 100px; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.2); color: white; padding: 8px; margin-bottom: 12px; border-radius: 4px;" placeholder="描述">${safeDesc}</textarea>
                    <input type="text" id="edit-cat-${img.id}" value="${safeCat}" style="width: 100%; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.2); color: white; padding: 8px; margin-bottom: 12px; border-radius: 4px;" placeholder="Category">
                    <input type="text" id="edit-tags-${img.id}" value="${safeTagsStr}" style="width: 100%; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.2); color: white; padding: 8px; margin-bottom: 12px; border-radius: 4px;" placeholder="Tags (comma separated)">
                    <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                        <button data-action="save-story" data-id="${img.id}" style="background: white; color: black; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-weight: bold;">保存</button>
                        <button data-action="cancel-edit-story" data-id="${img.id}" style="background: rgba(255,255,255,0.1); color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer;">取消</button>
                    </div>
                </div>
            </div>
        `;
    }).join('');

    // 渲染分页控件
    if (pageContainer) renderPagination(pageContainer, page, total, PAGE_SIZE);
};

/**
 * 渲染页码控件
 */
function renderPagination(container, currentPage, total, pageSize) {
    if (!container) return;
    const totalPages = Math.ceil(total / pageSize);
    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }

    const pages = [];
    // 显示当前页前后各 2 页，避免页码过多
    const start = Math.max(1, currentPage - 2);
    const end = Math.min(totalPages, currentPage + 2);

    if (start > 1) {
        pages.push(`<button data-page="1" class="page-btn">1</button>`);
        if (start > 2) pages.push(`<span class="page-ellipsis">…</span>`);
    }
    for (let i = start; i <= end; i++) {
        pages.push(`<button data-page="${i}" class="page-btn${i === currentPage ? ' active' : ''}">${i}</button>`);
    }
    if (end < totalPages) {
        if (end < totalPages - 1) pages.push(`<span class="page-ellipsis">…</span>`);
        pages.push(`<button data-page="${totalPages}" class="page-btn">${totalPages}</button>`);
    }

    container.innerHTML = `
        <div style="display: flex; justify-content: center; align-items: center; gap: 8px; margin-top: 40px; padding-bottom: 20px;">
            <button data-page="${currentPage - 1}" class="page-btn nav-btn" ${currentPage === 1 ? 'disabled style="opacity:0.3;cursor:not-allowed;"' : ''}>上一页</button>
            ${pages.join('')}
            <button data-page="${currentPage + 1}" class="page-btn nav-btn" ${currentPage === totalPages ? 'disabled style="opacity:0.3;cursor:not-allowed;"' : ''}>下一页</button>
            <span style="color: rgba(255,255,255,0.4); font-size: 12px; margin-left: 8px;">共 ${total} 张</span>
        </div>
    `.trim();

    // 事件委托
    container.addEventListener('click', (e) => {
        const btn = e.target.closest('[data-page]');
        if (!btn || btn.disabled) return;
        const p = parseInt(btn.dataset.page, 10);
        if (p >= 1 && p <= totalPages && p !== currentPage) {
            window.scrollTo({ top: 0, behavior: 'smooth' });
            window._storyRender && window._storyRender('', p);
        }
    });
}

// 切换到编辑模式
function editStory(id) {
    const viewEl = document.getElementById(`story-view-${id}`);
    const editEl = document.getElementById(`story-edit-${id}`);
    if (viewEl) viewEl.style.display = 'none';
    if (editEl) editEl.style.display = 'block';
}

// 取消编辑
function cancelEditStory(id) {
    const viewEl = document.getElementById(`story-view-${id}`);
    const editEl = document.getElementById(`story-edit-${id}`);
    if (viewEl) viewEl.style.display = 'block';
    if (editEl) editEl.style.display = 'none';
}

// 保存修改
async function saveStory(id) {
    const title = document.getElementById(`edit-title-${id}`)?.value || '';
    const description = document.getElementById(`edit-desc-${id}`)?.value || '';
    const category = document.getElementById(`edit-cat-${id}`)?.value || '';
    const tagsStr = document.getElementById(`edit-tags-${id}`)?.value || '';
    const tagsArray = tagsStr
        .split(',')
        .map(t => t.trim())
        .filter(Boolean);

    try {
        const res = await fetch(`/api/images/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, description, category, tags: tagsArray }),
            credentials: 'include',
        });

        if (res.ok) {
            // 重新渲染时间线以显示更新后的数据
            window._storyRender && window._storyRender();
        } else {
            const error = await res.json().catch(() => ({}));
            alert(error.detail || '保存失败');
        }
    } catch (err) {
        console.error(err);
        alert('网络错误');
    }
}

// 删除图片
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
        console.error(err);
        alert('网络错误');
    }
}

// 事件委托处理按钮点击
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

// 页面加载完成后初始化
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
