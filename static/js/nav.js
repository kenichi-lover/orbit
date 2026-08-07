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

  // Debounced search — wait 300ms after user stops typing
  let searchTimer = null;
  searchInput.addEventListener("input", (e) => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      filterImages(e.target.value.trim().toLowerCase());
      performSearch(e.target.value.trim());
    }, 300);
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

async function performSearch(query) {
  if (!query) return;

  try {
    const res = await fetch(`/api/search?q=${encodeURIComponent(query)}&limit=20`, { credentials: 'include' });
    const data = await res.json();
    // Store search results for use in story mode re-render
    window._searchResults = data.items || [];
  } catch (err) {
    console.error("Search failed", err);
  }
}

async function renderStoryMode(query = "") {
  if (window._storyRender) {
    await window._storyRender(query);
  }
}
