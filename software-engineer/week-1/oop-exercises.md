# Five OOP exercises with solutions

## 1. Encapsulation
A `BankAccount` stores a private balance. Deposits must be positive; withdrawals cannot exceed balance. Expose `deposit`, `withdraw`, and read-only `balance` operations.

## 2. Abstraction
A `Shape` interface defines `area()`. `Rectangle` and `Circle` implement it. Client code uses the interface and does not need to know each formula.

## 3. Inheritance
`Employee` stores ID and name. `HourlyEmployee` adds hours and rate and overrides `monthly_pay()`. Prefer composition if the subtype does not satisfy the base type contract.

## 4. Polymorphism
A collection of `Shape` objects calls `area()` on each. The runtime implementation supplies the correct formula, so the loop does not branch on concrete type.

## 5. Composition and SOLID
A `ReportService` receives a `TaskRepository` and `Formatter`. It asks the repository for tasks and the formatter for output. This follows dependency inversion and keeps storage separate from formatting.
