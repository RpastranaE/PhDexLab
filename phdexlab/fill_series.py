"""Predictable spreadsheet series; identifiers never pass through floating point."""
import re
from decimal import Decimal,InvalidOperation


def series(seed,count,copy_only=False):
    if not seed:return ['']*count
    if copy_only:return [seed[i%len(seed)] for i in range(count)]
    def numeric(value):
        try:return Decimal(value.strip().replace(',','.'))
        except InvalidOperation:return None
    numbers=[numeric(v) for v in seed]
    if len(seed)>1 and all(n is not None and n.is_finite() for n in numbers):
        step=numbers[1]-numbers[0]
        if all(b-a==step for a,b in zip(numbers,numbers[1:])):
            places=max(0,max(-n.as_tuple().exponent for n in numbers));comma=any(',' in s for s in seed)
            def show(n):
                text=format(n,f'.{places}f')
                return text.replace('.',',') if comma else text
            return [show(numbers[-1]+step*(i+1)) for i in range(count)]
    parts=[re.fullmatch(r'(.*?)(\d+)([^\d]*)',v) for v in seed]
    if all(parts) and all((p[1],p[3])==(parts[0][1],parts[0][3]) for p in parts):
        values=[int(p[2]) for p in parts];step=values[1]-values[0] if len(values)>1 else 1
        if (len(seed)>1 or parts[0][1]) and all(b-a==step for a,b in zip(values,values[1:])):
            padded=any(len(p[2])>1 and p[2].startswith('0') for p in parts);width=max(len(p[2]) for p in parts) if padded else 0
            return [parts[0][1]+str(values[-1]+step*(i+1)).zfill(width)+parts[0][3] for i in range(count)]
    return [seed[i%len(seed)] for i in range(count)]
