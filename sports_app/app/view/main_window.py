"""Главное окно приложения: таблица, дерево, меню и панель инструментов."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, ttk
from typing import Callable

from ..model.athlete import Athlete
from .widgets import PaginationFrame, MessageBar


COLUMNS = ("fio", "squad", "position", "titles", "sport", "rank")
COLUMN_TITLES = {
    "fio": "ФИО спортсмена",
    "squad": "Состав",
    "position": "Позиция",
    "titles": "Титулы",
    "sport": "Вид спорта",
    "rank": "Разряд",
}


class MainWindow(tk.Tk):
    """Основное представление приложения с публичным API для контроллера."""

    def __init__(
        self,
        on_add: Callable[[], None],
        on_search: Callable[[], None],
        on_delete: Callable[[], None],
        on_load_xml: Callable[[str], None],
        on_save_xml: Callable[[str], None],
        on_switch_db: Callable[[str], None],
        on_refresh: Callable[[], None],
        on_page_change: Callable[[int, int], None],
    ):
        """Создаёт окно и связывает UI-коллбеки с действиями контроллера."""
        super().__init__()
        self.title("Спортсмены")
        self.geometry("1020x600")

        self._on_add = on_add
        self._on_search = on_search
        self._on_delete = on_delete
        self._on_load_xml = on_load_xml
        self._on_save_xml = on_save_xml
        self._on_switch_db = on_switch_db
        self._on_refresh = on_refresh
        self._on_page_change = on_page_change

        self._build_menu()
        self._build_toolbar()
        self._build_body()
        self._build_status()

    def _build_menu(self) -> None:
        """Строит главное меню приложения."""
        menubar = tk.Menu(self)

        m_file = tk.Menu(menubar, tearoff=0)
        m_file.add_command(label="Загрузить из XML…", command=self._action_load_xml)
        m_file.add_command(label="Сохранить в XML…", command=self._action_save_xml)
        m_file.add_separator()
        m_file.add_command(label="Выбрать/создать БД (SQLite)…", command=self._action_switch_db)
        m_file.add_separator()
        m_file.add_command(label="Выход", command=self.destroy)

        m_data = tk.Menu(menubar, tearoff=0)
        m_data.add_command(label="Добавить…", command=self._on_add)
        m_data.add_command(label="Поиск…", command=self._on_search)
        m_data.add_command(label="Удалить…", command=self._on_delete)
        m_data.add_separator()
        m_data.add_command(label="Обновить", command=self._on_refresh)

        menubar.add_cascade(label="Файл", menu=m_file)
        menubar.add_cascade(label="Данные", menu=m_data)

        self.config(menu=menubar)

    def _build_toolbar(self) -> None:
        """Строит панель инструментов с быстрыми действиями."""
        tb = ttk.Frame(self, padding=(6, 6))
        tb.pack(side=tk.TOP, fill=tk.X)

        ttk.Button(tb, text="➕ Добавить", command=self._on_add).pack(side=tk.LEFT, padx=3)
        ttk.Button(tb, text="🔎 Поиск", command=self._on_search).pack(side=tk.LEFT, padx=3)
        ttk.Button(tb, text="🗑 Удалить", command=self._on_delete).pack(side=tk.LEFT, padx=3)
        ttk.Separator(tb, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=6)
        ttk.Button(tb, text="📂 XML Загрузить", command=self._action_load_xml).pack(side=tk.LEFT, padx=3)
        ttk.Button(tb, text="💾 XML Сохранить", command=self._action_save_xml).pack(side=tk.LEFT, padx=3)
        ttk.Separator(tb, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=6)
        ttk.Button(tb, text="🔄 Обновить", command=self._on_refresh).pack(side=tk.LEFT, padx=3)

    def _build_body(self) -> None:
        """Строит вкладки таблицы и дерева."""
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill=tk.BOTH, expand=True)

        tab_table = ttk.Frame(self.nb, padding=8)
        self.nb.add(tab_table, text="Таблица")

        self.table = ttk.Treeview(tab_table, columns=COLUMNS, show="headings")
        for c in COLUMNS:
            self.table.heading(c, text=COLUMN_TITLES[c])
            self.table.column(c, width=140, anchor="w")
        self.table.column("fio", width=260)
        self.table.column("titles", width=90, anchor="center")

        vsb = ttk.Scrollbar(tab_table, orient="vertical", command=self.table.yview)
        hsb = ttk.Scrollbar(tab_table, orient="horizontal", command=self.table.xview)
        self.table.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.table.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        tab_table.rowconfigure(0, weight=1)
        tab_table.columnconfigure(0, weight=1)

        self.pagination = PaginationFrame(tab_table, on_change=self._on_page_change, page_size_default=10)
        self.pagination.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        tab_tree = ttk.Frame(self.nb, padding=8)
        self.nb.add(tab_tree, text="Дерево")

        self.tree = ttk.Treeview(tab_tree)
        vsb2 = ttk.Scrollbar(tab_tree, orient="vertical", command=self.tree.yview)
        hsb2 = ttk.Scrollbar(tab_tree, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb2.set, xscrollcommand=hsb2.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb2.grid(row=0, column=1, sticky="ns")
        hsb2.grid(row=1, column=0, sticky="ew")

        tab_tree.rowconfigure(0, weight=1)
        tab_tree.columnconfigure(0, weight=1)

        hint = ttk.Label(
            tab_tree,
            text="Листовые элементы соответствуют конкретным полям записи",
        )
        hint.grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))

    def _build_status(self) -> None:
        """Строит строку состояния внизу окна."""
        self.status = MessageBar(self)
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

    def set_status(self, text: str) -> None:
        """Обновляет текст строки состояния."""
        self.status.set(text)

    def set_table_page(self, records: list[Athlete], total: int, page: int, page_size: int) -> None:
        """Отрисовывает текущую страницу записей в табличной вкладке."""
        for iid in self.table.get_children():
            self.table.delete(iid)

        for a in records:
            self.table.insert(
                "",
                "end",
                values=(a.fio, a.squad, a.position, a.titles, a.sport, a.rank),
            )

        self.pagination.page_size_var.set(str(page_size))
        self.pagination.set_total(total)
        self.pagination.set_page(page)

    def set_tree_records(self, records: list[Athlete]) -> None:
        """Отрисовывает все записи в древовидном представлении."""
        self.tree.delete(*self.tree.get_children())

        for a in records:
            root_text = f"{a.fio} — {a.sport}"
            rid = self.tree.insert("", "end", text=root_text)
            self.tree.insert(rid, "end", text=f"Состав: {a.squad}")
            self.tree.insert(rid, "end", text=f"Позиция: {a.position}")
            self.tree.insert(rid, "end", text=f"Титулы: {a.titles}")
            self.tree.insert(rid, "end", text=f"Разряд: {a.rank}")

    def _action_load_xml(self) -> None:
        """Открывает диалог выбора XML и передаёт путь в контроллер."""
        path = filedialog.askopenfilename(
            parent=self,
            title="Загрузить из XML",
            filetypes=[("XML", "*.xml"), ("Все файлы", "*.*")],
        )
        if not path:
            return
        self._on_load_xml(path)

    def _action_save_xml(self) -> None:
        """Открывает диалог сохранения XML и передаёт путь в контроллер."""
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Сохранить в XML",
            defaultextension=".xml",
            filetypes=[("XML", "*.xml")],
        )
        if not path:
            return
        self._on_save_xml(path)

    def _action_switch_db(self) -> None:
        """Открывает диалог выбора/создания SQLite-файла."""
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Выбрать/создать файл БД (SQLite)",
            defaultextension=".db",
            filetypes=[("SQLite DB", "*.db"), ("Все файлы", "*.*")],
        )
        if not path:
            return
        self._on_switch_db(path)
