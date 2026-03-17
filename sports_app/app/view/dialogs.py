"""Диалоговые окна добавления, поиска и удаления спортсменов."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from ..model.athlete import Athlete, RANK_VALUES, SQUAD_VALUES
from .widgets import PaginationFrame


COLUMNS = ("fio", "squad", "position", "titles", "sport", "rank")
COLUMN_TITLES = {
    "fio": "ФИО",
    "squad": "Состав",
    "position": "Позиция",
    "titles": "Титулы",
    "sport": "Вид спорта",
    "rank": "Разряд",
}


class AddAthleteDialog(tk.Toplevel):
    """Модальный диалог добавления одного спортсмена."""

    def __init__(
        self,
        master,
        sport_suggestions: list[str],
        on_submit: Callable[[Athlete], None],
    ):
        """Строит форму ввода и привязывает обработчик сохранения."""
        super().__init__(master)
        self.title("Добавить спортсмена")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self._on_submit = on_submit

        self.var_fio = tk.StringVar()
        self.var_squad = tk.StringVar(value=SQUAD_VALUES[0])
        self.var_position = tk.StringVar()
        self.var_titles = tk.StringVar(value="0")
        self.var_sport = tk.StringVar(value=(sport_suggestions[0] if sport_suggestions else ""))
        self.var_rank = tk.StringVar(value=RANK_VALUES[0])

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)

        def row(label: str, widget: tk.Widget, r: int):
            ttk.Label(frm, text=label).grid(row=r, column=0, sticky="w", pady=4)
            widget.grid(row=r, column=1, sticky="ew", pady=4)

        ent_fio = ttk.Entry(frm, textvariable=self.var_fio, width=40)
        row("ФИО спортсмена", ent_fio, 0)

        cb_squad = ttk.Combobox(frm, textvariable=self.var_squad, values=list(SQUAD_VALUES), state="readonly", width=37)
        row("Состав", cb_squad, 1)

        ent_position = ttk.Entry(frm, textvariable=self.var_position, width=40)
        row("Позиция", ent_position, 2)

        ent_titles = ttk.Entry(frm, textvariable=self.var_titles, width=40)
        row("Титулы (число)", ent_titles, 3)

        cb_sport = ttk.Combobox(frm, textvariable=self.var_sport, values=sport_suggestions, state="normal", width=37)
        row("Вид спорта", cb_sport, 4)

        cb_rank = ttk.Combobox(frm, textvariable=self.var_rank, values=list(RANK_VALUES), state="readonly", width=37)
        row("Разряд", cb_rank, 5)

        frm.columnconfigure(1, weight=1)

        btns = ttk.Frame(frm)
        btns.grid(row=6, column=0, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(btns, text="Отмена", command=self.destroy).pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(btns, text="Добавить", command=self._submit).pack(side=tk.RIGHT)

        ent_fio.focus_set()
        self.bind("<Return>", lambda e: self._submit())

    def _submit(self) -> None:
        """Валидирует запись, вызывает callback и закрывает окно."""
        try:
            a = Athlete(
                fio=self.var_fio.get(),
                squad=self.var_squad.get(),
                position=self.var_position.get(),
                titles=int(self.var_titles.get() or 0),
                sport=self.var_sport.get(),
                rank=self.var_rank.get(),
            ).normalized()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e), parent=self)
            return

        self._on_submit(a)
        self.destroy()


class SearchDialog(tk.Toplevel):
    """Диалог поиска с переключаемыми условиями и пагинацией."""

    def __init__(
        self,
        master,
        sport_values: list[str],
        rank_values: list[str],
        on_search: Callable[[str, dict[str, str], int, int], tuple[list[Athlete], int]],
    ):
        """`on_search(mode, params, page, page_size) -> (records, total)`."""
        super().__init__(master)
        self.title("Поиск")
        self.geometry("900x520")
        self.transient(master)
        self.grab_set()

        self._on_search = on_search
        self._mode = tk.StringVar(value="fio_or_sport")

        self._page = 1
        self._page_size = 10
        self._current_params: dict[str, str] = {}

        top = ttk.Frame(self, padding=10)
        top.pack(side=tk.TOP, fill=tk.X)

        modes = ttk.LabelFrame(top, text="Условие поиска (вариант 7)")
        modes.pack(side=tk.TOP, fill=tk.X)

        r1 = ttk.Radiobutton(
            modes,
            text="По ФИО или виду спорта",
            value="fio_or_sport",
            variable=self._mode,
            command=self._switch_mode,
        )
        r2 = ttk.Radiobutton(
            modes,
            text="По количеству титулов (нижний/верхний предел)",
            value="titles_range",
            variable=self._mode,
            command=self._switch_mode,
        )
        r3 = ttk.Radiobutton(
            modes,
            text="По ФИО или разряду",
            value="fio_or_rank",
            variable=self._mode,
            command=self._switch_mode,
        )

        r1.grid(row=0, column=0, sticky="w", padx=8, pady=4)
        r2.grid(row=0, column=1, sticky="w", padx=8, pady=4)
        r3.grid(row=0, column=2, sticky="w", padx=8, pady=4)

        self.frm_inputs = ttk.Frame(top)
        self.frm_inputs.pack(side=tk.TOP, fill=tk.X, pady=(8, 0))

        self.var_fio1 = tk.StringVar()
        self.var_sport1 = tk.StringVar(value="")
        self.var_low = tk.StringVar(value="0")
        self.var_high = tk.StringVar(value="0")
        self.var_fio3 = tk.StringVar()
        self.var_rank3 = tk.StringVar(value="")

        self._sport_values = [""] + sport_values
        self._rank_values = [""] + rank_values

        self._inputs_widgets: list[tk.Widget] = []

        btn_search = ttk.Button(top, text="Искать", command=self._do_search)
        btn_search.pack(side=tk.TOP, anchor="e", pady=(8, 0))

        mid = ttk.Frame(self, padding=10)
        mid.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(mid, columns=COLUMNS, show="headings")
        for c in COLUMNS:
            self.tree.heading(c, text=COLUMN_TITLES[c])
            self.tree.column(c, width=120, anchor="w")
        self.tree.column("fio", width=220)
        self.tree.column("position", width=140)
        self.tree.column("titles", width=80, anchor="center")

        vsb = ttk.Scrollbar(mid, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(mid, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        mid.columnconfigure(0, weight=1)
        mid.rowconfigure(0, weight=1)

        self.pagination = PaginationFrame(self, on_change=self._page_changed, page_size_default=10)
        self.pagination.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        self._switch_mode()
        self._do_search()

    def _clear_inputs(self) -> None:
        """Удаляет поля ввода предыдущего режима поиска."""
        for w in self._inputs_widgets:
            w.destroy()
        self._inputs_widgets = []

    def _switch_mode(self) -> None:
        """Перерисовывает панель ввода под выбранный режим поиска."""
        self._clear_inputs()
        mode = self._mode.get()

        if mode == "fio_or_sport":
            frm = ttk.Frame(self.frm_inputs)
            ttk.Label(frm, text="ФИО содержит:").pack(side=tk.LEFT)
            e = ttk.Entry(frm, textvariable=self.var_fio1, width=30)
            e.pack(side=tk.LEFT, padx=(6, 12))
            ttk.Label(frm, text="Вид спорта:").pack(side=tk.LEFT)
            cb = ttk.Combobox(frm, textvariable=self.var_sport1, values=self._sport_values, state="readonly", width=30)
            cb.pack(side=tk.LEFT, padx=(6, 0))
            frm.pack(side=tk.LEFT, fill=tk.X)
            self._inputs_widgets.append(frm)

        elif mode == "titles_range":
            frm = ttk.Frame(self.frm_inputs)
            ttk.Label(frm, text="Нижний предел:").pack(side=tk.LEFT)
            e1 = ttk.Entry(frm, textvariable=self.var_low, width=10)
            e1.pack(side=tk.LEFT, padx=(6, 12))
            ttk.Label(frm, text="Верхний предел:").pack(side=tk.LEFT)
            e2 = ttk.Entry(frm, textvariable=self.var_high, width=10)
            e2.pack(side=tk.LEFT, padx=(6, 0))
            frm.pack(side=tk.LEFT, fill=tk.X)
            self._inputs_widgets.append(frm)

        elif mode == "fio_or_rank":
            frm = ttk.Frame(self.frm_inputs)
            ttk.Label(frm, text="ФИО содержит:").pack(side=tk.LEFT)
            e = ttk.Entry(frm, textvariable=self.var_fio3, width=30)
            e.pack(side=tk.LEFT, padx=(6, 12))
            ttk.Label(frm, text="Разряд:").pack(side=tk.LEFT)
            cb = ttk.Combobox(frm, textvariable=self.var_rank3, values=self._rank_values, state="readonly", width=30)
            cb.pack(side=tk.LEFT, padx=(6, 0))
            frm.pack(side=tk.LEFT, fill=tk.X)
            self._inputs_widgets.append(frm)

    def _get_params(self) -> tuple[str, dict[str, str]]:
        """Собирает параметры из текущих полей ввода."""
        mode = self._mode.get()
        if mode == "fio_or_sport":
            return mode, {"fio_sub": self.var_fio1.get(), "sport": self.var_sport1.get()}
        if mode == "titles_range":
            return mode, {"low": self.var_low.get(), "high": self.var_high.get()}
        if mode == "fio_or_rank":
            return mode, {"fio_sub": self.var_fio3.get(), "rank": self.var_rank3.get()}
        return "fio_or_sport", {}

    def _do_search(self) -> None:
        """Запускает новый поиск с первой страницы."""
        mode, params = self._get_params()
        self._current_params = params
        self._page = 1
        self.pagination.set_page(1)
        self._refresh(mode, params, self._page, self.pagination.page_size)

    def _page_changed(self, page: int, page_size: int) -> None:
        """Обрабатывает смену страницы результатов."""
        self._page = page
        self._page_size = page_size
        mode = self._mode.get()
        self._refresh(mode, self._current_params, page, page_size)

    def _refresh(self, mode: str, params: dict[str, str], page: int, page_size: int) -> None:
        """Обновляет таблицу результатов по параметрам запроса."""
        try:
            records, total = self._on_search(mode, params, page, page_size)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e), parent=self)
            return

        for iid in self.tree.get_children():
            self.tree.delete(iid)

        for a in records:
            self.tree.insert(
                "",
                "end",
                values=(a.fio, a.squad, a.position, a.titles, a.sport, a.rank),
            )

        self.pagination.set_total(total)
        self.pagination.set_page(page)


class DeleteDialog(tk.Toplevel):
    """Диалог удаления записей по одному из условий варианта."""

    def __init__(
        self,
        master,
        sport_values: list[str],
        rank_values: list[str],
        on_delete: Callable[[str, dict[str, str]], int],
    ):
        """Строит форму удаления и привязывает callback удаления."""
        super().__init__(master)
        self.title("Удаление")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self._on_delete = on_delete
        self._mode = tk.StringVar(value="fio_or_sport")

        self.var_fio1 = tk.StringVar()
        self.var_sport1 = tk.StringVar(value="")
        self.var_low = tk.StringVar(value="0")
        self.var_high = tk.StringVar(value="0")
        self.var_fio3 = tk.StringVar()
        self.var_rank3 = tk.StringVar(value="")

        self._sport_values = [""] + sport_values
        self._rank_values = [""] + rank_values

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)

        modes = ttk.LabelFrame(frm, text="Условие удаления")
        modes.grid(row=0, column=0, columnspan=2, sticky="ew")

        ttk.Radiobutton(modes, text="По ФИО или виду спорта", value="fio_or_sport", variable=self._mode, command=self._switch_mode).grid(row=0, column=0, sticky="w", padx=8, pady=4)
        ttk.Radiobutton(modes, text="По титулам (диапазон)", value="titles_range", variable=self._mode, command=self._switch_mode).grid(row=0, column=1, sticky="w", padx=8, pady=4)
        ttk.Radiobutton(modes, text="По ФИО или разряду", value="fio_or_rank", variable=self._mode, command=self._switch_mode).grid(row=0, column=2, sticky="w", padx=8, pady=4)

        self.frm_inputs = ttk.Frame(frm)
        self.frm_inputs.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        btns = ttk.Frame(frm)
        btns.grid(row=2, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(btns, text="Отмена", command=self.destroy).pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(btns, text="Удалить", command=self._do_delete).pack(side=tk.RIGHT)

        self._inputs_widgets: list[tk.Widget] = []
        self._switch_mode()

    def _clear_inputs(self) -> None:
        """Удаляет поля ввода предыдущего режима удаления."""
        for w in self._inputs_widgets:
            w.destroy()
        self._inputs_widgets = []

    def _switch_mode(self) -> None:
        """Перерисовывает панель ввода под выбранный режим удаления."""
        self._clear_inputs()
        mode = self._mode.get()

        if mode == "fio_or_sport":
            frm = ttk.Frame(self.frm_inputs)
            ttk.Label(frm, text="ФИО содержит:").grid(row=0, column=0, sticky="w")
            ttk.Entry(frm, textvariable=self.var_fio1, width=28).grid(row=0, column=1, padx=(6, 12))
            ttk.Label(frm, text="Вид спорта:").grid(row=0, column=2, sticky="w")
            ttk.Combobox(frm, textvariable=self.var_sport1, values=self._sport_values, state="readonly", width=28).grid(row=0, column=3, padx=(6, 0))
            frm.pack(fill=tk.X)
            self._inputs_widgets.append(frm)

        elif mode == "titles_range":
            frm = ttk.Frame(self.frm_inputs)
            ttk.Label(frm, text="Нижний предел:").grid(row=0, column=0, sticky="w")
            ttk.Entry(frm, textvariable=self.var_low, width=10).grid(row=0, column=1, padx=(6, 12))
            ttk.Label(frm, text="Верхний предел:").grid(row=0, column=2, sticky="w")
            ttk.Entry(frm, textvariable=self.var_high, width=10).grid(row=0, column=3, padx=(6, 0))
            frm.pack(fill=tk.X)
            self._inputs_widgets.append(frm)

        elif mode == "fio_or_rank":
            frm = ttk.Frame(self.frm_inputs)
            ttk.Label(frm, text="ФИО содержит:").grid(row=0, column=0, sticky="w")
            ttk.Entry(frm, textvariable=self.var_fio3, width=28).grid(row=0, column=1, padx=(6, 12))
            ttk.Label(frm, text="Разряд:").grid(row=0, column=2, sticky="w")
            ttk.Combobox(frm, textvariable=self.var_rank3, values=self._rank_values, state="readonly", width=28).grid(row=0, column=3, padx=(6, 0))
            frm.pack(fill=tk.X)
            self._inputs_widgets.append(frm)

    def _get_params(self) -> tuple[str, dict[str, str]]:
        """Собирает параметры удаления из текущих полей."""
        mode = self._mode.get()
        if mode == "fio_or_sport":
            return mode, {"fio_sub": self.var_fio1.get(), "sport": self.var_sport1.get()}
        if mode == "titles_range":
            return mode, {"low": self.var_low.get(), "high": self.var_high.get()}
        if mode == "fio_or_rank":
            return mode, {"fio_sub": self.var_fio3.get(), "rank": self.var_rank3.get()}
        return "fio_or_sport", {}

    def _do_delete(self) -> None:
        """Выполняет удаление и показывает результат пользователю."""
        mode, params = self._get_params()
        try:
            deleted = self._on_delete(mode, params)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e), parent=self)
            return

        if deleted > 0:
            messagebox.showinfo("Удаление", f"Удалено записей: {deleted}", parent=self)
        else:
            messagebox.showinfo("Удаление", "Записей по заданным условиям не найдено", parent=self)
        self.destroy()
