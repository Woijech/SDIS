"""Повторно используемые виджеты интерфейса Sports App."""

from __future__ import annotations

import math
import tkinter as tk
from tkinter import ttk
from typing import Callable


class PaginationFrame(ttk.Frame):
    """Виджет пагинации с навигацией и выбором размера страницы."""

    def __init__(
        self,
        master,
        on_change: Callable[[int, int], None],
        page_size_default: int = 10,
    ):
        """Создаёт элементы управления пагинацией."""
        super().__init__(master)
        self._on_change = on_change
        self._page = 1
        self._page_size = max(1, int(page_size_default))
        self._total = 0

        self.btn_first = ttk.Button(self, text="⏮", width=3, command=self._go_first)
        self.btn_prev = ttk.Button(self, text="◀", width=3, command=self._go_prev)
        self.btn_next = ttk.Button(self, text="▶", width=3, command=self._go_next)
        self.btn_last = ttk.Button(self, text="⏭", width=3, command=self._go_last)

        self.lbl_info = ttk.Label(self, text="Стр. 1/1 | Записей: 0")

        self.page_size_var = tk.StringVar(value=str(self._page_size))
        self.spin_page_size = ttk.Spinbox(
            self,
            from_=1,
            to=1000,
            width=5,
            textvariable=self.page_size_var,
            command=self._page_size_changed,
        )
        self.spin_page_size.bind("<Return>", lambda e: self._page_size_changed())

        ttk.Label(self, text="На странице:").grid(row=0, column=0, padx=(0, 6))
        self.spin_page_size.grid(row=0, column=1, padx=(0, 12))
        self.btn_first.grid(row=0, column=2)
        self.btn_prev.grid(row=0, column=3)
        self.lbl_info.grid(row=0, column=4, padx=10)
        self.btn_next.grid(row=0, column=5)
        self.btn_last.grid(row=0, column=6)

        self._refresh_info()

    def set_total(self, total: int) -> None:
        """Обновляет общее число записей и корректирует текущую страницу."""
        self._total = max(0, int(total))
        if self._page > self.total_pages:
            self._page = max(1, self.total_pages)
        self._refresh_info()

    @property
    def total_pages(self) -> int:
        if self._total <= 0:
            return 1
        return max(1, math.ceil(self._total / self._page_size))

    @property
    def page(self) -> int:
        return self._page

    @property
    def page_size(self) -> int:
        return self._page_size

    def set_page(self, page: int) -> None:
        """Устанавливает текущую страницу в допустимых границах."""
        self._page = max(1, int(page))
        if self._page > self.total_pages:
            self._page = self.total_pages
        self._refresh_info()

    def notify_change(self) -> None:
        """Уведомляет внешний обработчик о смене состояния пагинации."""
        self._on_change(self._page, self._page_size)

    def _refresh_info(self) -> None:
        """Обновляет текст состояния и доступность кнопок навигации."""
        self.lbl_info.config(
            text=f"Стр. {self._page}/{self.total_pages} | Записей: {self._total}"
        )
        first_last_disabled = self._total == 0 or self.total_pages <= 1
        self.btn_first.state(["disabled"] if first_last_disabled or self._page == 1 else ["!disabled"])
        self.btn_prev.state(["disabled"] if first_last_disabled or self._page == 1 else ["!disabled"])
        self.btn_next.state(["disabled"] if first_last_disabled or self._page >= self.total_pages else ["!disabled"])
        self.btn_last.state(["disabled"] if first_last_disabled or self._page >= self.total_pages else ["!disabled"])

    def _go_first(self) -> None:
        """Переходит на первую страницу."""
        self.set_page(1)
        self.notify_change()

    def _go_prev(self) -> None:
        """Переходит на предыдущую страницу."""
        self.set_page(self._page - 1)
        self.notify_change()

    def _go_next(self) -> None:
        """Переходит на следующую страницу."""
        self.set_page(self._page + 1)
        self.notify_change()

    def _go_last(self) -> None:
        """Переходит на последнюю страницу."""
        self.set_page(self.total_pages)
        self.notify_change()

    def _page_size_changed(self) -> None:
        """Применяет новый размер страницы и сбрасывает страницу на первую."""
        try:
            ps = int(self.page_size_var.get())
        except Exception:
            ps = self._page_size
        ps = max(1, min(1000, ps))
        self._page_size = ps
        self.page_size_var.set(str(ps))
        self.set_page(1)
        self.notify_change()


class MessageBar(ttk.Frame):
    """Строка состояния с одним текстовым сообщением."""

    def __init__(self, master: tk.Misc):
        """Создаёт виджет сообщения."""
        super().__init__(master)
        self.var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.var).pack(side=tk.LEFT, padx=6)

    def set(self, text: str) -> None:
        """Устанавливает текст строки состояния."""
        self.var.set(text)


def make_labeled_entry(
    parent: tk.Misc,
    label: str,
    textvariable: tk.StringVar,
    width: int = 30,
) -> tuple[ttk.Frame, ttk.Entry]:
    """Создаёт контейнер с подписью и `Entry`."""
    frm = ttk.Frame(parent)
    ttk.Label(frm, text=label).pack(side=tk.LEFT)
    ent = ttk.Entry(frm, textvariable=textvariable, width=width)
    ent.pack(side=tk.LEFT, padx=(8, 0), fill=tk.X, expand=True)
    return frm, ent


def make_labeled_combobox(
    parent: tk.Misc,
    label: str,
    textvariable: tk.StringVar,
    values: list[str],
    width: int = 27,
) -> tuple[ttk.Frame, ttk.Combobox]:
    """Создаёт контейнер с подписью и `Combobox`."""
    frm = ttk.Frame(parent)
    ttk.Label(frm, text=label).pack(side=tk.LEFT)
    cb = ttk.Combobox(frm, textvariable=textvariable, values=values, width=width, state="readonly")
    cb.pack(side=tk.LEFT, padx=(8, 0), fill=tk.X, expand=True)
    return frm, cb
