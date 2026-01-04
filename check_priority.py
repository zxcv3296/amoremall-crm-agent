import sys
sys.path.insert(0, '.')

from data.personas import personas
from core.customer_analytics import get_message_priority

results = {}
details = []

for p in personas:
    priority = get_message_priority(p)
    name = priority['priority_name']
    results[name] = results.get(name, 0) + 1
    details.append({
        'name': p.get('name'),
        'priority': name,
        'reason': priority.get('reason', '')
    })

print('=== 발신목적 분포 ===')
for k, v in results.items():
    print(f'{k}: {v}명')

print('\n=== 상세 (처음 10명) ===')
for d in details[:10]:
    print(f"{d['name']}: {d['priority']} - {d['reason']}")
