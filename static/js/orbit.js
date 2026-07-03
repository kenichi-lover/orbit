// 核心配置
const config = {
  imageUrls: [
    "https://picsum.photos/400/400?random=1",
    "https://picsum.photos/400/400?random=2", 
    "https://picsum.photos/400/400?random=3",
    "https://picsum.photos/400/400?random=4",
    "https://picsum.photos/400/400?random=5",
    "https://picsum.photos/400/400?random=6",
    "https://picsum.photos/400/400?random=7",
    "https://picsum.photos/400/400?random=8",
    "https://picsum.photos/400/400?random=9",
    "https://picsum.photos/400/400?random=10",
    "https://picsum.photos/400/400?random=11",
    "https://picsum.photos/400/400?random=12",
  ],
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
export function initOrbit() {
  initPhotos();
  initSteam();
  initThumbnails();
  initControls();
  animate();
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
  
  requestAnimationFrame(animate);
}

/**
 * 显示详情
 */
function showDetail(index) {
  const detail = document.getElementById("detail-panel");
  if (detail) {
    detail.style.display = "block";
    console.log(`Photo ${index}`);
  }
}

