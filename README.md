# 🐍 SnakeCharmers — Персональний Асистент

> CLI-додаток для керування контактами і нотатками з інтелектуальним автодоповненням, валідацією та збереженням даних між сесіями.

## 🚀 Встановлення та запуск

### Спосіб 1 — pip install (рекомендовано)

```bash
git clone https://github.com/tatianava123-arch/SnakeCharmers01.git
cd SnakeCharmers01
pip install .
helper-bot
```

Команда `helper-bot` доступна **з будь-якої папки** системи завдяки `setup.py` → `entry_points = {'console_scripts': ['helper-bot=cli:main']}`.

### Спосіб 2 — запуск як скрипт

```bash
pip install -r requirements.txt
python cli.py
```

---

## 📁 Структура проєкту

```
SnakeCharmers01/
├── cli.py           — головний модуль: меню, цикл while True, load/save
├── contacts.py      — AddressBook : UserDict, Record, поля, валідація, дні народження
├── notebook.py      — Notebook : UserDict, Note, Tags, пошук, сортування
├── utils.py         — CommandCompleter : Completer, Tab-автодоповнення, ask_yes_no()
├── setup.py         — конфігурація pip-пакету, entry_points
└── requirements.txt — prompt_toolkit==3.0.52, rich==14.3.3
```

---

## 🏠 Головне меню

При запуску `cli.py` відновлює дані з `contacts.pkl` і `notebook.pkl`, потім відображає меню через `rich.Panel`:

```
╭────── Персональний асистент ──────╮
│                                    │
│   1  📒 Адресна книга              │
│   2  📓 Нотатник                   │
│   3  👋 Вийти                      │
│                                    │
╰────────────────────────────────────╯
Оберіть:
```

При виборі `3` — автоматично зберігає обидві бази через `pickle.dump()` і завершує роботу.

---

## 📒 Адресна книга

### Команди

