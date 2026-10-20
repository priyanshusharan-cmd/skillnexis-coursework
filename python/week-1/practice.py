"""Week 1 Python practice questions."""

from math import pi


def circle_area(radius: float) -> float:
    if radius < 0:
        raise ValueError("Radius cannot be negative.")
    return pi * radius**2


def is_even(number: int) -> bool:
    return number % 2 == 0


def factorial(number: int) -> int:
    if number < 0:
        raise ValueError("Factorial is defined here only for non-negative integers.")
    if number in (0, 1):
        return 1
    return number * factorial(number - 1)


def count_vowels_and_consonants(text: str) -> tuple[int, int]:
    vowels = set("aeiou")
    vowel_count = 0
    consonant_count = 0
    for character in text.lower():
        if character.isalpha():
            if character in vowels:
                vowel_count += 1
            else:
                consonant_count += 1
    return vowel_count, consonant_count


def fibonacci(terms: int) -> list[int]:
    if terms < 0:
        raise ValueError("Number of terms cannot be negative.")
    sequence: list[int] = []
    first, second = 0, 1
    for _ in range(terms):
        sequence.append(first)
        first, second = second, first + second
    return sequence


def main() -> None:
    while True:
        print("\nWeek 1 practice")
        print("1) Area of a circle")
        print("2) Even or odd")
        print("3) Factorial (recursion)")
        print("4) Count vowels and consonants")
        print("5) Fibonacci sequence")
        print("6) Exit")
        choice = input("Choose a question: ").strip()

        try:
            if choice == "1":
                radius = float(input("Radius: "))
                print(f"Area: {circle_area(radius):.2f}")
            elif choice == "2":
                number = int(input("Integer: "))
                print("Even" if is_even(number) else "Odd")
            elif choice == "3":
                number = int(input("Non-negative integer: "))
                print(f"{number}! = {factorial(number)}")
            elif choice == "4":
                vowels, consonants = count_vowels_and_consonants(input("Text: "))
                print(f"Vowels: {vowels}; consonants: {consonants}")
            elif choice == "5":
                terms = int(input("Number of terms: "))
                print(*fibonacci(terms))
            elif choice == "6":
                return
            else:
                print("Choose a number from 1 to 6.")
        except ValueError as error:
            print(f"Invalid input: {error}")


if __name__ == "__main__":
    main()
