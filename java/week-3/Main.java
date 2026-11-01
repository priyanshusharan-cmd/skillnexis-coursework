import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

public class Main {
    static void studentMarks() {
        List<Integer> marks = new ArrayList<>(List.of(72, 88, 45, 91, 67, 59));
        System.out.println("  marks: " + marks);
        System.out.println("  highest: " + Collections.max(marks) + ", lowest: " + Collections.min(marks));
        Collections.sort(marks);
        System.out.println("  sorted: " + marks + ", index of 67 (binary search): " + Collections.binarySearch(marks, 67));
    }

    static void wordFrequency(String in, String out) throws IOException {
        try (BufferedWriter w = new BufferedWriter(new FileWriter(in))) {
            w.write("the quick brown fox\njumps over the lazy dog\nthe end\n");
        }
        Map<String, Integer> freq = new TreeMap<>();
        try (BufferedReader r = new BufferedReader(new FileReader(in))) {
            String line;
            while ((line = r.readLine()) != null) {
                for (String word : line.toLowerCase().split("\\W+")) {
                    if (!word.isEmpty()) {
                        freq.merge(word, 1, Integer::sum);
                    }
                }
            }
        }
        try (BufferedWriter w = new BufferedWriter(new FileWriter(out))) {
            for (Map.Entry<String, Integer> e : freq.entrySet()) {
                w.write(e.getKey() + " " + e.getValue());
                w.newLine();
            }
        }
        System.out.println("  wrote " + freq.size() + " distinct words to " + out + ": " + freq);
    }

    record Employee(int id, String name, String dept, double salary) {
        String toLine() {
            return id + "," + name + "," + dept + "," + salary;
        }

        static Employee parse(String line) {
            String[] p = line.split(",");
            if (p.length != 4) {
                throw new IllegalArgumentException("bad record: " + line);
            }
            return new Employee(Integer.parseInt(p[0].trim()), p[1].trim(), p[2].trim(), Double.parseDouble(p[3].trim()));
        }
    }

    static class EmployeeStore {
        private final Map<Integer, Employee> byId = new LinkedHashMap<>();
        private final String path;

        EmployeeStore(String path) {
            this.path = path;
        }

        void add(String idText, String name, String dept, String salaryText) {
            int id;
            double salary;
            try {
                id = Integer.parseInt(idText);
                salary = Double.parseDouble(salaryText);
            } catch (NumberFormatException e) {
                throw new IllegalArgumentException("id and salary must be numbers", e);
            }
            if (salary < 0 || name.isBlank() || byId.containsKey(id)) {
                throw new IllegalArgumentException("invalid or duplicate employee " + id);
            }
            byId.put(id, new Employee(id, name, dept, salary));
        }

        void save() throws IOException {
            try (BufferedWriter w = new BufferedWriter(new FileWriter(path))) {
                for (Employee e : byId.values()) {
                    w.write(e.toLine());
                    w.newLine();
                }
            }
        }

        void load() throws IOException {
            byId.clear();
            try (BufferedReader r = new BufferedReader(new FileReader(path))) {
                String line;
                while ((line = r.readLine()) != null) {
                    if (!line.isBlank()) {
                        Employee e = Employee.parse(line);
                        byId.put(e.id(), e);
                    }
                }
            }
        }

        void print() {
            byId.values().forEach(e -> System.out.printf("  %d %-6s %-12s %.2f%n", e.id(), e.name(), e.dept(), e.salary()));
        }
    }

    public static void main(String[] args) throws IOException {
        System.out.println("1. Student marks (ArrayList)");
        studentMarks();

        System.out.println("2. File I/O: word frequency");
        wordFrequency("input.txt", "output.txt");

        System.out.println("Employee management (collections + file I/O)");
        EmployeeStore store = new EmployeeStore("employees.txt");
        store.add("1", "Asha", "Engineering", "85000");
        store.add("2", "Ravi", "Design", "62000.5");
        String[][] bad = {{"x", "Bad", "HR", "1"}, {"3", "Neg", "HR", "-5"}, {"1", "Dup", "HR", "10"}};
        for (String[] b : bad) {
            try {
                store.add(b[0], b[1], b[2], b[3]);
            } catch (IllegalArgumentException e) {
                System.out.println("  rejected: " + e.getMessage());
            }
        }
        store.save();
        EmployeeStore reloaded = new EmployeeStore("employees.txt");
        reloaded.load();
        System.out.println("  reloaded from file:");
        reloaded.print();
        try {
            new EmployeeStore("missing.txt").load();
        } catch (IOException e) {
            System.out.println("  handled missing file: " + e.getClass().getSimpleName());
        } finally {
            System.out.println("  finally block ran");
        }
    }
}
