export let currentQuery = "";
export let currentCategory = "";
export let currentTag = "";
export let allImagesData = [];

let onFilterChangeCallback = null;

export function setFilterCallback(callback) {
  onFilterChangeCallback = callback;
}

export function getFilterState() {
  return { currentQuery, currentCategory, currentTag };
}

export function setQuery(query) {
  currentQuery = query;
  applyFilters();
}

export async function populateFilterPanel() {
  if (allImagesData.length === 0) {
    try {
      const res = await fetch('/api/images');
      const data = await res.json();
      allImagesData = data.images || [];
    } catch (e) {
      console.error(e);
      return;
    }
  }
  
  const categories = [...new Set(allImagesData.map(img => img.category).filter(Boolean))];
  const tagsSet = new Set();
  allImagesData.forEach(img => {
    if (img.tags && Array.isArray(img.tags)) {
      img.tags.forEach(t => tagsSet.add(t));
    }
  });
  const tags = [...tagsSet];
  
  const catContainer = document.getElementById("filter-categories-container");
  if (catContainer) {
    catContainer.innerHTML = categories.map(cat => 
      `<button class="filter-chip ${currentCategory === cat ? 'active' : ''}" data-cat="${cat}">${cat}</button>`
    ).join('');
    
    catContainer.querySelectorAll('.filter-chip').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const cat = e.target.getAttribute('data-cat');
        currentCategory = currentCategory === cat ? "" : cat;
        populateFilterPanel(); 
        applyFilters();
      });
    });
  }
  
  const tagContainer = document.getElementById("filter-tags-container");
  if (tagContainer) {
    tagContainer.innerHTML = tags.map(tag => 
      `<button class="filter-chip ${currentTag === tag ? 'active' : ''}" data-tag="${tag}">#${tag}</button>`
    ).join('');
    
    tagContainer.querySelectorAll('.filter-chip').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const tag = e.target.getAttribute('data-tag');
        currentTag = currentTag === tag ? "" : tag;
        populateFilterPanel();
        applyFilters();
      });
    });
  }
}

export function applyFilters() {
  // Filter orbit photos
  const photoItems = document.querySelectorAll('.photo-item');
  photoItems.forEach((item, index) => {
    let show = true;
    const imgData = allImagesData[parseInt(item.dataset.index || index)];
    
    if (currentQuery && !item.src.toLowerCase().includes(currentQuery)) {
      // Because we lack title data on the img itself, we use allImagesData if available
      if (imgData && imgData.title && imgData.title.toLowerCase().includes(currentQuery)) {
         // Keep it
      } else {
         show = false;
      }
    }
    
    if (imgData) {
      if (currentCategory && imgData.category !== currentCategory) show = false;
      if (currentTag && (!imgData.tags || !imgData.tags.includes(currentTag))) show = false;
    }

    item.style.display = show ? 'block' : 'none';
  });

  // Filter thumbnails
  const thumbItems = document.querySelectorAll('.thumbnail-item');
  thumbItems.forEach((item, index) => {
    let show = true;
    const imgData = allImagesData[parseInt(item.dataset.index || index)];
    
    if (currentQuery && !item.src.toLowerCase().includes(currentQuery)) {
      if (imgData && imgData.title && imgData.title.toLowerCase().includes(currentQuery)) {
      } else {
         show = false;
      }
    }
    
    if (imgData) {
      if (currentCategory && imgData.category !== currentCategory) show = false;
      if (currentTag && (!imgData.tags || !imgData.tags.includes(currentTag))) show = false;
    }

    item.style.display = show ? 'block' : 'none';
  });
  
  if (onFilterChangeCallback) {
    onFilterChangeCallback();
  }
}

export function initFilterPanel() {
  const filterBtn = document.getElementById("nav-filter");
  const filterPanel = document.getElementById("nav-filter-panel");
  const filterClear = document.getElementById("nav-filter-clear");
  
  if (!filterBtn || !filterPanel) return;

  filterBtn.addEventListener("click", () => {
    if (filterPanel.style.display === "none") {
      filterPanel.style.display = "block";
      populateFilterPanel();
    } else {
      filterPanel.style.display = "none";
    }
  });
  
  if (filterClear) {
    filterClear.addEventListener("click", () => {
      currentCategory = "";
      currentTag = "";
      populateFilterPanel();
      applyFilters();
    });
  }
  
  document.addEventListener("click", (e) => {
    if (!filterBtn.contains(e.target) && !filterPanel.contains(e.target)) {
      filterPanel.style.display = "none";
    }
  });
}

