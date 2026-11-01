import java.util.ArrayList;
import java.util.List;

interface Borrowable {
    boolean isAvailable();

    void borrow(User user);

    void giveBack();
}

class Student {
    private final String name;
    private final int rollNo;
    private final double marks;

    Student(String name, int rollNo, double marks) {
        this.name = name;
        this.rollNo = rollNo;
        this.marks = marks;
    }

    void display() {
        System.out.printf("Student{name=%s, rollNo=%d, marks=%.1f}%n", name, rollNo, marks);
    }
}

class Vehicle {
    protected final String name;

    Vehicle(String name) {
        this.name = name;
    }

    int wheels() {
        return 0;
    }

    String describe() {
        return name + " has " + wheels() + " wheels";
    }
}

class Car extends Vehicle {
    Car(String name) {
        super(name);
    }

    @Override
    int wheels() {
        return 4;
    }
}

class Bike extends Vehicle {
    Bike(String name) {
        super(name);
    }

    @Override
    int wheels() {
        return 2;
    }

    @Override
    String describe() {
        return super.describe() + " and no roof";
    }
}

abstract class Item implements Borrowable {
    private final String title;
    private User holder;

    Item(String title) {
        this.title = title;
    }

    String getTitle() {
        return title;
    }

    User getHolder() {
        return holder;
    }

    public boolean isAvailable() {
        return holder == null;
    }

    public void borrow(User user) {
        if (!isAvailable()) {
            throw new IllegalStateException(title + " is already borrowed by " + holder.getName());
        }
        holder = user;
    }

    public void giveBack() {
        if (isAvailable()) {
            throw new IllegalStateException(title + " was not borrowed");
        }
        holder = null;
    }

    abstract String kind();
}

class Book extends Item {
    private final String author;

    Book(String title, String author) {
        super(title);
        this.author = author;
    }

    @Override
    String kind() {
        return "Book by " + author;
    }
}

class User {
    private final String name;
    private final List<Item> borrowed = new ArrayList<>();

    User(String name) {
        this.name = name;
    }

    String getName() {
        return name;
    }

    List<Item> getBorrowed() {
        return borrowed;
    }
}

class Library {
    private final List<Item> items = new ArrayList<>();

    void addBook(Item item) {
        items.add(item);
    }

    void borrowBook(String title, User user) {
        Item item = find(title);
        item.borrow(user);
        user.getBorrowed().add(item);
    }

    void returnBook(String title, User user) {
        Item item = find(title);
        if (item.getHolder() != user) {
            throw new IllegalStateException(user.getName() + " did not borrow " + title);
        }
        item.giveBack();
        user.getBorrowed().remove(item);
    }

    private Item find(String title) {
        for (Item i : items) {
            if (i.getTitle().equalsIgnoreCase(title)) {
                return i;
            }
        }
        throw new IllegalArgumentException("no such book: " + title);
    }

    void print() {
        for (Item i : items) {
            System.out.println("  " + i.getTitle() + " (" + i.kind() + ") - "
                    + (i.isAvailable() ? "available" : "borrowed by " + i.getHolder().getName()));
        }
    }
}

public class Main {
    public static void main(String[] args) {
        System.out.println("1. Student class");
        new Student("Asha", 101, 88.5).display();

        System.out.println("2. Vehicle inheritance and overriding");
        Vehicle[] vehicles = {new Car("Sedan"), new Bike("Roadster"), new Vehicle("Generic")};
        for (Vehicle v : vehicles) {
            System.out.println("  " + v.describe());
        }

        System.out.println("Library management");
        Library lib = new Library();
        lib.addBook(new Book("Effective Java", "Joshua Bloch"));
        lib.addBook(new Book("Clean Code", "Robert Martin"));
        User asha = new User("Asha");
        User ravi = new User("Ravi");
        lib.borrowBook("Effective Java", asha);
        try {
            lib.borrowBook("effective java", ravi);
        } catch (IllegalStateException e) {
            System.out.println("  rejected: " + e.getMessage());
        }
        try {
            lib.returnBook("Effective Java", ravi);
        } catch (IllegalStateException e) {
            System.out.println("  rejected: " + e.getMessage());
        }
        lib.print();
        lib.returnBook("Effective Java", asha);
        lib.print();
    }
}
