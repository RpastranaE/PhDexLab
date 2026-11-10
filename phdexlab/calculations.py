"""One production equation source: Excel formulas. Independent oracle lives in tests."""
from collections import OrderedDict
from .reading_design import absorbance_formula,stats,mean

def groups(rows, kinds):
    result = OrderedDict()
    for i, d in enumerate(rows, 2):
        if d["kind"] in kinds:
            result.setdefault((d["kind"], d["sample_id"], d["bio_id"]), []).append(i)
    return result

def plan(rows, p):
    """Return sheet cell formulas. Excel is the sole production calculation engine."""
    n = len(rows)+1
    params = list(p)
    def par(key):
        return f"Parameters!$B${params.index(key)+2}"
    formulas = {}
    def put(s, cell, f):
        formulas.setdefault(s, {})[cell] = "=" + f
    for i, d in enumerate(rows, 2):
        put("Processing", f"A{i}", f"RAW!A{i}")
        put("Processing", f"B{i}", absorbance_formula(p,i))
        put("Processing", f"C{i}", f'IF(RAW!B{i}="blank",B{i},B{i}-Calibration!$J$2-RAW!I{i})')
    put("Calibration", "J2", '0' if p.get('blank_handling')=='zeroed' else f'AVERAGEIF(RAW!$B$2:$B${n},"blank",Processing!$B$2:$B${n})')
    standards = groups(rows, {"standard"})
    for r, (_, indices) in enumerate(standards.items(), 2):
        put("Calibration", f"A{r}", f"RAW!F{indices[0]}")
        refs = ",".join(f"Processing!C{i}" for i in indices)
        put("Calibration", f"B{r}", f"AVERAGE({refs})")
        from .reading_design import stats
        count,sd=stats(rows,indices,p,refs,'100/Calibration!$J$2' if p.get('engine')=='inhibition' else '1')
        put("Calibration", f"C{r}", count)
        put("Calibration", f"D{r}", sd)
        put("Calibration", f"E{r}", f"$J$3*A{r}+$J$4")
        put("Calibration", f"F{r}", f"B{r}-E{r}")
    end = len(standards)+1
    for cell, f in {"J3":f"SLOPE(B2:B{end},A2:A{end})", "J4":f"INTERCEPT(B2:B{end},A2:A{end})",
                    "J5":f"RSQ(B2:B{end},A2:A{end})", "J6":f"MIN(A2:A{end})", "J7":f"MAX(A2:A{end})"}.items():
        put("Calibration", cell, f)
    put("Calibration", "J8", f'IF(AND(J3>0,J5>={par("r2_min")}),"OK provisional","REVISAR calibración")')
    for i,d in enumerate(rows,2):
        if d["kind"] in ("sample", "control"):
            put("Processing",f"D{i}",f"IF(Calibration!$J$3>0,(C{i}-Calibration!$J$4)/Calibration!$J$3,NA())")
            if d["kind"]=="sample":
                factor = f'({par("aliquot_uL")}+{par("reagent_uL")}+{par("water_uL")})/{par("aliquot_uL")}' if p["calibration_basis"]=="final" else "1"
                # Each observation is normalised BEFORE averaging, including when
                # the same extraction was measured at several prior dilutions.
                put("Processing",f"G{i}",factor)
                put("Processing",f"H{i}",f'RAW!J{i}')
                put("Processing",f"I{i}",f'D{i}*G{i}*H{i}')
                put("Processing",f"J{i}",f'RAW!K{i}/1000')
                put("Processing",f"K{i}",f'RAW!L{i}')
                put("Processing",f"L{i}",par("report_factor"))
                put("Processing",f"M{i}",f'I{i}*J{i}')
                put("Processing",f"E{i}",f'M{i}/K{i}*L{i}')
            else:
                put("Processing",f"E{i}",f"D{i}/RAW!M{i}*100")
    results = groups(rows,{"sample","control"})
    for r, ((kind,sid,bio),indices) in enumerate(results.items(),2):
        for col,rawcol in (("A","B"),("B","C"),("C","D")):
            put("Results",f"{col}{r}",f"RAW!{rawcol}{indices[0]}")
        refs=",".join(f"Processing!E{i}" for i in indices)
        d=rows[indices[0]-2]
        factor=f'({par("aliquot_uL")}+{par("reagent_uL")}+{par("water_uL")})/{par("aliquot_uL")}' if p["calibration_basis"]=="final" else "1"
        scale=f'({factor})*RAW!J{indices[0]}*RAW!K{indices[0]}/1000/RAW!L{indices[0]}*{par("report_factor")}/Calibration!$J$3' if kind=="sample" else f'100/RAW!M{indices[0]}/Calibration!$J$3'
        if p.get('engine')=='inhibition':scale=f'({scale})*100/Calibration!$J$2'
        count,sd=stats(rows,indices,p,refs,scale)
        put("Results",f"D{r}",count)
        put("Results",f"E{r}",f"AVERAGE({refs})")
        put("Results",f"F{r}",sd)
        put("Results",f"G{r}",f'IF(E{r}=0,NA(),ABS(F{r}/E{r})*100)')
        cs=",".join(f"Processing!D{i}" for i in indices)
        low=f'MIN({cs})<Calibration!$J$6'; high=f'MAX({cs})>Calibration!$J$7'
        recovery=f',E{r}<{par("recovery_min_percent")},E{r}>{par("recovery_max_percent")}' if kind=="control" else ""
        put("Results",f"H{r}",f'IF(OR({low},{high}),"FUERA DE RANGO",IF(D{r}<2,"N técnico insuficiente",IF(OR(Calibration!$J$3<=0,Calibration!$J$5<{par("r2_min")},G{r}>{par("cv_max_percent")}{recovery}),"REVISAR QC","OK provisional")))')
        from .reading_design import mean
        if mean(d):
            precision=('reported technical SD' if d.get('technical_sd') is not None else 'technical SD unavailable')+('; technical n unknown' if d.get('technical_n') is None else '')
            precision_qc=f',IFERROR(G{r}>{par("cv_max_percent")},TRUE)' if d.get('technical_sd') is not None else ''
            put("Results",f"H{r}",f'IF(OR({low},{high}),"OUT OF RANGE",IF(OR(Calibration!$J$3<=0,Calibration!$J$5<{par("r2_min")}{recovery}{precision_qc}),"REVIEW QC; PRECOMPUTED MEAN","PRECOMPUTED MEAN; {precision}; review QC"))')
    # Experimental units first averaged over technical readings; never pool technical readings as independent n.
    samples = sorted({sid for kind,sid,bio in results if kind=="sample"})
    for r,sid in enumerate(samples,2):
        positions=[i for i,((kind,s,bio),_) in enumerate(results.items(),2) if kind=="sample" and s==sid]
        refs=",".join(f"Results!E{i}" for i in positions)
        put("Summary",f"A{r}",f"Results!B{positions[0]}")
        put("Summary",f"B{r}",f"COUNT({refs})")
        put("Summary",f"C{r}",f"AVERAGE({refs})")
        put("Summary",f"D{r}",f"STDEV({refs})" if len(positions)>1 else "NA()")
    return formulas
