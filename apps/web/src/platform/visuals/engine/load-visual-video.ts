export function loadVisualVideo(videoUrl: string): Promise<HTMLVideoElement> {
  return new Promise((resolve, reject) => {
    const video = document.createElement('video');
    video.src = videoUrl;
    if (videoUrl.startsWith('http')) {
      video.crossOrigin = 'anonymous';
    }
    video.loop = true;
    video.muted = true;
    video.playsInline = true;
    video.autoplay = true;

    video.addEventListener(
      'loadeddata',
      () => {
        video.play().catch(() => {
          // Ignore autoplay errors, the video will still be available as a texture.
        });
        resolve(video);
      },
      { once: true },
    );

    video.addEventListener(
      'error',
      () => {
        reject(new Error(`Failed to load visual video: ${videoUrl}`));
      },
      { once: true },
    );

    video.load();
  });
}
