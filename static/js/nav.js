export function initNav() {
  const navExplore = document.getElementById("nav-explore");
  const navStory = document.getElementById("nav-story");
  const orbitStage = document.getElementById("orbit-stage");
  const storyStage = document.getElementById("story-stage");
  const controlPanel = document.querySelector(".control-panel");
  const thumbnailBar = document.getElementById("thumbnail-bar");
  const navigatorEl = document.getElementById("navigator");

  navExplore.addEventListener("click", () => {
    navExplore.classList.add("active");
    navStory.classList.remove("active");
    
    orbitStage.style.display = "block";
    storyStage.style.display = "none";
    if(controlPanel) controlPanel.style.display = "flex";
    if(thumbnailBar) thumbnailBar.style.display = "flex";
    if(navigatorEl) navigatorEl.style.display = "block";
  });

  navStory.addEventListener("click", () => {
    navStory.classList.add("active");
    navExplore.classList.remove("active");
    
    orbitStage.style.display = "none";
    storyStage.style.display = "block";
    if(controlPanel) controlPanel.style.display = "none";
    if(thumbnailBar) thumbnailBar.style.display = "none";
    if(navigatorEl) navigatorEl.style.display = "none";
    
    renderStoryMode();
  });

  // Search functionality
  const searchInput = document.getElementById("nav-search-input");
  const searchTrigger = document.getElementById("nav-search-trigger");
  const searchBox = document.getElementById("nav-search-box");
  const searchClose = document.getElementById("nav-search-close");

  searchTrigger.addEventListener("click", () => {
    searchBox.classList.add("expanded");
    searchInput.focus();
  });

  searchClose.addEventListener("click", () => {
    searchBox.classList.remove("expanded");
    searchInput.value = "";
    filterImages("");
  });

  searchInput.addEventListener("input", (e) => {
    filterImages(e.target.value.trim().toLowerCase());
  });
}

function filterImages(query) {
  // Filter orbit photos
  const photoItems = document.querySelectorAll('.photo-item');
  photoItems.forEach(item => {
    const url = item.src.toLowerCase();
    
    // For now, if query is empty, show all.
    // If not empty, hide those that don't match. 
    // We can simulate tags by matching the image filename.
    if (!query || url.includes(query)) {
      item.style.display = 'block';
    } else {
      item.style.display = 'none';
    }
  });

  // Filter thumbnails
  const thumbItems = document.querySelectorAll('.thumbnail-item');
  thumbItems.forEach(item => {
    const url = item.src.toLowerCase();
    if (!query || url.includes(query)) {
      item.style.display = 'block';
    } else {
      item.style.display = 'none';
    }
  });
  
  // Re-render story mode if it's active
  const storyStage = document.getElementById("story-stage");
  if (storyStage && storyStage.style.display !== "none") {
    renderStoryMode(query);
  }
}

