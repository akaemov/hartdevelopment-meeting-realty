"""Reconcile the supplied Q4 2026 budget snapshot. No third-party dependencies."""
import json
from pathlib import Path

data=json.loads((Path(__file__).resolve().parents[1]/'data/budget_q4_2026.json').read_text())
for project in data['projects'].values():
    t=project['totals']
    for month in project['monthly']:
        for items,total in [('lead_items','lead'),('brand_items','brand'),('operations_items','operations')]:
            assert abs(sum(item['amount'] for item in month[items])-month[total])<0.01
        assert abs(sum(month[k] for k in ['lead','brand','agent','operations','registration'])-month['commercial'])<0.01
        assert abs(month['agent']-month['sales']*.7*project['agent_rate'])<0.01
    for key in ['sales','escrow','lead','brand','agent','operations','registration','commercial','subsidy','attraction']:
        assert abs(sum(m[key] for m in project['monthly'])-t[key])<0.01
    assert abs(t['requested_agent']+t['requested_lead']-t['attraction'])<0.01
    print(project['name'], 'attraction:',round(t['attraction'],2),'commercial without payroll:',round(t['commercial'],2),'Direct model gap:',round(t['direct_gap'],2))
for key,value in data['combined'].items():
    assert abs(sum(p['totals'][key] for p in data['projects'].values())-value)<0.01
print('Q4 arithmetic reconciled. Source truth, source freshness, ROI and individual channel conversion are not independently verified.')
