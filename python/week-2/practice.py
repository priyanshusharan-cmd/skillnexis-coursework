"""Week 2 data structures and loops practice questions."""

import re


def list_crud_demo() -> list[str]:
    items: list[str] = []
    while True:
        print("\nList CRUD: 1) Add  2) Read  3) Update  4) Delete  5) Done")
        choice = input("Choose: ").strip()
        if choice == "1":
            items.append(input("Item to add: ").strip())
        elif choice == "2":
            print(list(enumerate(items)))
        elif choice in {"3", "4"}:
            try:
                index = int(input("Item index: "))
                if not 0 <= index < len(items):
                    raise IndexError
            except (ValueError, IndexError):
                print("Enter an index shown by Read.")
                continue
            if choice == "3":
                items[index] = input("Replacement item: ").strip()
            else:
                items.pop(index)
        elif choice == "5":
            return items
        else:
            print("Choose a number from 1 to 5.")


def word_frequency(text: str) -> dict[str, int]:
    words = re.findall(r"\b[\w']+\b", text.lower())
    counts: dict[str, int] = {}
    for word in words:
        counts[word] = counts.get(word, 0) + 1
    return counts


def print_pattern(rows: int) -> None:
    for row in range(1, rows + 1):
        for _ in range(row):
            print("*", end="")
        print()


def list_extrema(numbers: list[float]) -> tuple[float, float]:
    if not numbers:
        raise ValueError("Provide at least one number.")
    return min(numbers), max(numbers)


def sort_by_length(words: list[str]) -> list[str]:
    return sorted(words, key=lambda word: (len(word), word.lower()))


def main() -> None:
    while True:
        print("\nPython Week 2 practice")
        print("1) List CRUD")
        print("2) Word frequency")
        print("3) Nested-loop pattern")
        print("4) Largest and smallest")
        print("5) Sort words by length with lambda")
        print("6) Exit")
        choice = input("Choose: ").strip()

        if choice == "1":
            print("Final list:", list_crud_demo())
        elif choice == "2":
            print(word_frequency(input("Text: ")))
        elif choice == "3":
            try:
                rows = int(input("Rows: "))
                if rows < 0:
                    raise ValueError
            except ValueError:
                print("Enter a non-negative whole number.")
                continue
            print_pattern(rows)
        elif choice == "4":
            try:
                numbers = [float(item) for item in input("Numbers separated by spaces: ").split()]
                smallest, largest = list_extrema(numbers)
                print(f"Smallest: {smallest}; largest: {largest}")
            except ValueError as error:
                print(f"Invalid list: {error}")
        elif choice == "5":
            words = input("Words separated by spaces: ").split()
            print(sort_by_length(words))
        elif choice == "6":
            return
        else:
            print("Choose a number from 1 to 6.")


if __name__ == "__main__":
    main()