async function renderStoryMode(query = "") {
  const container = document.getElementById("story-timeline");
  if (!container) return;
  
  try {
    const res = await fetch('/api/images');
    const data = await res.json();
    let images = data.images || [];
    
    if (query) {
      images = images.filter(img => img.title.toLowerCase().includes(query) || img.url.toLowerCase().includes(query));
    }
    
    container.innerHTML = images.map((img, index) => {
      const isEven = index % 2 === 0;
      const tagsHtml = (img.tags || ['Photography']).map(t => `<span style="background: rgba(255,255,255,0.1); padding: 4px 12px; border-radius: 20px; font-size: 12px; color: rgba(255,255,255,0.8);">#${t}</span>`).join('');
      
      let editBtnHtml = '';
      if (window.currentUser) {
        editBtnHtml = `
          <button onclick="window.editStory('${img.id}')" style="margin-top: 16px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: white; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 12px; transition: background 0.2s;">
            编辑
          </button>
        `;
      }

      return `
      <div style="background: rgba(30, 30, 30, 0.6); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; overflow: hidden; display: flex; flex-direction: ${isEven ? 'row' : 'row-reverse'}; gap: 24px; align-items: center; transition: transform 0.3s;" class="story-item" id="story-item-${img.id}">
        <div style="flex: 1;">
          <img src="${img.url}" alt="${img.title}" style="width: 100%; height: 300px; object-fit: cover; border-radius: 12px;" />
        </div>
        
        <!-- View Mode -->
        <div id="story-view-${img.id}" style="flex: 1; padding: 24px;">
          <h3 style="color: white; font-size: 24px; font-weight: 300; margin-bottom: 12px;">${img.title}</h3>
          <p style="color: rgba(255,255,255,0.6); font-size: 14px; line-height: 1.6;">
            ${img.description}
          </p>
          <div style="margin-top: 20px; display: flex; gap: 8px; flex-wrap: wrap;">
            <span style="background: rgba(255,255,255,0.1); padding: 4px 12px; border-radius: 20px; font-size: 12px; color: rgba(255,255,255,0.8);">#${img.category}</span>
            ${tagsHtml}
          </div>
          ${editBtnHtml}
        </div>
        
        <!-- Edit Mode -->
        <div id="story-edit-${img.id}" style="flex: 1; padding: 24px; display: none;">
          <input type="text" id="edit-title-${img.id}" value="${img.title}" style="width: 100%; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.2); color: white; padding: 8px; margin-bottom: 12px; border-radius: 4px;">
          <textarea id="edit-desc-${img.id}" style="width: 100%; height: 100px; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.2); color: white; padding: 8px; margin-bottom: 12px; border-radius: 4px;">${img.description}</textarea>
          <input type="text" id="edit-cat-${img.id}" value="${img.category}" style="width: 100%; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.2); color: white; padding: 8px; margin-bottom: 12px; border-radius: 4px;" placeholder="Category">
          <input type="text" id="edit-tags-${img.id}" value="${(img.tags || ['Photography']).join(', ')}" style="width: 100%; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.2); color: white; padding: 8px; margin-bottom: 12px; border-radius: 4px;" placeholder="Tags (comma separated)">
          
          <div style="display: flex; gap: 10px;">
            <button onclick="window.saveStory('${img.id}')" style="background: white; color: black; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-weight: bold;">保存</button>
            <button onclick="window.cancelEditStory('${img.id}')" style="background: rgba(255,255,255,0.1); color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer;">取消</button>
            <button onclick="window.deleteStory('${img.id}')" style="background: rgba(255,50,50,0.8); color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; margin-left: auto;">删除</button>
          </div>
        </div>
      </div>
      `;
    }).join('');
  } catch (err) {
    console.error("Failed to load story mode images", err);
    container.innerHTML = '<p style="color: white; text-align: center;">加载叙事内容失败</p>';
  }
}

window.editStory = function(id) {
  document.getElementById(`story-view-${id}`).style.display = 'none';
  document.getElementById(`story-edit-${id}`).style.display = 'block';
};

window.cancelEditStory = function(id) {
  document.getElementById(`story-view-${id}`).style.display = 'block';
  document.getElementById(`story-edit-${id}`).style.display = 'none';
};

window.saveStory = async function(id) {
  const title = document.getElementById(`edit-title-${id}`).value;
  const description = document.getElementById(`edit-desc-${id}`).value;
  const category = document.getElementById(`edit-cat-${id}`).value;
  const tagsStr = document.getElementById(`edit-tags-${id}`).value;
  const tags = tagsStr.split(',').map(t => t.trim()).filter(t => t);
  
  try {
    const res = await fetch(`/api/images/${id}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ title, description, category, tags })
    });
    
    if (res.ok) {
      // Re-render
      renderStoryMode(document.getElementById("nav-search-input") ? document.getElementById("nav-search-input").value.trim().toLowerCase() : "");
    } else {
      alert("保存失败");
    }
  } catch (err) {
    alert("网络错误");
  }
};

window.deleteStory = async function(id) {
  if (!confirm("确定要删除此图片吗？")) return;
  
  try {
    const res = await fetch(`/api/images/${id}?hard=true`, {
      method: "DELETE"
    });
    
    if (res.ok) {
      renderStoryMode(document.getElementById("nav-search-input") ? document.getElementById("nav-search-input").value.trim().toLowerCase() : "");
    } else {
      alert("删除失败");
    }
  } catch (err) {
    alert("网络错误");
  }
};

