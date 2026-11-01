import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Data layer: accounts persisted in a plain text file. */
public final class AccountRepository {
    private final Path file;
    private final Map<String, Account> accounts = new LinkedHashMap<>();

    public AccountRepository(Path file) throws IOException {
        this.file = file;
        if (Files.exists(file)) {
            for (String line : Files.readAllLines(file)) {
                if (!line.isBlank()) {
                    Account a = Account.deserialize(line);
                    accounts.put(a.getNumber(), a);
                }
            }
        } else {
            add(new Account("1001", "1234", 5000));
            add(new Account("1002", "4321", 250));
            save();
        }
    }

    private void add(Account a) {
        accounts.put(a.getNumber(), a);
    }

    public Account find(String number) {
        return accounts.get(number);
    }

    public void save() throws IOException {
        List<String> lines = new ArrayList<>();
        for (Account a : accounts.values()) {
            lines.add(a.serialize());
        }
        Files.write(file, lines);
    }
}
