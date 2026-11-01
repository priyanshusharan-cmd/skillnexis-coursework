import java.io.IOException;
import java.nio.file.Path;
import java.util.Scanner;

/** View: console menu. Reads commands from stdin so it can be scripted. */
public class AtmView {
    public static void main(String[] args) throws IOException {
        AtmController atm = new AtmController(new AccountRepository(Path.of("accounts.txt")));
        Scanner in = new Scanner(System.in);
        System.out.println("=== ATM Simulation ===");
        boolean ok = false;
        while (!ok) {
            System.out.print("Account number: ");
            String number = in.nextLine().trim();
            System.out.print("PIN: ");
            String pin = in.nextLine().trim();
            try {
                ok = atm.login(number, pin);
            } catch (IllegalStateException e) {
                System.out.println(e.getMessage());
                return;
            }
            if (!ok) {
                System.out.println("Wrong account or PIN");
            }
        }
        boolean running = true;
        while (running && in.hasNextLine()) {
            System.out.print("\n1) Balance 2) Deposit 3) Withdraw 4) History 5) Exit: ");
            String choice = in.nextLine().trim();
            try {
                switch (choice) {
                    case "1" -> System.out.printf("Balance: %.2f%n", atm.balance());
                    case "2" -> {
                        System.out.print("Amount: ");
                        atm.deposit(Double.parseDouble(in.nextLine().trim()));
                        System.out.println("Deposited.");
                    }
                    case "3" -> {
                        System.out.print("Amount: ");
                        atm.withdraw(Double.parseDouble(in.nextLine().trim()));
                        System.out.println("Please take your cash.");
                    }
                    case "4" -> {
                        int n = 0;
                        for (String h : atm.history()) {
                            System.out.println(++n + ". " + h);
                        }
                        if (n == 0) {
                            System.out.println("No transactions yet.");
                        }
                    }
                    case "5" -> running = false;
                    default -> System.out.println("Unknown option");
                }
            } catch (NumberFormatException e) {
                System.out.println("Enter a valid number");
            } catch (IllegalArgumentException | IllegalStateException e) {
                System.out.println("Error: " + e.getMessage());
            }
        }
        System.out.println("Goodbye.");
    }
}
