from __future__ import annotations

from pathlib import Path
from typing import Any

import pygame


class SilentSound:
    """Fallback object used when pygame mixer is unavailable."""

    def play(self, *args: Any, **kwargs: Any) -> None:
        """Mimic ``pygame.mixer.Sound.play`` without producing audio.

        Args:
            *args: Ignored positional arguments kept for API compatibility.
            **kwargs: Ignored keyword arguments kept for API compatibility.

        Returns:
            None.
        """
        return None

    def stop(self) -> None:
        """Mimic ``pygame.mixer.Sound.stop`` for silent fallback sounds.

        Returns:
            None.
        """
        return None

    def set_volume(self, volume: float) -> None:
        """Accept a volume value without doing anything.

        Args:
            volume: Requested playback volume.

        Returns:
            None.
        """
        return None


class ResourceManager:
    """Loads and plays audio assets with graceful fallback."""

    def __init__(self, assets_dir: Path, music_volume: float, sfx_volume: float) -> None:
        """Prepare audio and image caches for the project assets.

        Args:
            assets_dir: Root assets directory that contains ``sounds`` and
                ``images``.
            music_volume: Playback volume used for looping music tracks.
            sfx_volume: Playback volume used for sound effects.

        Returns:
            None.
        """
        self.assets_dir = assets_dir
        self.sounds_dir = assets_dir / "sounds"
        self.images_dir = assets_dir / "images"
        self.audio_enabled = False
        self._music_volume = music_volume
        self._sfx_volume = sfx_volume
        self._music_channel = None
        self._current_music = None
        self._sound_cache: dict[str, pygame.mixer.Sound] = {}
        self._image_cache: dict[str, pygame.Surface] = {}
        self._round_sprite_cache: dict[tuple[str, int], pygame.Surface] = {}
        self._missing_images: set[str] = set()

        try:
            pygame.mixer.init()
            self.audio_enabled = True
        except pygame.error:
            self.audio_enabled = False

    def get_sound(self, name: str, fallback: str | None = None) -> pygame.mixer.Sound | SilentSound:
        """Load or retrieve a cached sound effect by name.

        Args:
            name: Sound identifier without file extension.
            fallback: Optional secondary sound name used when ``name`` is
                missing.

        Returns:
            Loaded ``pygame.mixer.Sound`` instance when audio is available, or a
            ``SilentSound`` fallback otherwise.
        """
        if not self.audio_enabled:
            return SilentSound()
        if name in self._sound_cache:
            return self._sound_cache[name]
        file_path = self.sounds_dir / f"{name}.wav"
        if not file_path.exists():
            return self.get_sound(fallback) if fallback is not None else SilentSound()
        sound = pygame.mixer.Sound(str(file_path))
        sound.set_volume(self._sfx_volume)
        self._sound_cache[name] = sound
        return sound

    def play_sound(self, name: str, fallback: str | None = None) -> None:
        """Play a one-shot sound effect.

        Args:
            name: Sound identifier without file extension.
            fallback: Optional fallback sound identifier.

        Returns:
            None.
        """
        sound = self.get_sound(name, fallback=fallback)
        sound.play()

    def play_music(self, name: str) -> None:
        """Play or switch looping background music.

        Args:
            name: Music track identifier without file extension.

        Returns:
            None.
        """
        if not self.audio_enabled:
            return
        if self._current_music == name and self._music_channel is not None:
            return
        sound = self.get_sound(name)
        sound.set_volume(self._music_volume)
        if self._music_channel is not None:
            self._music_channel.stop()
        self._music_channel = sound.play(loops=-1)
        self._current_music = name

    def stop_music(self) -> None:
        """Stop the currently playing looping music track.

        Returns:
            None.
        """
        if self._music_channel is not None:
            self._music_channel.stop()
        self._current_music = None

    def get_image(self, relative_path: str | None) -> pygame.Surface | None:
        """Load and cache a sprite from ``assets/images``.

        Args:
            relative_path: Relative path inside the image directory.

        Returns:
            Loaded image surface, or ``None`` when the path is empty, unsafe, or
            the file cannot be loaded.
        """
        if not relative_path:
            return None

        normalized_path = relative_path.replace("\\", "/").strip("/")
        if not normalized_path:
            return None
        if normalized_path in self._missing_images:
            return None
        if normalized_path in self._image_cache:
            return self._image_cache[normalized_path]

        file_path = self._resolve_image_path(normalized_path)
        if file_path is None:
            self._missing_images.add(normalized_path)
            return None

        try:
            image = pygame.image.load(str(file_path)).convert_alpha()
        except pygame.error:
            self._missing_images.add(normalized_path)
            return None

        self._image_cache[normalized_path] = image
        return image

    def get_round_sprite(self, relative_path: str | None, diameter: int) -> pygame.Surface | None:
        """Load an image and crop it into a circular sprite.

        Args:
            relative_path: Relative path inside the image directory.
            diameter: Desired output diameter in pixels.

        Returns:
            Circularly masked surface scaled to the requested diameter, or
            ``None`` when the source image is unavailable.
        """
        if not relative_path or diameter <= 0:
            return None

        normalized_path = relative_path.replace("\\", "/").strip("/")
        cache_key = (normalized_path, diameter)
        if cache_key in self._round_sprite_cache:
            return self._round_sprite_cache[cache_key]

        image = self.get_image(normalized_path)
        if image is None:
            return None

        scaled = pygame.transform.smoothscale(image, (diameter, diameter))
        mask = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        pygame.draw.circle(mask, (255, 255, 255, 255), (diameter // 2, diameter // 2), diameter // 2)

        rounded = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        rounded.blit(scaled, (0, 0))
        rounded.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        self._round_sprite_cache[cache_key] = rounded
        return rounded

    def _resolve_image_path(self, relative_path: str) -> Path | None:
        """Resolve a safe absolute path inside the image directory.

        Args:
            relative_path: Candidate relative path inside ``assets/images``.

        Returns:
            Absolute file path when the image exists inside the image root, or
            ``None`` when the path is invalid or points outside the root.
        """
        try:
            images_root = self.images_dir.resolve()
            file_path = (self.images_dir / relative_path).resolve()
        except OSError:
            return None

        try:
            file_path.relative_to(images_root)
        except ValueError:
            return None

        if not file_path.is_file():
            return None

        return file_path
