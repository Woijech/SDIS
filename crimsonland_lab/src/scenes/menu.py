from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.scenes.base import BaseScene
from src.ui.button import Button

if TYPE_CHECKING:
    from src.app import App


class MainMenuScene(BaseScene):
    """Main menu scene with keyboard and mouse navigation."""

    def __init__(self, app: App) -> None:
        """Create menu buttons and selection state.

        Args:
            app: Running application instance.

        Returns:
            None.
        """
        super().__init__(app)
        center_x = self.app.settings["screen_width"] // 2
        start_y = 266
        width = 320
        height = 56
        spacing = 18
        labels_callbacks = [
            ("Start Game", lambda: self.app.change_scene("game")),
            ("High Scores", lambda: self.app.change_scene("highscores")),
            ("Exit", self.app.quit),
        ]
        self.buttons = []
        for index, (label, callback) in enumerate(labels_callbacks):
            rect = pygame.Rect(0, 0, width, height)
            rect.center = (center_x, start_y + index * (height + spacing))
            self.buttons.append(Button(rect, label, callback))
        self.selected_index = 0

    def on_enter(self) -> None:
        """Start menu background music.

        Returns:
            None.
        """
        self.app.resources.play_music("menu_music")

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle mouse and keyboard interactions in the menu.

        Args:
            event: Event received from the main loop.

        Returns:
            None.
        """
        for button in self.buttons:
            if button.handle_event(event):
                self.app.resources.play_sound("ui_confirm")

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected_index = (self.selected_index + 1) % len(self.buttons)
                self.app.resources.play_sound("ui_move")
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.selected_index = (self.selected_index - 1) % len(self.buttons)
                self.app.resources.play_sound("ui_move")
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.app.resources.play_sound("ui_confirm")
                self.buttons[self.selected_index].callback()

    def update(self, dt: float) -> None:
        """Keep the menu scene interface consistent with the scene API.

        Args:
            dt: Frame delta time in seconds.

        Returns:
            None. The menu currently has no time-based state to update.
        """
        return None

    def render(self, surface: pygame.Surface) -> None:
        """Draw the menu interface.

        Args:
            surface: Framebuffer surface used for the current frame.

        Returns:
            None.
        """
        self.draw_backdrop(surface, accent=(212, 92, 76), secondary=(104, 176, 241))
        title = self.app.title_font.render("Crimsonland Lite", True, (247, 236, 220))
        subtitle = self.app.default_font.render("Arcade survival laboratory build", True, (184, 197, 216))
        tag = self.app.small_font.render("20 waves  |  upgrades  |  mini-bosses", True, (255, 195, 129))
        surface.blit(title, title.get_rect(center=(surface.get_width() // 2, 108)))
        surface.blit(subtitle, subtitle.get_rect(center=(surface.get_width() // 2, 154)))
        surface.blit(tag, tag.get_rect(center=(surface.get_width() // 2, 186)))

        panel = pygame.Rect(surface.get_width() // 2 - 230, 236, 460, 240)
        self.draw_panel(surface, panel, accent=(212, 92, 76))

        for index, button in enumerate(self.buttons):
            button.draw(surface, self.app.default_font, selected=index == self.selected_index)

        note = self.app.small_font.render("W/S or arrows to navigate  |  Enter to confirm", True, (154, 169, 189))
        surface.blit(note, note.get_rect(center=(surface.get_width() // 2, 588)))
