from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class Note:
    """Одна нотатка."""
    text: str
    tags: List[str] = field(default_factory=list)

    def add_tag(self, tag: str) -> None:
        clean_tag = tag.strip().lower()
        if clean_tag and clean_tag not in self.tags:
            self.tags.append(clean_tag)

    def remove_tag(self, tag: str) -> bool:
        clean_tag = tag.strip().lower()
        if clean_tag in self.tags:
            self.tags.remove(clean_tag)
            return True
        return False

    def edit_text(self, new_text: str) -> None:
        self.text = new_text.strip()

    def matches_text(self, query: str) -> bool:
        return query.lower().strip() in self.text.lower()

    def has_tag(self, tag: str) -> bool:
        return tag.strip().lower() in self.tags

    def __str__(self) -> str:
        tags_str = ", ".join(self.tags) if self.tags else "—"
        return f"Note: {self.text} | Tags: {tags_str}"


class NoteBook:
    """Колекція нотаток."""

    def __init__(self) -> None:
        self.notes: List[Note] = []

    def add_note(self, text: str, tags: List[str] | None = None) -> None:
        note = Note(text=text.strip())
        if tags:
            for tag in tags:
                note.add_tag(tag)
        self.notes.append(note)

    def delete_note(self, index: int) -> bool:
        if 0 <= index < len(self.notes):
            del self.notes[index]
            return True
        return False

    def edit_note(self, index: int, new_text: str) -> bool:
        if 0 <= index < len(self.notes):
            self.notes[index].edit_text(new_text)
            return True
        return False

    def add_tag_to_note(self, index: int, tag: str) -> bool:
        if 0 <= index < len(self.notes):
            self.notes[index].add_tag(tag)
            return True
        return False

    def remove_tag_from_note(self, index: int, tag: str) -> bool:
        if 0 <= index < len(self.notes):
            return self.notes[index].remove_tag(tag)
        return False

    def search_notes(self, query: str) -> List[Note]:
        return [note for note in self.notes if note.matches_text(query)]

    def search_by_tag(self, tag: str) -> List[Note]:
        return [note for note in self.notes if note.has_tag(tag)]

    def sort_by_tags(self) -> List[Note]:
        return sorted(self.notes, key=lambda note: ", ".join(note.tags))

    def __iter__(self):
        return iter(self.notes)

    def __len__(self) -> int:
        return len(self.notes)


if __name__ == "__main__":
    notebook = NoteBook()

    notebook.add_note("Buy milk and tea", ["shopping", "home"])
    notebook.add_note("Prepare Python demo", ["study", "python"])
    notebook.add_note("Tea ceremony ideas", ["tea", "project"])

    print("=== ALL NOTES ===")
    for i, note in enumerate(notebook):
        print(i, note)

    print("\n=== SEARCH TEXT 'tea' ===")
    for note in notebook.search_notes("tea"):
        print(note)

    print("\n=== SEARCH TAG 'python' ===")
    for note in notebook.search_by_tag("python"):
        print(note)

    print("\n=== EDIT NOTE 0 ===")
    notebook.edit_note(0, "Buy milk, tea and honey")
    print(notebook.notes[0])

    print("\n=== ADD TAG TO NOTE 1 ===")
    notebook.add_tag_to_note(1, "demo")
    print(notebook.notes[1])

    print("\n=== SORT BY TAGS ===")
    for note in notebook.sort_by_tags():
        print(note)