import os
import tempfile
import pygame


def play_intro_video(video_path="assets/video/intro.mp4"):
    """Play an MP4 intro video in fullscreen with synchronized audio in Pygame.

    Safely skips if the file or dependencies are missing so tests and teammates
    without the video never crash. Press SPACE, ENTER, ESC, or click to skip.
    """
    if not os.path.exists(video_path):
        return

    try:
        import cv2
    except ImportError:
        return

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return

    pygame.init()
    screen = pygame.display.get_surface()
    if screen is None:
        # Match the native monitor resolution in fullscreen mode
        info = pygame.display.Info()
        screen = pygame.display.set_mode(
            (info.current_w, info.current_h),
            pygame.FULLSCREEN | pygame.SCALED,
        )
        pygame.display.set_caption("Memory Heist")

    # Extract and start audio track if available
    temp_audio_path = None
    has_audio = False
    try:
        try:
            from moviepy import VideoFileClip
        except ImportError:
            from moviepy.editor import VideoFileClip

        clip = VideoFileClip(video_path)
        if clip.audio is not None:
            fd, temp_audio_path = tempfile.mkstemp(suffix=".mp3")
            os.close(fd)
            clip.audio.write_audiofile(temp_audio_path, logger=None)
            pygame.mixer.init()
            pygame.mixer.music.load(temp_audio_path)
            pygame.mixer.music.play()
            has_audio = True
        clip.close()
    except Exception:
        has_audio = False

    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        fps = 30.0

    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if has_audio:
                    pygame.mixer.music.stop()
                cap.release()
                if temp_audio_path and os.path.exists(temp_audio_path):
                    try:
                        os.remove(temp_audio_path)
                    except OSError:
                        pass
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_SPACE,
                pygame.K_RETURN,
                pygame.K_ESCAPE,
            ):
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                running = False

        if not running:
            break

        ret, frame = cap.read()
        if not ret:
            break

        # Convert BGR (OpenCV) to RGB (Pygame) and fit fullscreen resolution
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        win_w, win_h = screen.get_size()
        vid_h, vid_w = frame_rgb.shape[:2]

        scale = min(win_w / vid_w, win_h / vid_h)
        new_w = int(vid_w * scale)
        new_h = int(vid_h * scale)
        resized = cv2.resize(frame_rgb, (new_w, new_h), interpolation=cv2.INTER_AREA)

        surface = pygame.image.frombuffer(resized.tobytes(), (new_w, new_h), "RGB")
        screen.fill((0, 0, 0))
        screen.blit(surface, ((win_w - new_w) // 2, (win_h - new_h) // 2))
        pygame.display.flip()

        clock.tick(fps)

    # Clean up audio and temporary files before starting the main game
    if has_audio:
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
    cap.release()

    if temp_audio_path and os.path.exists(temp_audio_path):
        try:
            os.remove(temp_audio_path)
        except OSError:
            pass