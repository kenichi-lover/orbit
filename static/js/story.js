// 页面专用脚本：渲染叙事时间线（与 nav.js 中的 renderStoryMode 类似的独立实现）
async function loadStoryTimeline() {
  const container = document.getElementById('story-timeline');
  if (!container) return;

  let images = [];
  try {
    const res = await fetch('/api/images?skip=0&limit=50');
    const data = await res.json();
    images = data.items || [];
  } catch (err) {
    console.error('Failed to load images for story page', err);
    container.innerHTML = '<p style="color: white; text-align: center;">加载叙事内容失败</p>';
    return;
  }

  if (images.length === 0) {
    container.innerHTML = '<p style="color: rgba(255,255,255,0.6); text-align: center;">当前没有可展示的图片。</p>';
    return;
  }

  container.innerHTML = images.map((img, index) => {
    const isEven = index % 2 === 0;
    const tagsList = img.tags ? img.tags.split(',').map(t => t.trim()).filter(Boolean) : ['Photography'];
    const tagsHtml = tagsList.map(t => `<span style="background: rgba(255,255,255,0.1); padding: 4px 12px; border-radius: 20px; font-size: 12px; color: rgba(255,255,255,0.8);">#${t}</span>`).join('');

    return `
    <div style="background: rgba(30, 30, 30, 0.6); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; overflow: hidden; display: flex; flex-direction: ${isEven ? 'row' : 'row-reverse'}; gap: 24px; align-items: center; transition: transform 0.3s;" class="story-item" id="story-item-${img.id}">
      <div style="flex: 1;">
        <img src="${img.url}" alt="${img.title}" style="width: 100%; height: 300px; object-fit: cover; border-radius: 12px;" />
      </div>

      <div style="flex: 1; padding: 24px;">
        <h3 style="color: white; font-size: 24px; font-weight: 300; margin-bottom: 12px;">${img.title}</h3>
        <p style="color: rgba(255,255,255,0.6); font-size: 14px; line-height: 1.6;">${img.description || ''}</p>
        <div style="margin-top: 20px; display: flex; gap: 8px; flex-wrap: wrap;">
          <span style="background: rgba(255,255,255,0.1); padding: 4px 12px; border-radius: 20px; font-size: 12px; color: rgba(255,255,255,0.8);">#${img.category || 'Gallery'}</span>
          ${tagsHtml}
        </div>
      </div>
    </div>
    `;
  }).join('');
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', loadStoryTimeline);
} else {
  loadStoryTimeline();
}