| Команда | Опис |
|---|---|
| `add` | Покрокове створення контакту (ім'я, телефони, ДН, email, адреса) |
| `edit [ім'я]` | Редагувати вибрані поля контакту |
| `delete [ім'я]` | Видалити контакт |
| `all` | Всі контакти у таблиці `rich.Table` |
| `search [запит]` | Пошук за іменем, телефоном, email або адресою |
| `birthdays` | Іменинники на найближчі 30 днів |
| `show-birthday [ім'я]` | Скільки днів до дня народження контакту |
| `help` | Список усіх команд |
| `back` | Зберегти і повернутись до головного меню |

### Поля контакту

| Поле | Клас | Обов'язкове | Особливість |
|---|---|---|---|
| Ім'я | `Name(Field)` | ✅ | Будь-який рядок |
| Телефон | `Phone(Field)` | ні | Кілька номерів, нормалізація при ініціалізації |
| Email | `Email(Field)` | ні | Один на контакт, regex-валідація |
| Адреса | `Address(Field)` | ні | Довільний текст |
| День народження | `Birthday(Field)` | ні | Формат `DD.MM.YYYY`, зберігає `date`-об'єкт |

### Команда `add` — покроковий діалог

```
Ім'я: Tetiana
Додати телефон (y/n): y
  Телефон: 0671234567
  → нормалізовано: +380671234567
Додати ще телефон (y/n): y
  Телефон: +380991234567
Додати ще телефон (y/n): n
Додати день народження (y/n): y
  День народження DD.MM.YYYY: 15.03.1995
Додати email (y/n): y
  Email: tetiana@gmail.com
Додати адресу (y/n): n

Контакт створено
```

> Якщо контакт з таким іменем вже існує — система попередить і запитає підтвердження через `ask_yes_no()`.

### Команда `edit` — редагування окремих полів

```
edit Tetiana
Редагувати телефони (y/n): y
  Телефони: +380671234567, +380991234567
  1 — додати  2 — видалити  3 — замінити
  Опція: 3
    Старий телефон: +380671234567
    Новий телефон: 0631234567
Редагувати день народження (y/n): n
Редагувати email (y/n): n
Редагувати адресу (y/n): n
Контакт оновлено
```

### Однакові імена — `_pick_record()`

Якщо є кілька контактів з однаковим іменем, система дає вибрати потрібний:

```
edit Іван
Знайдено 2 контакти з іменем 'Іван':
  1. Телефони: +380671234567 | Email: ivan1@gmail.com
  2. Телефони: +380991234567 | Email: ivan2@gmail.com
Оберіть номер (1-2): 1
```

### Команда `search`

```
search 067        → всі контакти з 067 в номері
search gmail      → всі контакти з gmail в email
search Tetiana    → за іменем
search Київ       → за адресою
```

Метод `Record.matches(query)` перевіряє **всі поля** одночасно: ім'я, телефони, email, адресу.

### Команда `birthdays`

Показує іменинників на найближчі 30 днів у вигляді таблиці. Дата привітання вже враховує переноси (див. розділ "Інтелектуальний аналіз").

### Команда `show-birthday [ім'я]`

```
show-birthday Tetiana
→ День народження Tetiana: 15.03.1995 (через 3 дні)
```

---

## 📓 Нотатник

### Команди

| Команда | Опис |
|---|---|
| `add` | Створити нотатку із заголовком, вмістом і тегами |
| `edit [заголовок]` | Редагувати вміст або теги (вибірково) |
| `delete [заголовок]` | Видалити нотатку |
| `all` | Всі нотатки у таблиці (заголовок, вміст, теги, дати) |
| `search [запит]` | Пошук по заголовку і тегах одночасно |
| `sort [тег]` | Нотатки з тегом — вгору списку ⭐ |
| `help` | Список усіх команд |
| `back` | Зберегти і повернутись до головного меню |

### Команда `add`

```
Заголовок нотатки: Ідеї для проєкту
Вміст: Реалізувати CLI з автодоповненням і тегами
Теги (через кому, необов'язково): python, work, important

Нотатку створено
```

Теги нормалізуються автоматично: `"python, work, important"` → `["python", "work", "important"]`. Заголовки унікальні — дублювання заборонено.

### Команда `edit`

```
edit Ідеї для проєкту
Редагувати вміст (y/n): y
  Новий вміст: Реалізувати CLI — ГОТОВО
Редагувати теги (y/n): y
  Нові теги: python, done
Нотатку оновлено
```

`updated_at = datetime.now()` — час змін фіксується автоматично.

### Команда `search`

```
search python     → нотатки де "python" є в заголовку АБО в тегах
search work       → те саме для "work"
```

Tab підказує теги 🏷 і заголовки 📝 одночасно.

### Команда `sort`

```
sort python
→ Ідеї для проєкту  (#python, #work)   ← вгору
→ Список книг       (#python, #study)   ← вгору
→ Нотатки до зустрічі                  ← після
```

Алгоритм: `notes_with_tag + others` — нотатки з тегом зберігають між собою порядок додавання.

---

## 🧠 Додаткові рішення

### 1. Нормалізація телефону — `normalize_ua_phone()`

Приймає будь-який поширений формат, повертає стандарт `+380XXXXXXXXX`:

```
0671234567      →  +380671234567  ✓
380671234567    →  +380671234567  ✓
+380671234567   →  +380671234567  ✓
067-123-45-67   →  +380671234567  ✓  (видаляємо розділювачі)
1234            →  ValueError         (програма не падає)
```

```python
cleaned = re.sub(r"[^0-9+]", "", phone.strip())
if cleaned.startswith("+380"):   normalized = cleaned
elif cleaned.startswith("380"):  normalized = "+" + cleaned
elif cleaned.startswith("0"):    normalized = "+38" + cleaned
else: raise ValueError("Невалідний український номер телефону")

if not re.fullmatch(r"\+380\d{9}", normalized):
    raise ValueError("Невалідний український номер телефону")
```

### 2. Розумні дні народження — `get_upcoming_birthdays()`

Три крайні випадки з реального коду:

```python
# Крайній випадок 1: 29 лютого не існує у звичайних роках
try:
    congrats = bday.replace(year=today.year)
except ValueError:
    congrats = date(today.year, 2, 28)          # → 28 лютого

# Крайній випадок 2: дата вже минула цього року
if congrats < today:
    try:
        congrats = bday.replace(year=today.year + 1)
    except ValueError:
        congrats = date(today.year + 1, 2, 28)

# Крайній випадок 3: вихідні → понеділок
if congrats.weekday() == 5:                     # субота → +2
    congrats += timedelta(days=2)
elif congrats.weekday() == 6:                   # неділя → +1
    congrats += timedelta(days=1)

# Фінальне сортування за датою
result.sort(key=lambda x: datetime.strptime(x["congratulation_date"], "%d.%m.%Y"))
```

### 3. Контекстне Tab-автодоповнення — `CommandCompleter`

```python
NAME_COMMANDS   = {"edit", "delete", "show-birthday"}
# → підказує імена контактів: lambda: list({r.name.value for r in book.data.values()})

TITLE_COMMANDS  = {"edit", "delete"}
# → підказує заголовки нотаток: lambda: list(book.data.keys())

SEARCH_COMMANDS = {"search", "sort"}
# → підказує теги 🏷 і заголовки 📝 одночасно, з дедуплікацією через seen: set[str]
```

Дані беруться через `lambda` у момент натискання Tab — новий контакт одразу у підказках без перезапуску.

---

## 💾 Збереження даних

| Файл | Вміст | Коли зберігається |
|---|---|---|
| `contacts.pkl` | Весь `AddressBook` з усіма `Record` | При `back` або виборі "3 — Вийти" |
| `notebook.pkl` | Весь `Notebook` з усіма `Note` | При `back` або виборі "3 — Вийти" |

**Graceful load** — якщо файл відсутній або пошкоджений:

```python
try:
    with open("notebook.pkl", "rb") as f:
        return pickle.load(f)
except (FileNotFoundError, EOFError, pickle.UnpicklingError):
    return Notebook()   # чистий старт без повідомлення про помилку
```

---

## 🏗️ Архітектура та ООП

### Ієрархія класів

```
Field
├── Name
├── Phone          → normalize_ua_phone() при __init__
├── Email          → validate_email() при __init__
├── Address
├── Birthday       → datetime.strptime("%d.%m.%Y") при __init__
├── Title
├── Content
└── Tags           → split(",") → strip() при __init__

UserDict
├── AddressBook    → ключ: str(uuid.uuid4())
└── Notebook       → ключ: заголовок нотатки

Completer (prompt_toolkit)
└── CommandCompleter

Record    — Name + [Phone] + Email + Address + Birthday + uuid id
Note      — Title + Content + Tags + created_at + updated_at
```

### Ключові дизайн-рішення

| Рішення | Навіщо |
|---|---|
| UUID як ключ в `AddressBook` | Дозволяє однакові імена; `delete` видаляє за `id`, не торкаючись однофамільців |
| Валідація у `__init__` полів | `Phone("1234")` кидає `ValueError` одразу — неможливо зберегти некоректний номер |
| `_pick_record()` | Вирішує неоднозначність коли кілька контактів мають однакове ім'я |
| Lambda у `CommandCompleter` | Підказки відображають поточний стан книги без перезапуску |
| `UserDict` як база | Дозволяє використовувати стандартні dict-операції і pickle-серіалізацію |

---

## ✨ Технології

| Технологія | Версія | Де використовується |
|---|---|---|
| `prompt_toolkit` | 3.0.52 | `PromptSession`, `Completer`, `Completion`, `Document` |
| `rich` | 14.3.3 | `Console`, `Table`, `Panel`, `Text`, `box.ROUNDED` |
| `pickle` | stdlib | `pickle.dump()`, `pickle.load()`, `UnpicklingError` |
| `uuid` | stdlib | `uuid.uuid4()` як унікальний ключ `Record` |
| `re` | stdlib | `re.sub()`, `re.fullmatch()` для телефону і email |
| `datetime` | stdlib | `date`, `datetime`, `timedelta` для дат народження |
| `collections` | stdlib | `UserDict` як база для `AddressBook` і `Notebook` |

---

## 👥 Команда SnakeCharmers

| Учасник | Роль | Зона відповідальності |
|---|---|---|
| **Tetiana** | Team Lead | Архітектура, code review, координація |
| **Natalia** | Scrum Master | Планування спринтів, Trello, процеси |
| **Miko** | Developer | `contacts.py` — поля, валідація, UUID, дні народження |
| **Oleksiy** | Developer | `notebook.py` — Note, Tags, пошук, сортування |

---

