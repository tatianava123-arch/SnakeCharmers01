import pickle
from datetime import datetime
from collections import UserDict
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich import box

from prompt_toolkit import PromptSession

from utils import CommandCompleter, ask_yes_no

console = Console()


# =========================
# Fields
# =========================
class Field:
    """Базовий клас для полів нотатки."""

    def __init__(self, value: str | list) -> None:
        """
        Ініціалізує поле із заданим значенням.

        :param value: Значення поля.
        """
        self.value = value

    def __str__(self) -> str:
        """Повертає рядкове представлення значення поля."""
        return str(self.value)


class Title(Field):
    """Поле заголовку нотатки."""
    pass


class Content(Field):
    """Поле вмісту нотатки."""
    pass


class Tags(Field):
    """
    Поле тегів нотатки.

    Зберігає теги як список рядків.
    Приймає як рядок з комами, так і готовий список.
    """

    def __init__(self, value: Optional[str | list]) -> None:
        """
        Ініціалізує теги з рядка або списку.

        :param value: Рядок тегів через кому або список рядків.
        """
        if isinstance(value, str):
            value = [tag.strip() for tag in value.split(",") if tag.strip()]
        elif not isinstance(value, list):
            value = []
        super().__init__(value)


# =========================
# Note
# =========================
class Note:
    """Нотатка із заголовком, вмістом, тегами та датами створення/оновлення."""

    def __init__(self, title: str, content: str, tags: Optional[str] = None) -> None:
        """
        Створює нову нотатку.

        :param title: Заголовок нотатки.
        :param content: Вміст нотатки.
        :param tags: Теги через кому (необов'язково).
        """
        self.title = Title(title)
        self.content = Content(content)
        self.tags = Tags(tags)
        self.created_at: datetime = datetime.now()
        self.updated_at: datetime = datetime.now()

    def edit(self, new_content: Optional[str] = None, new_tags: Optional[str] = None) -> None:
        """
        Оновлює вміст або теги нотатки.

        :param new_content: Новий вміст (якщо None — не змінюється).
        :param new_tags: Нові теги через кому (якщо None — не змінюються).
        """
        if new_content is not None:
            self.content = Content(new_content)
        if new_tags is not None:
            self.tags = Tags(new_tags)
        self.updated_at = datetime.now()


# =========================
# Notebook
# =========================
class Notebook(UserDict):
    """Колекція нотаток із методами для додавання, пошуку, видалення та сортування."""

    def add_note(self, note: Note) -> None:
        """
        Додає нотатку до нотатника.

        :param note: Об'єкт нотатки для додавання.
        """
        self.data[note.title.value] = note

    def find(self, title: str) -> Optional[Note]:
        """
        Знаходить нотатку за точним заголовком.

        :param title: Заголовок нотатки.
        :return: Нотатка або None, якщо не знайдено.
        """
        return self.data.get(title)

    def delete(self, title: str) -> bool:
        """
        Видаляє нотатку за заголовком.

        :param title: Заголовок нотатки для видалення.
        :return: True якщо видалено, False якщо не знайдено.
        """
        if title in self.data:
            del self.data[title]
            return True
        return False

    def search(self, query: Optional[str] = None) -> list[Note]:
        """
        Шукає нотатки за частковим збігом у заголовку або тегах.

        Якщо запит не вказано — повертає всі нотатки.

        :param query: Пошуковий рядок (необов'язково).
        :return: Список нотаток, що відповідають запиту.
        """
        result = []
        for note in self.data.values():
            if not query:
                result.append(note)
                continue
            q = query.lower()
            title_match = q in note.title.value.lower()
            tag_match = any(q in t.lower() for t in note.tags.value)
            if title_match or tag_match:
                result.append(note)
        return result

    def sort_notes_by_tag(self, tag: str) -> list[Note]:
        """
        Сортує нотатки: спочатку ті, що містять вказаний тег, потім решта.

        :param tag: Тег для сортування.
        :return: Відсортований список нотаток.
        """
        notes_with_tag = [n for n in self.data.values() if tag.lower() in [
            t.lower() for t in n.tags.value]]
        notes_without_tag = [
            n for n in self.data.values() if n not in notes_with_tag]
        return notes_with_tag + notes_without_tag


# =========================
# Save / Load
# =========================
def save_data(book: Notebook) -> None:
    """
    Зберігає нотатник у файл notebook.pkl.

    :param book: нотатник для збереження.
    """
    with open("notebook.pkl", "wb") as f:
        pickle.dump(book, f)


