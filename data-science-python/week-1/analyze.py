import csv, statistics
from collections import defaultdict
from datetime import date
with open('sales.csv', newline='') as f: rows=list(csv.DictReader(f))
for r in rows:
 r['revenue']=int(r['quantity'])*float(r['unit_price']); r['year']=date.fromisoformat(r['date']).year
print('Rows:',len(rows),'Total revenue:',round(sum(r['revenue'] for r in rows),2))
def totals(key):
 out=defaultdict(float)
 for r in rows: out[r[key]]+=r['revenue']
 return sorted(out.items(),key=lambda kv:kv[1],reverse=True)
for key in ('category','year','department','region'):
 print(f'\nRevenue by {key}:')
 for k,v in totals(key):print(f'  {k}: {v:.2f}')
vals=[r['revenue'] for r in rows]
print('\nMean / median / population variance:',statistics.mean(vals),statistics.median(vals),statistics.pvariance(vals))
print('\nSample data only: replace sales.csv with the official linked dataset for course submission.')
