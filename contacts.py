from __future__ import annotations

import re
from collections import UserDict
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional


# =========================
# ВАЛІДАЦІЯ
# =========================

def normalize_ua_phone(phone: str) -> str:
    """Нормалізує український номер до формату +380XXXXXXXXX."""
    cleaned = re.sub(r"[^0-9+]", "", phone.strip())

    if cleaned.startswith("+380"):
        normalized = cleaned
    elif cleaned.startswith("380"):
        normalized = "+" + cleaned
    elif cleaned.startswith("0"):
        normalized = "+38" + cleaned
    else:
        raise ValueError("Invalid Ukrainian phone number.")

    if not re.fullmatch(r"\+380\d{9}", normalized):
        raise ValueError("Invalid Ukrainian phone number.")

    return normalized


def validate_email(email: str) -> str:
    """Перевіряє email."""
    email = email.strip()
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"

    if not re.fullmatch(pattern, email):
        raise ValueError("Invalid email format.")

    return email


# =========================
# ПОЛЯ
# =========================

class Field:
    def __init__(self, value: str) -> None:
        self.value = value

    def __str__(self) -> str:
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):
    def __init__(self, value: str) -> None:
        super().__init__(normalize_ua_phone(value))


class Email(Field):
    def __init__(self, value: str) -> None:
        super().__init__(validate_email(value))


class Address(Field):
    pass


class Birthday(Field):
    def __init__(self, value: str) -> None:
        try:
            self.date_value: date = datetime.strptime(value.strip(), "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        super().__init__(value.strip())


# =========================
# КОНТАКТ
# =========================

class Record:
    """Один контакт в адресній книзі."""

    def __init__(self, name: str) -> None:
        self.name = Name(name.strip())
        self.phones: List[Phone] = []
        self.email: Optional[Email] = None
        self.address: Optional[Address] = None
        self.birthday: Optional[Birthday] = None

    def add_phone(self, phone: str) -> None:
        new_phone = Phone(phone)
        if any(p.value == new_phone.value for p in self.phones):
            return
        self.phones.append(new_phone)

    def find_phone(self, phone: str) -> Optional[Phone]:
        normalized = normalize_ua_phone(phone)
        return next((p for p in self.phones if p.value == normalized), None)

    def remove_phone(self, phone: str) -> bool:
        found = self.find_phone(phone)
        if found is None:
            return False
        self.phones.remove(found)
        return True

    def edit_phone(self, old_phone: str, new_phone: str) -> bool:
        found = self.find_phone(old_phone)
        if found is None:
            return False
        found.value = Phone(new_phone).value
        return True

    def add_email(self, email: str) -> None:
        self.email = Email(email)

    def add_address(self, address: str) -> None:
        self.address = Address(address.strip())

    def add_birthday(self, birthday: str) -> None:
        self.birthday = Birthday(birthday)

    def matches(self, query: str) -> bool:
        q = query.lower().strip()

        if q in self.name.value.lower():
            return True

        if self.email and q in self.email.value.lower():
            return True

        if self.address and q in self.address.value.lower():
            return True

        return any(q in p.value.lower() for p in self.phones)

    def __str__(self) -> str:
        phones = ", ".join(p.value for p in self.phones) if self.phones else "—"
        email = self.email.value if self.email else "—"
        address = self.address.value if self.address else "—"
        birthday = self.birthday.value if self.birthday else "—"

        return (
            f"Name: {self.name.value} | Phones: {phones} | "
            f"Email: {email} | Birthday: {birthday} | Address: {address}"
        )


# =========================
# ДОПОМОГА ДЛЯ BIRTHDAYS
# =========================

def birthday_in_year(bday: date, year: int) -> date:
    """Повертає день народження в заданому році, коректно обробляє 29.02."""
    try:
        return bday.replace(year=year)
    except ValueError:
        return date(year, 2, 28)


# =========================
# АДРЕСНА КНИГА
# =========================

class AddressBook(UserDict):
    """Книга контактів."""

    def add_record(self, record: Record) -> None:
        self.data[record.name.value] = record

    def find(self, name: str) -> Optional[Record]:
        return self.data.get(name.strip())

    def delete(self, name: str) -> bool:
        name = name.strip()
        if name not in self.data:
            return False
        del self.data[name]
        return True

    def search(self, query: str) -> List[Record]:
        return [record for record in self.data.values() if record.matches(query)]

    def get_upcoming_birthdays(self, days: int = 7) -> List[Dict[str, str]]:
        today = date.today()
        end_date = today + timedelta(days=days)
        result: List[Dict[str, str]] = []

        for record in self.data.values():
            if record.birthday is None:
                continue

            current_year_bday = birthday_in_year(record.birthday.date_value, today.year)

            if current_year_bday < today:
                current_year_bday = birthday_in_year(record.birthday.date_value, today.year + 1)

            congrats_date = current_year_bday
            if congrats_date.weekday() == 5:
                congrats_date += timedelta(days=2)
            elif congrats_date.weekday() == 6:
                congrats_date += timedelta(days=1)

            if today <= congrats_date <= end_date:
                result.append(
                    {
                        "name": record.name.value,
                        "congratulation_date": congrats_date.strftime("%d.%m.%Y"),
                    }
                )

        result.sort(key=lambda item: datetime.strptime(item["congratulation_date"], "%d.%m.%Y"))
        return result


# =========================
# МІНІ-ТЕСТ
# =========================

if __name__ == "__main__":
    book = AddressBook()

    john = Record("John")
    john.add_phone("050 123 45 67")
    john.add_email("john@example.com")
    john.add_birthday("15.03.1990")
    john.add_address("Kyiv")
    book.add_record(john)

    kate = Record("Kate")
    kate.add_phone("0979998877")
    kate.add_email("kate@gmail.com")
    book.add_record(kate)

    print("=== ALL CONTACTS ===")
    for rec in book.data.values():
        print(rec)

    print("\n=== SEARCH 'john' ===")
    for rec in book.search("john"):
        print(rec)

    print("\n=== UPCOMING BIRTHDAYS ===")
    print(book.get_upcoming_birthdays(30))