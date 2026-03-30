from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from src.app import App


class BaseScene:
    """Shared scene helpers and lifecycle hooks."""

    def __init__(self, app: App) -> None:
        """Store the application reference shared by all scenes.

        Args:
            app: Running application instance.

        Returns:
            None.
        """
        self.app = app

    def on_enter(self) -> None:
        """Run scene-specific logic when the scene becomes active.

        Returns:
            None. Subclasses override this hook when needed.
        """
        return None

    def on_exit(self) -> None:
        """Run scene-specific cleanup before switching away.

        Returns:
            None. Subclasses override this hook when needed.
        """
        return None

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle a pygame event routed to this scene.

        Args:
            event: Event received from the main loop.

        Returns:
            None. Subclasses override this hook when needed.
        """
        return None

    def update(self, dt: float) -> None:
        """Advance scene state for a single frame.

        Args:
            dt: Frame delta time in seconds.

        Returns:
            None. Subclasses override this hook when needed.
        """
        return None

    def render(self, surface: pygame.Surface) -> None:
        """Draw the scene to the provided surface.

        Args:
            surface: Target surface used as the current framebuffer.

        Returns:
            None. Subclasses override this hook when needed.
        """
        return None

    @staticmethod
    def mix_color(
        start: tuple[int, int, int],
        end: tuple[int, int, int],
        factor: float,
    ) -> tuple[int, int, int]:
        """Blend two RGB colors using a linear interpolation factor.

        Args:
            start: Color used when ``factor`` equals ``0``.
            end: Color used when ``factor`` equals ``1``.
            factor: Blend factor that will be clamped to ``[0, 1]``.

        Returns:
            Interpolated RGB color tuple.
        """
        clamped = max(0.0, min(1.0, factor))
        return tuple(int(a + (b - a) * clamped) for a, b in zip(start, end))

    @staticmethod
    def boost_color(color: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
        """Brighten an RGB color toward white.

        Args:
            color: Base RGB color.
            amount: Brightening factor where ``0`` keeps the original color and
                larger values move channels closer to ``255``.

        Returns:
            Brightened RGB color tuple.
        """
        return tuple(min(255, int(component + (255 - component) * amount)) for component in color)

    def draw_glow(
        self,
        surface: pygame.Surface,
        center: tuple[int, int] | tuple[float, float],
        radius: int,
        color: tuple[int, int, int],
        alpha: int = 90,
    ) -> None:
        """Draw a layered glow sprite around a point.

        Args:
            surface: Surface that receives the glow.
            center: Glow center in pixel coordinates.
            radius: Base glow radius in pixels.
            color: RGB color of the glow.
            alpha: Approximate overall transparency of the glow.

        Returns:
            None.
        """
        if radius <= 0 or alpha <= 0:
            return
        glow = pygame.Surface((radius * 2 + 6, radius * 2 + 6), pygame.SRCALPHA)
        local_center = (radius + 3, radius + 3)
        for scale, strength in ((1.0, 0.16), (0.72, 0.28), (0.45, 0.44)):
            current_radius = max(1, int(radius * scale))
            current_alpha = max(1, int(alpha * strength))
            pygame.draw.circle(glow, (*color, current_alpha), local_center, current_radius)
        surface.blit(glow, (int(center[0] - local_center[0]), int(center[1] - local_center[1])))

    def draw_panel(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        *,
        accent: tuple[int, int, int],
        fill: tuple[int, int, int, int] = (12, 16, 24, 220),
    ) -> None:
        """Draw a reusable translucent UI panel.

        Args:
            surface: Surface that receives the panel.
            rect: Destination rectangle for the panel.
            accent: RGB color used for borders and highlights.
            fill: RGBA color used for the panel background.

        Returns:
            None.
        """
        shadow = pygame.Surface((rect.width + 24, rect.height + 24), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 72), shadow.get_rect(), border_radius=28)
        surface.blit(shadow, (rect.x - 12, rect.y + 10))

        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        panel_rect = panel.get_rect()
        pygame.draw.rect(panel, fill, panel_rect, border_radius=20)
        pygame.draw.rect(panel, (*accent, 220), panel_rect, width=2, border_radius=20)
        pygame.draw.line(panel, (255, 255, 255, 22), (22, 18), (rect.width - 22, 18), 2)
        pygame.draw.line(panel, (*accent, 110), (22, rect.height - 18), (rect.width - 22, rect.height - 18), 2)
        surface.blit(panel, rect.topleft)

    def draw_backdrop(
        self,
        surface: pygame.Surface,
        *,
        accent: tuple[int, int, int] = (209, 93, 74),
        secondary: tuple[int, int, int] = (101, 173, 244),
    ) -> None:
        """Paint an animated background shared by menu-like scenes.

        Args:
            surface: Surface that receives the background.
            accent: Primary RGB accent color used for larger glows.
            secondary: Secondary RGB accent color used for diagonal overlays.

        Returns:
            None.
        """
        width, height = surface.get_size()
        top_color = (8, 11, 17)
        bottom_color = (33, 17, 22)

        for y in range(0, height, 4):
            blend = y / max(1, height - 1)
            color = self.mix_color(top_color, bottom_color, blend)
            pygame.draw.rect(surface, color, (0, y, width, 4))

        time_value = pygame.time.get_ticks() / 1000.0
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        slant_offset = int((time_value * 46) % 84)

        for x in range(-height, width + height, 84):
            pygame.draw.line(
                overlay,
                (*secondary, 16),
                (x + slant_offset, 0),
                (x - height + slant_offset, height),
                1,
            )

        for y in range(0, height, 64):
            pulse = 10 + int(6 * (0.5 + 0.5 * math.sin(time_value * 1.2 + y * 0.04)))
            pygame.draw.line(overlay, (255, 255, 255, pulse), (0, y), (width, y), 1)

        self.draw_glow(overlay, (int(width * 0.16), int(height * 0.2)), 180, accent, 125)
        self.draw_glow(overlay, (int(width * 0.82), int(height * 0.22)), 150, secondary, 80)
        self.draw_glow(overlay, (int(width * 0.55), int(height * 0.82)), 210, accent, 58)
        surface.blit(overlay, (0, 0))
