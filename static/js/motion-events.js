(function () {
  const banner = document.getElementById("motion-banner");
  let bannerTimer = null;

  function showBanner(cameraName) {
    if (!banner) return;
    banner.textContent = "Motion detected: " + cameraName;
    banner.classList.add("visible");
    clearTimeout(bannerTimer);
    bannerTimer = setTimeout(() => banner.classList.remove("visible"), 6000);
  }

  function enterPictureInPicture(video) {
    if (!video || !document.pictureInPictureEnabled || video.disablePictureInPicture) {
      return;
    }
    if (document.pictureInPictureElement === video) {
      return;
    }
    // Browsers may reject this outside a user gesture; that's fine, the
    // on-screen banner still shows either way.
    video.requestPictureInPicture().catch(() => {});
  }

  function handleMotionEvent(data) {
    const video = document.querySelector('video[data-camera-id="' + data.camera_id + '"]');
    const tile = video ? video.closest(".camera-tile") : null;
    const heading = tile ? tile.querySelector("h2") : null;
    const name = heading ? heading.textContent : data.camera_id;

    showBanner(name);
    enterPictureInPicture(video);
  }

  const source = new EventSource("/api/events/stream");
  source.onmessage = (message) => {
    let data;
    try {
      data = JSON.parse(message.data);
    } catch (err) {
      return;
    }
    if (data.event === "motion") {
      handleMotionEvent(data);
    }
  };
})();
