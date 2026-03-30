from __future__ import annotations

import math
from typing import Callable

import pygame


class Button:
    """Interactive menu button with keyboard and mouse friendly visuals."""

    def __init__(self, rect: pygame.Rect, text: str, callback: Callable[[], None]) -> None:
        """Store button geometry, label, and callback.

        Args:
            rect: Button area in screen coordinates.
            text: Caption rendered inside the button.
            callback: Function executed when the button is activated.

        Returns:
            None.
        """
        self.rect = rect
        self.text = text
        self.callback = callback
        self.hovered = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Update hover state and react to mouse clicks.

        Args:
            event: Pygame event received during the current frame.

        Returns:
            ``True`` when the button was clicked and its callback was invoked,
            otherwise ``False``.
        """
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()
                return True
        return False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, selected: bool = False) -> None:
        """Render the button using the current interactive state.

        Args:
            surface: Target surface where the button should be drawn.
            font: Font used to render the button label.
            selected: Whether the button is currently selected through keyboard
                navigation.

        Returns:
            None.
        """
        active = self.hovered or selected
        pulse = 0.55 + 0.45 * math.sin(pygame.time.get_ticks() / 180)

        shadow = pygame.Surface((self.rect.width + 18, self.rect.height + 18), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 76), shadow.get_rect(), border_radius=20)
        surface.blit(shadow, (self.rect.x - 9, self.rect.y + 8))

        button = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        button_rect = button.get_rect()
        fill = (55, 32, 34, 235) if active else (20, 26, 34, 220)
        border = (241, 161, 99) if active else (104, 138, 171)
        inner_alpha = 50 + int(40 * pulse) if active else 18

        pygame.draw.rect(button, fill, button_rect, border_radius=16)
        pygame.draw.rect(button, (*border, 225), button_rect, width=2, border_radius=16)
        pygame.draw.rect(button, (255, 255, 255, inner_alpha), button_rect.inflate(-18, -28), width=1, border_radius=12)
        pygame.draw.line(button, (*border, 110), (18, 14), (self.rect.width - 18, 14), 2)

        surface.blit(button, self.rect.topleft)

        label_color = (250, 241, 224) if active else (226, 232, 240)
        label = font.render(self.text, True, label_color)
        surface.blit(label, label.get_rect(center=(self.rect.centerx, self.rect.centery - 1)))
