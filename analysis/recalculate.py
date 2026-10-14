"""Reproduce calculations from the published, dated input extracts. Python 3 stdlib."""
import json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(n):return json.loads((ROOT/'data'/n).read_text())
def annuity(loan,rate,months):
 i=rate/12
 return loan/months if i==0 else loan*i*(1+i)**months/((1+i)**months-1)
history=load('price_history_july_august_2026.json')
for r in history:
 if r['july_m2'] is not None and r['august_m2'] is not None:
  change=100*(r['august_m2']/r['july_m2']-1)
  assert math.isclose(change,r['delta_m2_pct'],abs_tol=1e-9)
  print(r['project'],r['rooms'],'rooms:',round(change,2),'%')
 else:assert r['delta_m2_pct'] is None
for r in load('affordability_scenarios.json'):
 pv=max(r['price_rub']*.201,r['price_rub']-6000000)
 loan=r['price_rub']-pv
 assert math.isclose(pv,r['down_payment_rub'],abs_tol=.01)
 assert math.isclose(annuity(loan,.06,360),r['payment_6pct_30yrs_rub'],abs_tol=.01)
 assert loan<=6000000.01
print('6m loan, 6%, 30y:',round(annuity(6000000,.06,360)))
print('6m loan, 18%, 30y:',round(annuity(6000000,.18,360)))
for r in load('lot_examples.json'):assert math.isclose(r['price']/r['area'],r['price_per_m2'],abs_tol=.01)
for r in [x for x in load('cbr_bashkortostan.json') if 'Количество' in x['title']]:
 d=r['data'];j=float(d['Июль 2026']);a=float(d['Август 2026']);print(r['file'],'MoM',round(100*(a/j-1),2),'%')
print('All arithmetic checks passed. These checks do not verify the truth of source inputs.')
