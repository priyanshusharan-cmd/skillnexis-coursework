# C Programming — Week 4: Structures & File Handling

Solutions for the supplied Week 4 brief: a `Student` structure, writing structure data to a file and reading it back, counting the lines in a file, appending to an existing file, and a mini project, an Employee Management System with file storage and command line arguments.

Compile with a C11 compiler: `cc -std=c11 -Wall -Wextra -pedantic main.c -o week4`.

- `./week4 demo` runs assignments 1-4.
- `./week4 add <name> <role> <salary> <DD-MM-YYYY>` adds an employee.
- `./week4 list [name-fragment]` lists or searches employees.
- `./week4 delete <id>` removes an employee.

Data files (`students.dat`, `notes.txt`, `employees.dat`) are created in the current directory.
