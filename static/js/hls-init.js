document.querySelectorAll("video[data-src]").forEach((video) => {
  const src = video.dataset.src;

  if (video.canPlayType("application/vnd.apple.mpegurl")) {
    // Safari has native HLS support.
    video.src = src;
    return;
  }

  if (window.Hls && window.Hls.isSupported()) {
    const hls = new window.Hls();
    hls.loadSource(src);
    hls.attachMedia(video);
    return;
  }

  const tile = video.closest(".camera-tile");
  if (tile) {
    const notice = document.createElement("p");
    notice.textContent = "This browser can't play HLS.";
    tile.appendChild(notice);
  }
});