def load_data() -> Notebook:
    """
    Завантажує нотатник із файлу notebook.pkl.

    Якщо файл не знайдено — повертає порожній нотатник.

    :return: Завантажений або новий порожній нотатник.
    """
    try:
        with open("notebook.pkl", "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return Notebook()


# =========================
# CLI
# =========================
def create_note(book: Notebook) -> None:
    """
    Інтерактивно створює нову нотатку і додає її до нотатника.

    :param book: нотатник, до якого додається нотатка.
    """
    title = input("Заголовок нотатки: ")
    if book.find(title):
        print("Нотатка з таким заголовком вже існує")
        return
    content = input("Вміст: ")
    tags = input("Теги (через кому, необов'язково): ")
    note = Note(title, content, tags)
    book.add_note(note)
    print("Нотатку створено")


def edit_note(book: Notebook, title: str = "") -> None:
    """
    Інтерактивно редагує існуючу нотатку.

    Якщо заголовок не передано — запитує його у користувача.

    :param book: нотатник із нотатками.
    :param title: Заголовок нотатки для редагування (необов'язково).
    """
    if not title:
        title = input("Заголовок нотатки: ")
    note = book.find(title)
    if not note:
        print("Нотатку не знайдено")
        return

    content: Optional[str] = None
    tags: Optional[str] = None

    if ask_yes_no("Редагувати вміст"):
        content = input("Новий вміст: ")
    if ask_yes_no("Редагувати теги"):
        tags = input("Нові теги (через кому): ")

    note.edit(content, tags)
    print("Нотатку оновлено")


def delete_note(book: Notebook, title: str = "") -> None:
    """
    Видаляє нотатку з нотатника.

    Якщо заголовок не передано — запитує його у користувача.

    :param book: нотатник із нотатками.
    :param title: Заголовок нотатки для видалення (необов'язково).
    """
    if not title:
        title = input("Заголовок нотатки: ")
    if book.delete(title):
        print("Нотатку видалено")
    else:
        print("Нотатку не знайдено")


def show_notes(book: Notebook, query: Optional[str] = None) -> None:
    """
    Виводить нотатки у вигляді таблиці.

    Якщо передано запит — фільтрує за заголовком або тегом.

    :param book: нотатник із нотатками.
    :param query: Пошуковий рядок (необов'язково).
    """
    notes = book.search(query)
    if not notes:
        print("Нотаток не знайдено")
        return

    table = Table(title="Нотатки", box=box.ROUNDED)
    table.add_column("Заголовок")
    table.add_column("Вміст")
    table.add_column("Теги")
    table.add_column("Створено")
    table.add_column("Оновлено")

    for note in notes:
        table.add_row(
            str(note.title.value),
            str(note.content.value),
            ", ".join(str(tag) for tag in note.tags.value),
            note.created_at.strftime("%d.%m.%Y %H:%M"),
            note.updated_at.strftime("%d.%m.%Y %H:%M"),
        )
    console.print(table)


def run(book: Notebook) -> None:
    """
    Запускає інтерактивний цикл нотатника.

    :param book: нотатник для роботи.
    """
    commands = ["add", "edit", "delete", "all",
                "search", "sort", "help", "back"]
    session = PromptSession()
    completer = CommandCompleter(commands, {
        "titles": lambda: list(book.data.keys()),
        "tags": lambda: list({tag for note in book.data.values() for tag in note.tags.value}),
    })

    console.print(
        "\n[cyan]📓 Нотатник[/cyan] — введіть [bold]help[/bold] для списку команд, або [bold]back[/bold] для повернення до головного меню\n")

    while True:
        user_input = session.prompt("Нотатник › ", completer=completer).strip()
        cmd = user_input.lower()

        if cmd == "back":
            save_data(book)
            break
        elif cmd == "help":
            table = Table(title="Команди нотатника", box=box.ROUNDED)
            table.add_column("Команда")
            table.add_column("Опис")
            table.add_row("add", "Створити нотатку")
            table.add_row("edit [заголовок]", "Редагувати нотатку")
            table.add_row("delete [заголовок]", "Видалити нотатку")
            table.add_row("all", "Показати всі нотатки")
            table.add_row("search [запит]", "Пошук за заголовком або тегом")
            table.add_row("sort [тег]", "Сортувати за тегом")
            table.add_row("help", "Список команд")
            table.add_row("back", "Повернутись до головного меню")
            console.print(table)
        elif cmd == "add":
            create_note(book)
        elif cmd.startswith("edit"):
            parts = user_input.split(maxsplit=1)
            edit_note(book, parts[1] if len(parts) == 2 else "")
        elif cmd.startswith("delete"):
            parts = user_input.split(maxsplit=1)
            delete_note(book, parts[1] if len(parts) == 2 else "")
        elif cmd == "all":
            show_notes(book)
        elif cmd.startswith("search"):
            parts = user_input.split(maxsplit=1)
            show_notes(book, parts[1] if len(parts) == 2 else None)
        elif cmd.startswith("sort"):
            parts = user_input.split(maxsplit=1)
            if len(parts) == 2:
                sorted_notes = book.sort_notes_by_tag(parts[1])
                show_notes(Notebook({n.title.value: n for n in sorted_notes}))
            else:
                print("Використання: sort ТЕГ")
        else:
            print("Невідома команда")
