"""Week 2 assignments: dictionaries, text files, JSON, and CSV."""

import csv
import json
from pathlib import Path

STUDENT_FILE = Path(__file__).with_name("students.csv")


def contact_book() -> None:
    contacts: dict[str, str] = {}
    while True:
        print("\nContact book: 1) Add  2) Search  3) Update  4) Delete  5) List  6) Exit")
        choice = input("Choose: ").strip()
        if choice == "1":
            name = input("Name: ").strip()
            phone = input("Phone: ").strip()
            if name and phone:
                contacts[name] = phone
                print("Contact saved.")
            else:
                print("Name and phone are required.")
        elif choice == "2":
            name = input("Name to search: ").strip()
            print(f"{name}: {contacts[name]}" if name in contacts else "Contact not found.")
        elif choice == "3":
            name = input("Name to update: ").strip()
            if name in contacts:
                contacts[name] = input("New phone: ").strip()
                print("Contact updated.")
            else:
                print("Contact not found.")
        elif choice == "4":
            name = input("Name to delete: ").strip()
            if contacts.pop(name, None) is None:
                print("Contact not found.")
            else:
                print("Contact deleted.")
        elif choice == "5":
            if not contacts:
                print("No contacts saved.")
            else:
                for name, phone in sorted(contacts.items()):
                    print(f"{name}: {phone}")
        elif choice == "6":
            return
        else:
            print("Choose a number from 1 to 6.")


def count_text_file() -> None:
    filename = input("Text file path: ").strip()
    try:
        content = Path(filename).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        print(f"Could not read file: {error}")
        return
    line_count = len(content.splitlines())
    word_count = len(content.split())
    character_count = len(content)
    print(f"Lines: {line_count}\nWords: {word_count}\nCharacters: {character_count}")


def read_json_file() -> None:
    filename = input("JSON file path: ").strip()
    try:
        data = json.loads(Path(filename).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"Could not read valid JSON: {error}")
        return
    print(json.dumps(data, indent=2, ensure_ascii=False))


def load_students() -> dict[str, dict[str, str]]:
    students: dict[str, dict[str, str]] = {}
    if not STUDENT_FILE.exists():
        return students
    with STUDENT_FILE.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            if row.get("roll_number"):
                students[row["roll_number"]] = row
    return students


def save_students(students: dict[str, dict[str, str]]) -> None:
    with STUDENT_FILE.open("w", newline="", encoding="utf-8") as stream:
        fields = ["roll_number", "name", "marks"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(students[key] for key in sorted(students))


def student_manager() -> None:
    students = load_students()
    while True:
        print("\nStudent manager: 1) Add  2) Search  3) Delete  4) List  5) Exit")
        choice = input("Choose: ").strip()
        if choice == "1":
            roll = input("Roll number: ").strip()
            name = input("Name: ").strip()
            marks = input("Marks: ").strip()
            if not roll or not name or not marks:
                print("All fields are required.")
            else:
                try:
                    float(marks)
                except ValueError:
                    print("Marks must be numeric.")
                    continue
                students[roll] = {"roll_number": roll, "name": name, "marks": marks}
                save_students(students)
                print("Student saved to CSV.")
        elif choice == "2":
            roll = input("Roll number to search: ").strip()
            student = students.get(roll)
            print(student if student else "Student not found.")
        elif choice == "3":
            roll = input("Roll number to delete: ").strip()
            if students.pop(roll, None) is None:
                print("Student not found.")
            else:
                save_students(students)
                print("Student deleted from CSV.")
        elif choice == "4":
            if not students:
                print("No students saved.")
            else:
                for roll in sorted(students):
                    print(students[roll])
        elif choice == "5":
            return
        else:
            print("Choose a number from 1 to 5.")


def main() -> None:
    actions = {
        "1": ("Contact book", contact_book),
        "2": ("Word counter from text file", count_text_file),
        "3": ("JSON file reader", read_json_file),
        "4": ("CSV student management system", student_manager),
    }
    while True:
        print("\nPython Week 2 assignments")
        for key, (label, _) in actions.items():
            print(f"{key}) {label}")
        print("5) Exit")
        choice = input("Choose an assignment: ").strip()
        if choice == "5":
            return
        action = actions.get(choice)
        if action:
            action[1]()
        else:
            print("Choose a number from 1 to 5.")


if __name__ == "__main__":
    main()
