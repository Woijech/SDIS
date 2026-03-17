"""Импорт и экспорт спортсменов в XML через DOM и SAX."""

from __future__ import annotations

from xml.dom import minidom
from xml.sax import handler, make_parser
from xml.sax.xmlreader import AttributesImpl

from .athlete import Athlete


def save_athletes_dom_xml(path: str, athletes: list[Athlete]) -> None:
    """Сохраняет список спортсменов в XML-файл через `xml.dom.minidom`."""
    doc = minidom.Document()
    root = doc.createElement("athletes")
    doc.appendChild(root)

    for a in athletes:
        a = a.normalized()
        node = doc.createElement("athlete")

        def add_text(tag: str, value: str) -> None:
            el = doc.createElement(tag)
            el.appendChild(doc.createTextNode(value))
            node.appendChild(el)

        add_text("fio", a.fio)
        add_text("squad", a.squad)
        add_text("position", a.position)
        add_text("titles", str(int(a.titles)))
        add_text("sport", a.sport)
        add_text("rank", a.rank)

        root.appendChild(node)

    xml_str = doc.toprettyxml(indent="  ", encoding="utf-8")
    with open(path, "wb") as f:
        f.write(xml_str)


class _AthleteSaxHandler(handler.ContentHandler):
    """SAX-обработчик, собирающий список `Athlete` из XML-потока."""

    def __init__(self) -> None:
        super().__init__()
        self.records: list[Athlete] = []
        self._current: dict[str, str | int] | None = None
        self._current_tag: str | None = None
        self._buf: list[str] = []

    def startElement(self, name: str, attrs: AttributesImpl) -> None:
        if name == "athlete":
            self._current = {
                "fio": "",
                "squad": "n/a",
                "position": "",
                "titles": 0,
                "sport": "",
                "rank": "",
            }
        elif self._current is not None:
            self._current_tag = name
            self._buf = []

    def characters(self, content: str) -> None:
        if self._current is None or self._current_tag is None:
            return
        self._buf.append(content)

    def endElement(self, name: str) -> None:
        if name == "athlete":
            if self._current is not None:
                a = Athlete(
                    fio=str(self._current.get("fio", "")),
                    squad=str(self._current.get("squad", "n/a")),
                    position=str(self._current.get("position", "")),
                    titles=int(self._current.get("titles", 0)),
                    sport=str(self._current.get("sport", "")),
                    rank=str(self._current.get("rank", "")),
                ).normalized()
                self.records.append(a)
            self._current = None
            self._current_tag = None
            self._buf = []
            return

        if self._current is None:
            return

        if self._current_tag == name:
            text = "".join(self._buf).strip()
            if name == "titles":
                try:
                    self._current[name] = int(text)
                except ValueError:
                    self._current[name] = 0
            else:
                self._current[name] = text
            self._current_tag = None
            self._buf = []


def load_athletes_sax_xml(path: str) -> list[Athlete]:
    """Загружает список спортсменов из XML-файла через `xml.sax`."""
    parser = make_parser()
    h = _AthleteSaxHandler()
    parser.setContentHandler(h)
    parser.parse(path)
    return h.records
