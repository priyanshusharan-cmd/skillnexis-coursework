import java.io.IOException;

/** Controller: login with lockout after three bad PINs, and the actions behind each menu option. */
public class AtmController {
    private static final int MAX_ATTEMPTS = 3;
    private final AccountRepository repo;
    private Account current;
    private int failures;

    public AtmController(AccountRepository repo) {
        this.repo = repo;
    }

    public boolean login(String number, String pin) {
        Account a = repo.find(number);
        if (failures >= MAX_ATTEMPTS) {
            throw new IllegalStateException("Card locked after " + MAX_ATTEMPTS + " failed attempts");
        }
        if (a == null || !a.checkPin(pin)) {
            failures++;
            return false;
        }
        failures = 0;
        current = a;
        return true;
    }

    public double balance() {
        return current.getBalance();
    }

    public void deposit(double amount) throws IOException {
        current.deposit(amount);
        repo.save();
    }

    public void withdraw(double amount) throws IOException {
        current.withdraw(amount);
        repo.save();
    }

    public Iterable<String> history() {
        return current.getHistory();
    }
}
