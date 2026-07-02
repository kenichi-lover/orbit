// 核心配置
const config = {
    imageUrls: [
        "https://picsum.photos/400/400?random=1",
        "https://picsum.photos/400/400?random=2",
        "https://picsum.photos/400/400?random=3",
    ],

    orbitRadius: 280,
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
    animate();
}


/**
 * 初始化图片
 */
function initPhotos() {

    const ring = document.getElementById("orbit-ring");

    config.imageUrls.forEach((url, index) => {

        const img = document.createElement("img");

        img.src = url;
        img.className = "photo-item";
        img.dataset.index = index;

        img.addEventListener("mouseenter", () => {
            config.isAutoRotate = false;
        });

        img.addEventListener("mouseleave", () => {
            config.isAutoRotate = true;
        });

        img.addEventListener("click", () => {
            showDetail(index);
        });

        ring.appendChild(img);

    });

}


/**
 * 动画循环
 */
function animate() {

    const photos = document.querySelectorAll(".photo-item");

    if (config.isAutoRotate) {
        rotation += config.rotationSpeed;
    }

    const step = (Math.PI * 2) / photos.length;

    photos.forEach((photo, index) => {

        const angle = step * index + rotation;

        const x = Math.cos(angle) * config.orbitRadius;

        const y = Math.sin(angle) * config.orbitRadius;

        photo.style.transform =
            `translate(-50%, -50%) translate3d(${x}px, ${y}px, 0)`;

    });

    requestAnimationFrame(animate);

}


/**
 * 显示详情
 */
function showDetail(index) {

    const detail = document.getElementById("detail-panel");

    detail.style.display = "block";

    console.log(`Photo ${index}`);

}
