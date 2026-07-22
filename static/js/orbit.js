// 核心配置
const config = {
  imageUrls: [],
  imagesInfo: [],
  orbitRadius: 320,
  orbitLayers: 2, // 2层轨道：上层和下层
  layerPhotoCounts: [6, 4],
  layerRadii: [340, 260],
  rotationSpeed: 0.005,
  isAutoRotate: true,
};

// 当前旋转角度
let rotation = 0;

/**
 * 初始化 Orbit
 */
export async function initOrbit() {
  try {
    const res = await fetch('/api/images');
    const data = await res.json();
    if (data.images && data.images.length > 0) {
      config.imageUrls = data.images.map(img => img.url);
      config.imagesInfo = data.images;
      
      // Update layer photo counts based on total images
      const total = config.imageUrls.length;
      if (total >= 10) {
        config.layerPhotoCounts = [Math.ceil(total * 0.6), Math.floor(total * 0.4)];
      } else {
        config.layerPhotoCounts = [total, 0];
        config.orbitLayers = 1;
      }
    }
  } catch(e) {
    console.error('Error fetching images', e);
  }
  
  initPhotos();
  initSteam();
  initThumbnails();
  initNavigator();
  initControls();
  animate();
}

/**
 * 初始化轨道示意图（Navigator）
 */
