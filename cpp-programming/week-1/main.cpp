#include <iostream>
#include <vector>
#include <limits>
#include <climits>
using namespace std;
long long reverseNumber(long long n) { long long r=0; while(n){ int d=n%10; if(r>(LLONG_MAX-d)/10 || r<(LLONG_MIN-d)/10) return 0; r=r*10+d; n/=10; } return r; }
bool prime(int n){ if(n<2)return false; for(int i=2;i<=n/i;i++)if(n%i==0)return false; return true; }
int main(){
  cout << "C++ Week 1\n1 Calculator 2 Array sum/average 3 Prime 4 Reverse 5 ATM\nChoice: "; int choice; if(!(cin>>choice)) return 1;
  if(choice==1){ double a,b; char op; cout<<"a operator b: ";cin>>a>>op>>b; if(op=='+')cout<<a+b;else if(op=='-')cout<<a-b;else if(op=='*')cout<<a*b;else if(op=='/'&&b!=0)cout<<a/b;else cout<<"Invalid operator or division by zero"; }
  else if(choice==2){ int n; cout<<"Count: ";cin>>n; if(n<=0)return 1; double sum=0,x; for(int i=0;i<n;i++){cin>>x;sum+=x;} cout<<"Sum="<<sum<<" Average="<<sum/n; }
  else if(choice==3){int n;cin>>n;cout<<(prime(n)?"Prime":"Not prime");}
  else if(choice==4){long long n;cin>>n;cout<<reverseNumber(n);}
  else if(choice==5){double balance=1000;int op; do{cout<<"\n1 Balance 2 Deposit 3 Withdraw 0 Exit: ";cin>>op;double x;if(op==1)cout<<balance;else if(op==2){cin>>x;if(x>0)balance+=x;else cout<<"Amount must be positive";}else if(op==3){cin>>x;if(x>0&&x<=balance)balance-=x;else cout<<"Invalid amount";}}while(op!=0);}
  else cout<<"Invalid choice";
}
