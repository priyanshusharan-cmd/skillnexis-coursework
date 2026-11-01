# Java Programming — Week 4: Capstone (Option 2, ATM Simulation)

An ATM simulation with PIN login, deposit, withdraw, balance check and transaction history. It follows MVC: `Account` is the model, `AtmController` holds the logic including a lockout after three wrong PINs, `AtmView` is the console view, and `AccountRepository` persists accounts to `accounts.txt`. Data is stored in a file rather than MySQL, which the brief allows for this option.

Sample accounts created on first run: `1001` with PIN `1234` and `1002` with PIN `4321`. These are demo values only.

```
cd atm
javac *.java
java AtmView
```
