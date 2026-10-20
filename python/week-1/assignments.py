"""Week 1 Python assignments: functions, conditions, loops, and lists."""


def celsius_to_fahrenheit(celsius: float) -> float:
    return (celsius * 9 / 5) + 32


def fahrenheit_to_celsius(fahrenheit: float) -> float:
    return (fahrenheit - 32) * 5 / 9


def temperature_converter() -> None:
    print("Temperature converter: C to F or F to C")
    direction = input("Choose C2F or F2C: ").strip().upper()
    try:
        value = float(input("Temperature: "))
    except ValueError:
        print("Please enter a valid number.")
        return

    if direction == "C2F":
        print(f"{value:g}°C = {celsius_to_fahrenheit(value):.2f}°F")
    elif direction == "F2C":
        print(f"{value:g}°F = {fahrenheit_to_celsius(value):.2f}°C")
    else:
        print("Choose C2F or F2C.")


def calculate_grade(marks: list[float]) -> tuple[float, str]:
    if not marks:
        raise ValueError("Enter at least one mark.")
    if any(mark < 0 or mark > 100 for mark in marks):
        raise ValueError("Every mark must be between 0 and 100.")

    average = sum(marks) / len(marks)
    if average >= 90:
        grade = "A"
    elif average >= 80:
        grade = "B"
    elif average >= 70:
        grade = "C"
    elif average >= 60:
        grade = "D"
    else:
        grade = "F"
    return average, grade


def student_grade_calculator() -> None:
    try:
        marks = [float(item) for item in input("Enter marks separated by spaces: ").split()]
        average, grade = calculate_grade(marks)
    except ValueError as error:
        print(f"Invalid marks: {error}")
        return
    print(f"Average: {average:.2f}; grade: {grade}")


def is_even(number: int) -> bool:
    return number % 2 == 0


def is_prime(number: int) -> bool:
    if number < 2:
        return False
    if number == 2:
        return True
    if number % 2 == 0:
        return False
    divisor = 3
    while divisor * divisor <= number:
        if number % divisor == 0:
            return False
        divisor += 2
    return True


def number_checker() -> None:
    try:
        number = int(input("Enter an integer: "))
    except ValueError:
        print("Please enter a whole number.")
        return
    parity = "even" if is_even(number) else "odd"
    primality = "prime" if is_prime(number) else "not prime"
    print(f"{number} is {parity} and {primality}.")


def atm_simulator() -> None:
    """A small in-memory ATM exercise; this is not a real banking system."""
    demo_pin = "1234"
    balance = 1000.00

    for attempt in range(3):
        pin = input("Enter the demo PIN (1234): ").strip()
        if pin == demo_pin:
            break
        remaining = 2 - attempt
        if remaining:
            print(f"Incorrect PIN. {remaining} attempt(s) left.")
    else:
        print("Too many incorrect attempts. Session ended.")
        return

    while True:
        print("\nATM menu: 1) Balance  2) Deposit  3) Withdraw  4) Exit")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            print(f"Balance: ${balance:.2f}")
        elif choice in {"2", "3"}:
            try:
                amount = float(input("Amount: "))
            except ValueError:
                print("Enter a valid amount.")
                continue
            if amount <= 0:
                print("Amount must be greater than zero.")
            elif choice == "2":
                balance += amount
                print(f"Deposit complete. Balance: ${balance:.2f}")
            elif amount > balance:
                print("Insufficient funds.")
            else:
                balance -= amount
                print(f"Withdrawal complete. Balance: ${balance:.2f}")
        elif choice == "4":
            print("Thank you. Goodbye!")
            return
        else:
            print("Choose 1, 2, 3, or 4.")


def main() -> None:
    actions = {
        "1": ("Temperature converter", temperature_converter),
        "2": ("Student grade calculator", student_grade_calculator),
        "3": ("Even/odd and prime checker", number_checker),
        "4": ("Simple ATM simulator", atm_simulator),
    }
    while True:
        print("\nWeek 1 assignments")
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
            print("Choose 1, 2, 3, 4, or 5.")


if __name__ == "__main__":
    main()
