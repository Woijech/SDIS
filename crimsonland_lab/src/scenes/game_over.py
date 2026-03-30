from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import pygame

from src.core.highscores import (
    ALLOWED_SCORE_NAME_CHARACTERS,
    MAX_SCORE_NAME_LENGTH,
    insert_score,
    load_scores,
    sanitize_score_name,
    save_scores,
)
from src.scenes.base import BaseScene
from src.ui.button import Button

if TYPE_CHECKING:
    from src.app import App


class GameOverScene(BaseScene):
    """Game-over scene with score summary and optional record entry."""

    def __init__(self, app: App, score: int, survived_all_waves: bool = False) -> None:
        """Prepare the game-over screen state.

        Args:
            app: Running application instance.
            score: Final score earned during the last run.
            survived_all_waves: Whether the player cleared all configured waves.

        Returns:
            None.
        """
        super().__init__(app)
        self.score = score
        self.survived_all_waves = survived_all_waves
        self.name_input = ""
        self.saved = False
        self.scores_path = self.app.base_dir / "config" / "scores.json"
        self.scores = load_scores(self.scores_path)
        best_score = self.scores[0]["score"] if self.scores else 0
        qualifies_top10 = len(self.scores) < 10 or score > self.scores[-1]["score"]
        self.is_new_best = score > best_score
        self.can_save = qualifies_top10
        self.message = "New Record!" if self.is_new_best else "Game Over"

        self.menu_button = Button(pygame.Rect(0, 0, 250, 54), "Main Menu", lambda: self.app.change_scene("menu"))
        self.retry_button = Button(pygame.Rect(0, 0, 250, 54), "Play Again", lambda: self.app.change_scene("game"))
        center_x = self.app.settings["screen_width"] // 2
        self.retry_button.rect.center = (center_x - 140, 500)
        self.menu_button.rect.center = (center_x + 140, 500)

    def on_enter(self) -> None:
        """Start game-over music and play the record sound if needed.

        Returns:
            None.
        """
        self.app.resources.play_music("game_over")
        if self.is_new_best:
            self.app.resources.play_sound("record")

    def save_current_score(self) -> None:
        """Persist the current run into the high-score table.

        Returns:
            None. After saving, the scene switches to a read-only confirmation
            state.
        """
        name = sanitize_score_name(self.name_input)
        achieved_at = datetime.now().strftime("%Y-%m-%d")
        updated, _ = insert_score(self.scores, name, self.score, achieved_at)
        save_scores(self.scores_path, updated)
        self.saved = True
        self.scores = updated
        self.message = "Score Saved"
        self.app.resources.play_sound("ui_confirm")

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle button clicks and score-name entry.

        Args:
            event: Event received from the main loop.

        Returns:
            None.
        """
        if self.retry_button.handle_event(event):
            self.app.resources.play_sound("ui_confirm")
        if self.menu_button.handle_event(event):
            self.app.resources.play_sound("ui_confirm")

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.app.resources.play_sound("ui_confirm")
                self.app.change_scene("menu")
            elif self.can_save and not self.saved:
                if event.key == pygame.K_RETURN:
                    self.save_current_score()
                elif event.key == pygame.K_BACKSPACE:
                    self.name_input = self.name_input[:-1]
                elif (
                    len(self.name_input) < MAX_SCORE_NAME_LENGTH
                    and event.unicode.isascii()
                    and event.unicode in ALLOWED_SCORE_NAME_CHARACTERS
                    and (event.unicode != " " or self.name_input)
                ):
                    self.name_input += event.unicode

    def render(self, surface: pygame.Surface) -> None:
        """Draw the game-over summary, score entry, and action buttons.

        Args:
            surface: Framebuffer surface used for the current frame.

        Returns:
            None.
        """
        self.draw_backdrop(surface, accent=(220, 104, 82), secondary=(113, 179, 241))
        title = self.app.title_font.render(self.message, True, (244, 233, 219))
        surface.blit(title, title.get_rect(center=(surface.get_width() // 2, 140)))

        panel = pygame.Rect(0, 0, 640, 284)
        panel.center = (surface.get_width() // 2, surface.get_height() // 2 - 10)
        self.draw_panel(surface, panel, accent=(220, 104, 82), fill=(12, 16, 24, 226))

        result = self.app.default_font.render(f"Score: {self.score}", True, (220, 232, 248))
        surface.blit(result, result.get_rect(center=(surface.get_width() // 2, panel.y + 20)))

        status = "You survived all 20 waves!" if self.survived_all_waves else "Try one more run and push the score higher."
        status_label = self.app.default_font.render(status, True, (163, 182, 205))
        surface.blit(status_label, status_label.get_rect(center=(surface.get_width() // 2, panel.y + 60)))

        if self.can_save and not self.saved:
            note_text = (
                "New record! Enter an English name and press Enter."
                if self.is_new_best
                else "Top-10 run. Enter an English name and press Enter."
            )
            note = self.app.default_font.render(note_text, True, (244, 196, 116))
            surface.blit(note, note.get_rect(center=(surface.get_width() // 2, panel.y + 130)))

            input_rect = pygame.Rect(0, 0, 360, 56)
            input_rect.center = (surface.get_width() // 2, panel.y + 200)
            self.draw_panel(surface, input_rect, accent=(109, 173, 255), fill=(18, 24, 34, 238))

            value = self.name_input or "English name..."
            color = (244, 244, 244) if self.name_input else (131, 146, 165)
            value_label = self.app.default_font.render(value, True, color)
            surface.blit(value_label, (input_rect.x + 18, input_rect.y + 15))
        elif self.saved:
            saved_text = self.app.default_font.render("Saved to config/scores.json", True, (164, 220, 167))
            surface.blit(saved_text, saved_text.get_rect(center=(surface.get_width() // 2, panel.y + 150)))
        else:
            no_save = self.app.default_font.render("This score missed the top 10, but the next run can change that.", True, (170, 186, 208))
            surface.blit(no_save, no_save.get_rect(center=(surface.get_width() // 2, panel.y + 150)))

        buttons_y = panel.bottom + 66
        center_x = surface.get_width() // 2
        self.retry_button.rect.center = (center_x - 140, buttons_y)
        self.menu_button.rect.center = (center_x + 140, buttons_y)
        self.retry_button.draw(surface, self.app.default_font)
        self.menu_button.draw(surface, self.app.default_font)
