import java.util.Scanner;

public class Main {
  static boolean prime(int n) { if (n < 2) return false; for (int i=2; i<=n/i; i++) if(n%i==0) return false; return true; }
  public static void main(String[] args) {
    Scanner in = new Scanner(System.in); double balance=1000; int choice;
    do {
      System.out.println("1 Calculator 2 Grade 3 Bank menu 0 Exit");
      if(!in.hasNextInt()) break; choice=in.nextInt();
      switch(choice) {
        case 1: System.out.print("Enter number operator number: "); double a=in.nextDouble(); char op=in.next().charAt(0); double b=in.nextDouble();
          if(op=='+') System.out.println(a+b); else if(op=='-') System.out.println(a-b); else if(op=='*') System.out.println(a*b); else if(op=='/'&&b!=0) System.out.println(a/b); else System.out.println("Invalid operation"); break;
        case 2: System.out.print("Marks (0-100): "); double m=in.nextDouble(); if(m<0||m>100)System.out.println("Invalid marks");else System.out.println(m>=80?"A":m>=60?"B":m>=40?"C":"Fail"); break;
        case 3: int action; do { System.out.println("1 Balance 2 Deposit 3 Withdraw 0 Back"); action=in.nextInt(); if(action==1)System.out.println("Balance: "+balance); else if(action==2){double x=in.nextDouble();if(x>0)balance+=x;else System.out.println("Amount must be positive");} else if(action==3){double x=in.nextDouble();if(x>0&&x<=balance)balance-=x;else System.out.println("Invalid amount");} } while(action!=0); break;
        case 0: break; default: System.out.println("Invalid choice");
      }
    } while(choice!=0);
    in.close();
  }
}
