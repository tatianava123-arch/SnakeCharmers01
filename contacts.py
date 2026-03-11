from __future__ import annotations

import pickle
import re
import uuid
from collections import UserDict
from datetime import date, datetime, timedelta
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich import box

from prompt_toolkit import PromptSession

from utils import CommandCompleter, ask_yes_no

console = Console()


# =========================
# Валідація
# =========================

def normalize_ua_phone(phone: str) -> str:
    """
    Нормалізує український номер телефону до формату +380XXXXXXXXX.

    :param phone: Вхідний рядок з номером.
    :return: Нормалізований номер.
    :raises ValueError: Якщо номер не відповідає українському формату.
    """
    cleaned = re.sub(r"[^0-9+]", "", phone.strip())

    if cleaned.startswith("+380"):
        normalized = cleaned
    elif cleaned.startswith("380"):
        normalized = "+" + cleaned
    elif cleaned.startswith("0"):
        normalized = "+38" + cleaned
    else:
        raise ValueError("Невалідний український номер телефону")

    if not re.fullmatch(r"\+380\d{9}", normalized):
        raise ValueError("Невалідний український номер телефону")

    return normalized


def validate_email(email: str) -> str:
    """
    Перевіряє формат email-адреси.

    :param email: Рядок з email.
    :return: Очищений email якщо валідний.
    :raises ValueError: Якщо формат невалідний.
    """
    email = email.strip()
    if not re.fullmatch(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
        raise ValueError("Невалідний email")
    return email


# =========================
# Fields
# =========================

class Field:
    """Базовий клас для полів запису адресної книги."""

    def __init__(self, value: str) -> None:
        """
        Ініціалізує поле із заданим значенням.

        :param value: Значення поля.
        """
        self.value = value

    def __str__(self) -> str:
        """Повертає рядкове представлення значення поля."""
        return str(self.value)


class Name(Field):
    """Поле імені контакту."""
    pass


class Phone(Field):
    """Поле номеру телефону з валідацією українського формату."""

    def __init__(self, value: str) -> None:
        """
        Ініціалізує телефон, нормалізуючи та валідуючи номер.

        :param value: Рядок з номером телефону.
        :raises ValueError: Якщо номер не відповідає українському формату.
        """
        super().__init__(normalize_ua_phone(value))


class Email(Field):
    """Поле електронної пошти з валідацією формату."""

    def __init__(self, value: str) -> None:
        """
        Ініціалізує email, перевіряючи його формат.

        :param value: Рядок з email-адресою.
        :raises ValueError: Якщо формат email невалідний.
        """
        super().__init__(validate_email(value))


class Address(Field):
    """Поле адреси контакту."""
    pass


class Birthday(Field):
    """Поле дати народження у форматі DD.MM.YYYY."""

    def __init__(self, value: str) -> None:
        """
        Ініціалізує дату народження, парсячи рядок.

        :param value: Дата у форматі DD.MM.YYYY.
        :raises ValueError: Якщо формат дати невірний.
        """
        try:
            self.date_value: date = datetime.strptime(
                value.strip(), "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Використовуйте формат DD.MM.YYYY")
        super().__init__(value.strip())


# =========================
# Record
# =========================

class Record:
    """Запис контакту з іменем, телефонами та додатковими полями."""

    def __init__(self, name: str) -> None:
        """
        Створює новий запис контакту з унікальним id.

        :param name: Ім'я контакту.
        """
        self.id: str = str(uuid.uuid4())
        self.name = Name(name.strip())
        self.phones: list[Phone] = []
        self.email: Optional[Email] = None
        self.address: Optional[Address] = None
        self.birthday: Optional[Birthday] = None

    def add_phone(self, phone: str) -> None:
        """
        Додає номер телефону до запису. Ігнорує дублікати.

        :param phone: Рядок з номером телефону.
        :raises ValueError: Якщо номер невалідний.
        """
        new_phone = Phone(phone)
        if any(p.value == new_phone.value for p in self.phones):
            return
        self.phones.append(new_phone)

    def find_phone(self, phone: str) -> Optional[Phone]:
        """
        Знаходить об'єкт телефону за номером.

        :param phone: Номер телефону для пошуку.
        :return: Об'єкт Phone або None якщо не знайдено.
        """
        normalized = normalize_ua_phone(phone)
        return next((p for p in self.phones if p.value == normalized), None)

    def remove_phone(self, phone: str) -> bool:
        """
        Видаляє номер телефону із запису.

        :param phone: Номер телефону для видалення.
        :return: True якщо видалено, False якщо не знайдено.
        """
        found = self.find_phone(phone)
        if found is None:
            return False
        self.phones.remove(found)
        return True

    def edit_phone(self, old_phone: str, new_phone: str) -> bool:
        """
        Замінює існуючий номер телефону на новий.

        :param old_phone: Старий номер телефону.
        :param new_phone: Новий номер телефону.
        :return: True якщо замінено, False якщо старий номер не знайдено.
        :raises ValueError: Якщо новий номер невалідний.
        """
        found = self.find_phone(old_phone)
        if found is None:
            return False
        found.value = Phone(new_phone).value
        return True

    def add_email(self, email: str) -> None:
        """
        Встановлює email контакту.

        :param email: Рядок з email-адресою.
        :raises ValueError: Якщо формат email невалідний.
        """
        self.email = Email(email)

    def add_address(self, address: str) -> None:
        """
        Встановлює адресу контакту.

        :param address: Рядок з адресою.
        """
        self.address = Address(address.strip())

    def add_birthday(self, birthday: str) -> None:
        """
        Встановлює дату народження контакту.

        :param birthday: Дата у форматі DD.MM.YYYY.
        :raises ValueError: Якщо формат дати невірний.
        """
        self.birthday = Birthday(birthday)

    def matches(self, query: str) -> bool:
        """
        Перевіряє чи відповідає контакт пошуковому запиту.

        Шукає за іменем, телефонами, email та адресою.

        :param query: Пошуковий рядок.
        :return: True якщо є збіг, False якщо ні.
        """
        q = query.lower().strip()
        if q in self.name.value.lower():
            return True
        if self.email and q in self.email.value.lower():
            return True
        if self.address and q in self.address.value.lower():
            return True
        return any(q in p.value for p in self.phones)


# =========================
# AddressBook
# =========================

class AddressBook(UserDict):
    """
    Колекція записів контактів.

    Ключем є унікальний id запису, що дозволяє зберігати
    кілька контактів з однаковим іменем.
    """

    def add_record(self, record: Record) -> None:
        """
        Додає запис до адресної книги.

        :param record: Об'єкт запису контакту.
        """
        self.data[record.id] = record

    def find_by_id(self, record_id: str) -> Optional[Record]:
        """
        Знаходить запис за унікальним id.

        :param record_id: Унікальний ідентифікатор запису.
        :return: Запис або None якщо не знайдено.
        """
        return self.data.get(record_id)

    def find(self, name: str) -> Optional[Record]:
        """
        Знаходить перший запис за точним іменем.

        :param name: Ім'я контакту.
        :return: Перший знайдений запис або None.
        """
        name = name.strip()
        return next((r for r in self.data.values() if r.name.value == name), None)

    def find_all_by_name(self, name: str) -> list[Record]:
        """
        Знаходить усі записи з заданим іменем.

        :param name: Ім'я контакту.
        :return: Список записів з таким іменем.
        """
        name = name.strip()
        return [r for r in self.data.values() if r.name.value == name]

    def delete(self, record_id: str) -> bool:
        """
        Видаляє запис за унікальним id.

        :param record_id: Унікальний ідентифікатор запису.
        :return: True якщо видалено, False якщо не знайдено.
        """
        if record_id not in self.data:
            return False
        del self.data[record_id]
        return True

    def search(self, query: str) -> list[Record]:
        """
        Шукає контакти за частковим збігом у імені, телефоні, email або адресі.

        :param query: Пошуковий рядок.
        :return: Список контактів що відповідають запиту.
        """
        return [r for r in self.data.values() if r.matches(query)]

    def get_upcoming_birthdays(self, days: int = 7) -> list[dict]:
        """
        Повертає список контактів з днями народження у найближчі N днів.

        Якщо день народження припадає на вихідний — переносить привітання
        на наступний понеділок.

        :param days: Кількість днів для перевірки (за замовчуванням 7).
        :return: Список словників з іменем і датою привітання.
        """
        today = date.today()
        end_date = today + timedelta(days=days)
        result: list[dict] = []

        for record in self.data.values():
            if record.birthday is None:
                continue

            bday = record.birthday.date_value
            try:
                congrats = bday.replace(year=today.year)
            except ValueError:
                congrats = date(today.year, 2, 28)

            if congrats < today:
                try:
                    congrats = bday.replace(year=today.year + 1)
                except ValueError:
                    congrats = date(today.year + 1, 2, 28)

            if congrats.weekday() == 5:
                congrats += timedelta(days=2)
            elif congrats.weekday() == 6:
                congrats += timedelta(days=1)

            if today <= congrats <= end_date:
                result.append({
                    "name": record.name.value,
                    "congratulation_date": congrats.strftime("%d.%m.%Y"),
                })

        result.sort(key=lambda x: datetime.strptime(
            x["congratulation_date"], "%d.%m.%Y"))
        return result


# =========================
# Save / Load
# =========================

def save_data(book: AddressBook) -> None:
    """
    Зберігає адресну книгу у файл contacts.pkl.

    :param book: Адресна книга для збереження.
    """
    with open("contacts.pkl", "wb") as f:
        pickle.dump(book, f)


def load_data() -> AddressBook:
    """
    Завантажує адресну книгу з файлу contacts.pkl.

    Якщо файл не знайдено — повертає порожню адресну книгу.

    :return: Завантажена або нова порожня адресна книга.
    """
    try:
        with open("contacts.pkl", "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()


# =========================
# CLI helpers
# =========================

def _pick_record(book: AddressBook, name: str) -> Optional[Record]:
    """
    Якщо існує кілька контактів з однаковим іменем — пропонує вибрати.

    :param book: Адресна книга.
    :param name: Ім'я контакту.
    :return: Обраний запис або None.
    """
    matches = book.find_all_by_name(name)

    if not matches:
        print("Контакт не знайдено")
        return None

    if len(matches) == 1:
        return matches[0]

    # Кілька контактів з однаковим іменем — показуємо список для вибору
    print(f"Знайдено {len(matches)} контакти з іменем '{name}':")
    for i, record in enumerate(matches, 1):
        phones = ", ".join(p.value for p in record.phones) or "—"
        email = record.email.value if record.email else "—"
        print(f"  {i}. Телефони: {phones} | Email: {email}")

    while True:
        choice = input(f"Оберіть номер (1-{len(matches)}): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(matches):
            return matches[int(choice) - 1]
        print("Невірний вибір")


# =========================
# CLI
# =========================

def create_contact(book: AddressBook) -> None:
    """
    Інтерактивно створює новий контакт і додає його до адресної книги.

    :param book: Адресна книга, до якої додається контакт.
    """
    name = input("Ім'я: ").strip()
    if not name:
        print("Ім'я не може бути порожнім")
        return

    # Попереджаємо якщо такий контакт вже є, але не забороняємо
    existing = book.find_all_by_name(name)
    if existing:
        print(f"Увага: контакт '{name}' вже існує ({len(existing)} шт.)")
        if not ask_yes_no("Все одно створити новий?"):
            return

    record = Record(name)

    while ask_yes_no("Додати телефон"):
        try:
            record.add_phone(input("Телефон: "))
        except ValueError as e:
            print(e)

    if ask_yes_no("Додати день народження"):
        try:
            record.add_birthday(input("День народження DD.MM.YYYY: "))
        except ValueError as e:
            print(e)

    if ask_yes_no("Додати email"):
        try:
            record.add_email(input("Email: "))
        except ValueError as e:
            print(e)

    if ask_yes_no("Додати адресу"):
        record.add_address(input("Адреса: "))

    book.add_record(record)
    print("\n\033[1mКонтакт створено\033[0m\n")


def edit_contact(book: AddressBook, name: str = "") -> None:
    """
    Інтерактивно редагує існуючий контакт.

    Якщо ім'я не передано — запитує його у користувача.
    Якщо є кілька контактів з таким іменем — пропонує вибрати.

    :param book: Адресна книга із контактами.
    :param name: Ім'я контакту для редагування (необов'язково).
    """
    if not name:
        name = input("Ім'я контакту: ").strip()

    record = _pick_record(book, name)
    if not record:
        return

    if ask_yes_no("Редагувати телефони"):
        phones_str = ", ".join(p.value for p in record.phones) or "—"
        print("Телефони:", phones_str)
        print("1 — додати  2 — видалити  3 — замінити")
        option = input("Опція: ")

        if option == "1":
            try:
                record.add_phone(input("Новий телефон: "))
            except ValueError as e:
                print(e)
        elif option == "2":
            if not record.remove_phone(input("Телефон для видалення: ")):
                print("Телефон не знайдено")
        elif option == "3":
            old = input("Старий телефон: ")
            new = input("Новий телефон: ")
            try:
                if not record.edit_phone(old, new):
                    print("Телефон не знайдено")
            except ValueError as e:
                print(e)

    if ask_yes_no("Редагувати день народження"):
        try:
            record.add_birthday(input("День народження: "))
        except ValueError as e:
            print(e)

    if ask_yes_no("Редагувати email"):
        try:
            record.add_email(input("Email: "))
        except ValueError as e:
            print(e)

    if ask_yes_no("Редагувати адресу"):
        record.add_address(input("Адреса: "))

    print("Контакт оновлено")


def delete_contact(book: AddressBook, name: str = "") -> None:
    """
    Видаляє контакт з адресної книги.

    Якщо є кілька контактів з таким іменем — пропонує вибрати який видалити.

    :param book: Адресна книга із контактами.
    :param name: Ім'я контакту для видалення (необов'язково).
    """
    if not name:
        name = input("Ім'я контакту: ").strip()

    record = _pick_record(book, name)
    if not record:
        return

    if book.delete(record.id):
        print("Видалено")
    else:
        print("Контакт не знайдено")


def show_contacts(book: AddressBook) -> None:
    """
    Виводить усі контакти адресної книги у вигляді таблиці.

    :param book: Адресна книга із контактами.
    """
    if not book.data:
        print("Немає контактів")
        return

    table = Table(title="Контакти", box=box.ROUNDED)
    table.add_column("Ім'я")
    table.add_column("Телефони")
    table.add_column("День народження")
    table.add_column("Email")
    table.add_column("Адреса")

    for record in book.data.values():
        phones = ", ".join(p.value for p in record.phones)
        birthday = record.birthday.value if record.birthday else ""
        email = record.email.value if record.email else ""
        address = record.address.value if record.address else ""
        table.add_row(record.name.value, phones, birthday, email, address)

    console.print(table)


def show_upcoming_birthdays(book: AddressBook, days_range: int = 30) -> None:
    """
    Виводить контакти з днями народження у найближчі N днів.

    :param book: Адресна книга із контактами.
    :param days_range: Кількість днів для перевірки (за замовчуванням 30).
    """
    upcoming = book.get_upcoming_birthdays(days_range)

    if not upcoming:
        print(f"Немає днів народження у найближчі {days_range} днів")
        return

    table = Table(
        title=f"Дні народження (наступні {days_range} днів)", box=box.ROUNDED)
    table.add_column("Ім'я")
    table.add_column("Дата привітання")

    for item in upcoming:
        table.add_row(item["name"], item["congratulation_date"])

    console.print(table)


def show_birthday(book: AddressBook, name: str) -> None:
    """
    Виводить день народження конкретного контакту.

    Якщо є кілька контактів з таким іменем — пропонує вибрати.

    :param book: Адресна книга із контактами.
    :param name: Ім'я контакту.
    """
    record = _pick_record(book, name)
    if not record:
        return

    if not record.birthday:
        print(f"{name} не має дня народження")
        return

    today = date.today()
    bday = record.birthday.date_value
    try:
        next_bd = bday.replace(year=today.year)
    except ValueError:
        next_bd = date(today.year, 2, 28)
    if next_bd < today:
        try:
            next_bd = bday.replace(year=today.year + 1)
        except ValueError:
            next_bd = date(today.year + 1, 2, 28)

    days_left = (next_bd - today).days
    print(
        f"День народження {name}: {record.birthday.value} (через {days_left} днів)")


def run(book: AddressBook) -> None:
    """
    Запускає інтерактивний цикл адресної книги.

    :param book: Адресна книга для роботи.
    """
    commands = ["add", "edit", "delete", "all", "search",
                "birthdays", "show-birthday", "help", "back"]
    session = PromptSession()
    completer = CommandCompleter(commands, {
        "names": lambda: list({r.name.value for r in book.data.values()}),
    })

    console.print(
        "\n[cyan]📒 Адресна книга[/cyan] — введіть [bold]help[/bold] для списку команд\n")

    while True:
        user_input = session.prompt(
            "Адресна книга › ", completer=completer).strip()
        cmd = user_input.lower()

        if cmd == "back":
            save_data(book)
            break
        elif cmd == "help":
            table = Table(title="Команди адресної книги", box=box.ROUNDED)
            table.add_column("Команда")
            table.add_column("Опис")
            table.add_row("add", "Створити контакт")
            table.add_row("edit [ім'я]", "Редагувати контакт")
            table.add_row("delete [ім'я]", "Видалити контакт")
            table.add_row("all", "Показати всі контакти")
            table.add_row("search [запит]",
                          "Пошук за іменем, телефоном, email")
            table.add_row("birthdays", "Найближчі дні народження")
            table.add_row("show-birthday [ім'я]", "День народження контакту")
            table.add_row("help", "Список команд")
            table.add_row("back", "Повернутись до головного меню")
            console.print(table)
        elif cmd == "add":
            create_contact(book)
        elif cmd.startswith("edit"):
            parts = user_input.split(maxsplit=1)
            edit_contact(book, parts[1] if len(parts) == 2 else "")
        elif cmd.startswith("delete"):
            parts = user_input.split(maxsplit=1)
            delete_contact(book, parts[1] if len(parts) == 2 else "")
        elif cmd == "all":
            show_contacts(book)
        elif cmd.startswith("search"):
            parts = user_input.split(maxsplit=1)
            if len(parts) == 2:
                results = book.search(parts[1])
                if results:
                    tmp = AddressBook({r.id: r for r in results})
                    show_contacts(tmp)
                else:
                    print("Нічого не знайдено")
            else:
                print("Використання: search ЗАПИТ")
        elif cmd == "birthdays":
            show_upcoming_birthdays(book)
        elif cmd.startswith("show-birthday"):
            parts = user_input.split(maxsplit=1)
            if len(parts) == 2:
                show_birthday(book, parts[1])
            else:
                print("Використання: show-birthday ІМ'Я")
        else:
            print("Невідома команда")
