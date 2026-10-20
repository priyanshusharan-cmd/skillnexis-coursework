#include <algorithm>
#include <iostream>
#include <vector>
using namespace std;
int linearSearch(const vector<int>& a,int x){for(int i=0;i<(int)a.size();++i)if(a[i]==x)return i;return -1;}
int binarySearch(const vector<int>& a,int x){int l=0,r=(int)a.size()-1;while(l<=r){int m=l+(r-l)/2;if(a[m]==x)return m;if(a[m]<x)l=m+1;else r=m-1;}return -1;}
long long bubble(vector<int>& a){long long swaps=0;for(int end=(int)a.size()-1;end>0;--end){bool changed=false;for(int i=0;i<end;++i)if(a[i]>a[i+1]){swap(a[i],a[i+1]);++swaps;changed=true;}if(!changed)break;}return swaps;}
int main(){vector<int>a={64,25,12,22,11,42};cout<<"linear search 22 index="<<linearSearch(a,22)<<"\n";auto sorted=a;sort(sorted.begin(),sorted.end());cout<<"binary search 22 index="<<binarySearch(sorted,22)<<"\n";cout<<"bubble swaps="<<bubble(a)<<" sorted:";for(int x:a)cout<<' '<<x;reverse(a.begin(),a.end());cout<<"\nreversed:";for(int x:a)cout<<' '<<x;cout<<"\n";
 vector<int> marks={78,91,64,88,95,72};double sum=0;for(int x:marks)sum+=x;sort(marks.rbegin(),marks.rend());cout<<"average="<<sum/marks.size()<<" top 3="<<marks[0]<<','<<marks[1]<<','<<marks[2]<<'\n';}