function initNavigator() {
  const container = document.getElementById("navigator");
  const canvas = document.getElementById("navigator-canvas");
  if (!container || !canvas) return;

  const dpr = window.devicePixelRatio || 1;
  const rect = container.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  const ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);

  const w = rect.width;
  const h = rect.height;
  const cx = w / 2;
  const cy = h / 2;

  // 最大半径对应外层轨道
  const maxRadius = Math.min(cx, cy) - 8;

  function draw() {
    ctx.clearRect(0, 0, w, h);

    // 画装饰环（俯视同心圆）
    const radii = config.layerRadii.map(r => (r / config.orbitRadius) * maxRadius);

    // 外环
    ctx.beginPath();
    ctx.arc(cx, cy, radii[0], 0, Math.PI * 2);
    ctx.strokeStyle = "rgba(255, 255, 255, 0.12)";
    ctx.lineWidth = 1;
    ctx.stroke();

    // 内环
    ctx.beginPath();
    ctx.arc(cx, cy, radii[1], 0, Math.PI * 2);
    ctx.strokeStyle = "rgba(255, 255, 255, 0.15)";
    ctx.lineWidth = 1;
    ctx.stroke();

    // 中心点
    ctx.beginPath();
    ctx.arc(cx, cy, 3, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(255, 180, 100, 0.6)";
    ctx.fill();

    // 画照片点
    const layers = document.querySelectorAll("#orbit-ring .photo-layer");
    layers.forEach((layer) => {
      const photos = layer.querySelectorAll(".photo-item");
      const layerIndex = parseInt(layer.dataset.layer);
      const radius = parseFloat(layer.dataset.radius) || config.orbitRadius;
      const photoCount = photos.length;
      const angleStep = (Math.PI * 2) / photoCount;
      const scaledRadius = (radius / config.orbitRadius) * maxRadius;

      photos.forEach((photo) => {
        // 读取当前 transform 中的 x, z 值来映射到俯视 2D
        const t = photo.style.transform;
        const txMatch = t.match(/translate3d\(([-\d.]+)px/);
        if (!txMatch) return;
        const tx = parseFloat(txMatch[1]);
        const tzMatch = t.match(/translate3d\([^,]+,[^,]+,([-\d.]+)px\)/);
        const tz = tzMatch ? parseFloat(tzMatch[1]) : 0;

        // 俯视投影：XZ 平面 -> 2D canvas
        // 将轨道空间映射到 navigator 空间
        const nx = cx + (tx / config.orbitRadius) * maxRadius;
        const ny = cy + (tz / config.orbitRadius) * maxRadius;

        const isSelected = photo.classList.contains("navigator-highlight");

        ctx.beginPath();
        ctx.arc(nx, ny, isSelected ? 5 : 3, 0, Math.PI * 2);
        ctx.fillStyle = isSelected
          ? "rgba(255, 200, 120, 0.95)"
          : "rgba(255, 220, 170, 0.7)";
        ctx.fill();

        if (isSelected) {
          ctx.beginPath();
          ctx.arc(nx, ny, 7, 0, Math.PI * 2);
          ctx.strokeStyle = "rgba(255, 200, 120, 0.4)";
          ctx.lineWidth = 1;
          ctx.stroke();
        }
      });
    });
  }

  // 每帧更新 navigator
  const origAnimate = animate;
  window._drawNavigator = draw;
}

/**
 * 初始化图片 - 围绕中心点的3D轨道
 */
function initPhotos() {
  const ring = document.getElementById("orbit-ring");
  if (!ring) return;
  
  // 清空现有内容
  ring.innerHTML = '';
  
  // 为每层轨道创建照片
  for (let layer = 0; layer < config.orbitLayers; layer++) {
    const layerPhotos = document.createElement('div');
    layerPhotos.className = `photo-layer layer-${layer}`;
    layerPhotos.dataset.layer = layer;
    layerPhotos.dataset.radius = config.layerRadii[layer] || config.orbitRadius;
    
    // 每层放置不同数量的照片
    const photoCount = config.layerPhotoCounts[layer] || 6;
    const radius = config.layerRadii[layer] || config.orbitRadius;
    const angleStep = (Math.PI * 2) / photoCount;
    
    for (let i = 0; i < photoCount; i++) {
      const img = document.createElement("img");
      img.src = config.imageUrls[i + layer * photoCount] || config.imageUrls[i];
      img.className = "photo-item";
      img.dataset.index = i + layer * photoCount;
      img.dataset.layer = layer;
      
      // 设置初始位置 - 围绕中心点
      const angle = angleStep * i;
      const x = Math.cos(angle) * radius;
      const y = Math.sin(angle) * radius;
      const z = layer * 80 - 80;
      
      img.style.setProperty('--initial-x', `${x}px`);
      img.style.setProperty('--initial-y', `${y}px`);
      img.style.setProperty('--initial-z', `${z}px`);
      
      img.addEventListener("mouseenter", () => {
        config.isAutoRotate = false;
      });
      img.addEventListener("mouseleave", () => {
        config.isAutoRotate = true;
      });
      img.addEventListener("click", () => {
        showDetail(parseInt(img.dataset.index));
      });
      
      layerPhotos.appendChild(img);
    }
    ring.appendChild(layerPhotos);
  }
}

/**
 * 初始化蒸汽效果
 */
function initSteam() {
  const core = document.getElementById("orbit-core");
  if (!core) return;
  // 当前没有具体蒸汽效果实现，保留占位函数以避免脚本错误。
}

function initThumbnails() {
  const thumbnailBar = document.getElementById("thumbnail-bar");
  if (!thumbnailBar) return;
  thumbnailBar.innerHTML = "";

  config.imageUrls.forEach((url, index) => {
    const thumb = document.createElement("img");
    thumb.src = url;
    thumb.className = "thumbnail-item";
    thumb.dataset.index = index;
    thumb.addEventListener("click", () => showDetail(index));
    thumbnailBar.appendChild(thumb);
  });
}

function initControls() {
  const autoBtn = document.getElementById("auto-rotate-btn");
  const pauseBtn = document.getElementById("pause-btn");
  const speedSlider = document.getElementById("speed-slider");
  const viewSlider = document.getElementById("view-slider");
  const orbitSystem = document.getElementById("orbit-system");
  
  if (autoBtn) {
    autoBtn.addEventListener("click", () => {
      config.isAutoRotate = !config.isAutoRotate;
      autoBtn.textContent = config.isAutoRotate ? "🔄 自动旋转" : "⏹️ 停止旋转";
    });
  }
  
  if (pauseBtn) {
    pauseBtn.addEventListener("click", () => {
      config.isAutoRotate = false;
      if (autoBtn) autoBtn.textContent = "🔄 自动旋转";
    });
  }

  if (speedSlider) {
    // 根据滑块值 (0-100) 动态计算旋转速度，50 对应基础速度 0.005
    speedSlider.addEventListener("input", (e) => {
      const val = parseInt(e.target.value, 10);
      config.rotationSpeed = 0.0001 + (val / 100) * 0.01;
    });
  }

  if (viewSlider && orbitSystem) {
    // 根据滑块值 (0-100) 动态计算俯仰视角 (0 到 70度)
    // 默认值 50 对应 35度左右
    const updateView = (val) => {
      const angle = (val / 100) * 70;
      orbitSystem.style.setProperty("--view-angle", `${angle}deg`);
    };
    
    viewSlider.addEventListener("input", (e) => {
      updateView(e.target.value);
    });
    
    // 初始化视角
    updateView(viewSlider.value);
  }
}

/**
 * 动画循环 - 围绕中心点的3D轨道
 */
function animate() {
  // 只选择我们创建的内部照片层
  const layers = document.querySelectorAll('#orbit-ring .photo-layer');
  if (config.isAutoRotate) {
    rotation += config.rotationSpeed;
  }
  
  layers.forEach((layer) => {
    const photos = layer.querySelectorAll('.photo-item');
    const layerIndex = parseInt(layer.dataset.layer);
    const radius = parseFloat(layer.dataset.radius) || config.orbitRadius;
    const photoCount = photos.length;
    const angleStep = (Math.PI * 2) / photoCount;
    
    photos.forEach((photo, index) => {
      const angle = angleStep * index + rotation;

      // 将轨道放在 XZ 平面（环面朝向观察者），这样有真实的前后深度
      const x = Math.cos(angle) * radius;
      const z = Math.sin(angle) * radius; // 用作 translateZ

      // 不同层在 Y 轴上有少量高度偏移，形成上下层次
      const layerOffset = 90; // 每层垂直间距
      const y = (layerIndex - (config.orbitLayers - 1) / 2) * layerOffset;

      // 根据 Z 值计算归一化深度 (0..1)，用于缩放与透明度
      const depthNorm = (z + radius) / (radius * 2);
      const scale = 0.7 + depthNorm * 0.8; // 靠近的图片更大
      const opacity = 0.4 + depthNorm * 0.6; // 靠近的更亮

      photo.style.transform = `translate(-50%,-50%) translate3d(${x}px, ${y}px, ${z}px) scale(${scale})`;
      photo.style.opacity = opacity;
    });
  });
  
  // 更新 navigator
  if (window._drawNavigator) {
    window._drawNavigator();
  }
  
  requestAnimationFrame(animate);
}

/**
 * 显示详情
 */
function showDetail(index) {
  const detail = document.getElementById("detail-panel");
  if (detail) {
    const info = config.imagesInfo[index] || {};
    
    // Update content
    const titleEl = detail.querySelector('.detail-title');
    if (titleEl) titleEl.textContent = info.title || `Photo ${index}`;
    
    const catEl = detail.querySelector('.detail-category');
    if (catEl) catEl.textContent = info.category || 'Gallery';
    
    const descEl = detail.querySelector('.detail-description');
    if (descEl) descEl.textContent = info.description || '';
    
    const dateEl = detail.querySelector('.detail-date');
    if (dateEl) dateEl.textContent = info.created_at ? new Date(info.created_at).toLocaleDateString() : '2024.05.12';
    
    const authorEl = detail.querySelector('.detail-camera');
    if (authorEl) authorEl.textContent = info.user_name || 'System';
    
    const tagsContainer = detail.querySelector('.detail-tags');
    if (tagsContainer) {
      tagsContainer.innerHTML = '';
      (info.tags || ['Photography']).forEach(tag => {
        const span = document.createElement('span');
        span.className = 'tag';
        span.textContent = `#${tag}`;
        tagsContainer.appendChild(span);
      });
    }
    
    detail.style.display = "block";
  }
}


