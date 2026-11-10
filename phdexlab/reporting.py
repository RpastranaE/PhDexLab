"""Display-only rounding of a mean and SD; saved numbers are never modified."""
from decimal import Decimal,localcontext,ROUND_HALF_UP
import math

def finite(value):return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)

def rounded_pair(mean,sd):
    """Two significant SD digits, mean rounded to the same decimal place.

    Unknown/zero SD does not determine a decimal place: use four significant
    mean digits. This is a reporting convention, not propagated uncertainty.
    """
    mean_text=f'{mean:.4g}' if finite(mean) else None
    if not finite(sd) or sd<0:return mean_text,None
    if sd==0:return mean_text,'0'
    deviation=Decimal(str(sd));value=Decimal(str(mean)) if finite(mean) else None
    place=deviation.adjusted()-1
    with localcontext() as context:
        context.prec=max(50,(value.adjusted()-place+10) if value else 50)
        deviation=deviation.quantize(Decimal(1).scaleb(place),rounding=ROUND_HALF_UP)
        # A carry such as 9.96 -> 10 changes the last significant position.
        place=deviation.adjusted()-1
        quantum=Decimal(1).scaleb(place)
        deviation=deviation.quantize(quantum,rounding=ROUND_HALF_UP)
        if value is not None:value=value.quantize(quantum,rounding=ROUND_HALF_UP)
        def show(number):
            if number==0:number=abs(number)
            if number and (place>0 or number.adjusted()>=6 or number.adjusted()<=-5):
                return format(number,f'.{max(0,number.adjusted()-place)}E').replace('E','e')
            return format(number,'f')
        return show(value) if value is not None else None,show(deviation)
