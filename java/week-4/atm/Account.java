import java.util.ArrayList;
import java.util.List;

/** Model: one bank account with a PIN and a transaction history. */
public class Account {
    private final String number;
    private final String pin;
    private double balance;
    private final List<String> history = new ArrayList<>();

    public Account(String number, String pin, double balance) {
        this.number = number;
        this.pin = pin;
        this.balance = balance;
    }

    public String getNumber() {
        return number;
    }

    public boolean checkPin(String attempt) {
        return pin.equals(attempt);
    }

    public double getBalance() {
        return balance;
    }

    public List<String> getHistory() {
        return history;
    }

    public void deposit(double amount) {
        if (amount <= 0) {
            throw new IllegalArgumentException("Deposit must be positive");
        }
        balance += amount;
        history.add(String.format("DEPOSIT %.2f -> %.2f", amount, balance));
    }

    public void withdraw(double amount) {
        if (amount <= 0) {
            throw new IllegalArgumentException("Withdrawal must be positive");
        }
        if (amount > balance) {
            throw new IllegalStateException("Insufficient funds");
        }
        balance -= amount;
        history.add(String.format("WITHDRAW %.2f -> %.2f", amount, balance));
    }

    public String serialize() {
        return number + "|" + pin + "|" + balance + "|" + String.join(";", history);
    }

    public static Account deserialize(String line) {
        String[] p = line.split("\\|", -1);
        Account a = new Account(p[0], p[1], Double.parseDouble(p[2]));
        if (p.length > 3 && !p[3].isEmpty()) {
            for (String h : p[3].split(";")) {
                a.history.add(h);
            }
        }
        return a;
    }
}
