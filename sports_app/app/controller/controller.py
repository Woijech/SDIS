"""Контроллер приложения: связывает UI, SQLite-репозиторий и XML IO."""

from __future__ import annotations

import os
from tkinter import messagebox

from ..model.athlete import Athlete, RANK_VALUES
from ..model.repository import AthleteRepository
from ..model.xml_io import load_athletes_sax_xml, save_athletes_dom_xml
from ..view.dialogs import AddAthleteDialog, DeleteDialog, SearchDialog
from ..view.main_window import MainWindow


class AppController:
    """Координирует действия пользователя и операции модели."""

    def __init__(self, db_path: str):
        """Инициализирует репозиторий, главное окно и состояние пагинации."""
        self.db_path = db_path
        self.repo = AthleteRepository(db_path)

        self.page = 1
        self.page_size = 10

        self.view = MainWindow(
            on_add=self.open_add,
            on_search=self.open_search,
            on_delete=self.open_delete,
            on_load_xml=self.load_from_xml,
            on_save_xml=self.save_to_xml,
            on_switch_db=self.switch_db,
            on_refresh=self.refresh,
            on_page_change=self.on_page_change,
        )

        self.refresh()

    def on_page_change(self, page: int, page_size: int) -> None:
        """Обновляет параметры пагинации и перерисовывает данные."""
        self.page = page
        self.page_size = page_size
        self.refresh()

    def refresh(self) -> None:
        """Перечитывает текущую страницу и синхронизирует таблицу, дерево и статус."""
        records, total = self.repo.list_page(self.page, self.page_size)
        self.view.set_table_page(records, total, self.page, self.page_size)
        self.view.set_tree_records(self.repo.list_all())
        self.view.set_status(f"БД: {os.path.abspath(self.db_path)}")

    def open_add(self) -> None:
        """Открывает диалог добавления записи."""
        sports = self.repo.distinct_sports()
        AddAthleteDialog(self.view, sport_suggestions=sports, on_submit=self._add_record)

    def _add_record(self, athlete: Athlete) -> None:
        """Добавляет спортсмена и обновляет представление."""
        try:
            self.repo.add(athlete)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e), parent=self.view)
            return
        self.page = 1
        self.refresh()

    def open_search(self) -> None:
        """Открывает диалог поиска по условиям варианта."""
        sports = self.repo.distinct_sports()
        ranks = self.repo.distinct_ranks() or list(RANK_VALUES)

        def on_search(mode: str, params: dict[str, str], page: int, page_size: int) -> tuple[list[Athlete], int]:
            if mode == "fio_or_sport":
                return self.repo.search_fio_or_sport(
                    fio_sub=params.get("fio_sub", ""),
                    sport=params.get("sport", ""),
                    page=page,
                    page_size=page_size,
                )
            if mode == "titles_range":
                low = int(params.get("low") or 0)
                high = int(params.get("high") or 0)
                return self.repo.search_titles_range(low=low, high=high, page=page, page_size=page_size)
            if mode == "fio_or_rank":
                return self.repo.search_fio_or_rank(
                    fio_sub=params.get("fio_sub", ""),
                    rank=params.get("rank", ""),
                    page=page,
                    page_size=page_size,
                )
            return self.repo.list_page(page, page_size)

        SearchDialog(self.view, sport_values=sports, rank_values=ranks, on_search=on_search)

    def open_delete(self) -> None:
        """Открывает диалог удаления по условиям варианта."""
        sports = self.repo.distinct_sports()
        ranks = self.repo.distinct_ranks() or list(RANK_VALUES)

        def on_delete(mode: str, params: dict[str, str]) -> int:
            if mode == "fio_or_sport":
                return self.repo.delete_fio_or_sport(
                    fio_sub=params.get("fio_sub", ""),
                    sport=params.get("sport", ""),
                )
            if mode == "titles_range":
                low = int(params.get("low") or 0)
                high = int(params.get("high") or 0)
                return self.repo.delete_titles_range(low=low, high=high)
            if mode == "fio_or_rank":
                return self.repo.delete_fio_or_rank(
                    fio_sub=params.get("fio_sub", ""),
                    rank=params.get("rank", ""),
                )
            return 0

        dlg = DeleteDialog(self.view, sport_values=sports, rank_values=ranks, on_delete=on_delete)
        self.view.wait_window(dlg)
        self.page = 1
        self.refresh()

    def load_from_xml(self, path: str) -> None:
        """Загружает записи из XML, полностью заменяя текущее содержимое БД."""
        try:
            athletes = load_athletes_sax_xml(path)
            self.repo.replace_all(athletes)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить XML: {e}", parent=self.view)
            return
        self.page = 1
        self.refresh()
        messagebox.showinfo("Загрузка", f"Загружено записей: {len(athletes)}", parent=self.view)

    def save_to_xml(self, path: str) -> None:
        """Сохраняет текущее содержимое БД в XML."""
        try:
            athletes = self.repo.list_all()
            save_athletes_dom_xml(path, athletes)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить XML: {e}", parent=self.view)
            return
        messagebox.showinfo("Сохранение", f"Сохранено записей: {len(athletes)}", parent=self.view)

    def switch_db(self, new_path: str) -> None:
        """Переключает приложение на другой файл SQLite."""
        self.repo.close()
        self.db_path = new_path
        self.repo = AthleteRepository(new_path)
        self.page = 1
        self.refresh()

    def run(self) -> None:
        """Запускает главный цикл tkinter."""
        self.view.mainloop()
