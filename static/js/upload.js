function openUploadModal() {
  document.getElementById('upload-modal')?.classList.add('is-open');
}

function closeUploadModal() {
  document.getElementById('upload-modal')?.classList.remove('is-open');
  document.getElementById('upload-form')?.reset();
}

function initUpload() {
  const form = document.getElementById('upload-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
      const res = await fetch('/api/images/upload', {
        method: 'POST',
        body: new FormData(form),
        credentials: 'include',
      });
      if (!res.ok) {
        const data = await res.json();
        alert('上传失败：' + (data.error || data.detail || '发生错误'));
        return;
      }
      const data = await res.json();
      if (data.success) {
        alert('上传成功！');
        closeUploadModal();
        window.location.reload();
      } else {
        alert('上传失败：' + (data.error || '发生错误'));
      }
    } catch (err) {
      alert('网络错误，请重试');
    }
  });
}

initUpload();

window.openUploadModal = openUploadModal;
window.closeUploadModal = closeUploadModal;
