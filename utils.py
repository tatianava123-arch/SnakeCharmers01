from typing import Iterator

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document


# =========================
# Autocomplete
# =========================
class CommandCompleter(Completer):
    """
    Універсальний комплітер для командного рядка.

    Підказує команди на початку введення.
    Залежно від команди підказує імена контактів, заголовки або теги нотаток.
    """

    # Команди адресної книги — підказуємо імена контактів
    NAME_COMMANDS: set[str] = {"edit", "delete", "show-birthday"}
    # Команди нотатника — підказуємо заголовки нотаток
    TITLE_COMMANDS: set[str] = {"edit", "delete"}
    # Команди нотатника — підказуємо заголовки і теги
    SEARCH_COMMANDS: set[str] = {"search", "sort"}

    def __init__(self, commands: list[str], context: dict) -> None:
        """
        Ініціалізує комплітер зі списком команд та контекстом даних.

        :param commands: Список доступних команд.
        :param context: Словник з лямбдами для підказок.
                        Можливі ключі: 'names', 'titles', 'tags'.
        """
        self.commands = commands
        self.context = context

    def get_completions(self, document: Document, complete_event: object) -> Iterator[Completion]:
        """
        Генерує підказки залежно від контексту введення.

        :param document: Поточний стан введення від prompt_toolkit.
        :param complete_event: Подія автодоповнення.
        :return: Генератор об'єктів Completion.
        """
        text = document.text_before_cursor
        parts = text.split()

        # Якщо вводиться перше слово — підказуємо команди
        if not parts or (len(parts) == 1 and not text.endswith(" ")):
            word = parts[0].lower() if parts else ""
            for command in self.commands:
                if command.startswith(word):
                    yield Completion(command, start_position=-len(word))
            return

        cmd = parts[0].lower()
        current_word = parts[1] if len(
            parts) > 1 and not text.endswith(" ") else ""

        # Підказуємо імена контактів (адресна книга)
        if cmd in self.NAME_COMMANDS and "names" in self.context:
            for name in self.context["names"]():
                if name.lower().startswith(current_word.lower()):
                    yield Completion(name, start_position=-len(current_word))

        # Підказуємо заголовки нотаток
        elif cmd in self.TITLE_COMMANDS and "titles" in self.context:
            for title in self.context["titles"]():
                if title.lower().startswith(current_word.lower()):
                    yield Completion(title, start_position=-len(current_word))

        # Підказуємо заголовки і теги нотаток
        elif cmd in self.SEARCH_COMMANDS and "titles" in self.context:
            seen: set[str] = set()
            for title in self.context["titles"]():
                if title.lower().startswith(current_word.lower()) and title not in seen:
                    seen.add(title)
                    yield Completion(title, start_position=-len(current_word), display=f"📝 {title}")
            for tag in self.context["tags"]():
                if tag.lower().startswith(current_word.lower()) and tag not in seen:
                    seen.add(tag)
                    yield Completion(tag, start_position=-len(current_word), display=f"🏷  {tag}")


# =========================
# Helpers
# =========================
def ask_yes_no(text: str) -> bool:
    """
    Запитує у користувача підтвердження (y/n).

    :param text: Текст запитання.
    :return: True якщо відповідь 'y', False якщо 'n'.
    """
    while True:
        answer = input(f"{text} (y/n): ").lower()
        if answer in ["y", "n"]:
            return answer == "y"
        print("Введіть y або n")
