"""Typed long-format RAW records and tab-separated paste, including decimal comma."""
import csv
import io
import math
from .i18n import add
add("Un control de calidad calcula recuperación (%), no resultado por masa. Para calcular FRAP/TPC/etc. con dilución, volumen y masa, cambia el tipo a Muestra; si realmente es un control, deja esos tres campos vacíos.", "A quality control calculates recovery (%), not a mass-normalised sample result. To calculate FRAP/TPC/etc. using dilution, extract volume and mass, change the reading type to Sample; for a true quality control, leave those three fields blank.")

COLUMNS = ["record_id", "kind", "sample_id", "bio_id", "tech_id", "concentration",
           "A_end", "A_initial", "matrix_blank_delta", "dilution", "extract_mL", "mass_g", "expected", "notes", "kind_label"]
KINDS = ("blank", "standard", "control", "sample")
NUMERIC = set(COLUMNS[5:13])

def number(value, required=False):
    if value is None or str(value).strip() == "":
        if required:
            raise ValueError("Dato numérico obligatorio ausente")
        return None
    x = float(str(value).strip().replace(",", "."))
    if not math.isfinite(x):
        raise ValueError("No se permiten NaN o infinitos")
    return x

def normalize(rows, protocol):
    clean, seen, reps, groups = [], set(), set(), {}
    for index, row in enumerate(rows, 1):
        if not any(v is not None and str(v).strip() for v in row.values()):
            continue
        d = {k: number(row.get(k)) if k in NUMERIC else str(row.get(k) or "").strip() for k in COLUMNS}
        from .reading_design import enabled,prepare_row,signal,matrix_mode
        if not enabled(protocol) and any(row.get(k) not in ('',None) for k in ('reading_basis','technical_n','technical_sd')):raise ValueError('Enable explicit reading options before importing mean provenance')
        if enabled(protocol):
            d.update({k:row.get(k,'') for k in ('reading_basis','technical_n','technical_sd')});d=prepare_row(d,protocol)
        rid = d["record_id"]
        if not rid or rid in seen:
            raise ValueError(f"Fila {index}: record_id vacío o duplicado")
        seen.add(rid)
        if d["kind"] not in KINDS:
            raise ValueError(f"{rid}: kind debe ser {KINDS}")
        for key in ("sample_id", "bio_id", "tech_id"):
            if not d[key]:
                raise ValueError(f"{rid}: falta {key}")
        rep = tuple(d[k] for k in ("kind", "sample_id", "bio_id", "tech_id"))
        flexible_dilution = enabled(protocol) and d['kind']=='sample'
        if flexible_dilution:rep += (d['dilution'],)
        if rep in reps:
            raise ValueError(f"{rid}: réplica técnica duplicada en la misma unidad experimental")
        reps.add(rep)
        if d["A_end"] is None or (signal(protocol) == "paired" and d["A_initial"] is None):
            raise ValueError(f"{rid}: faltan lecturas requeridas (A_end / A_initial)")
        if d["matrix_blank_delta"] is None and (matrix_mode(protocol)=="legacy" or matrix_mode(protocol)=="net" and d["kind"] in ("sample","control")):
            raise ValueError(f"{rid}: indicar matrix_blank_delta explícito (0 si no se aplica)")
        if (d["kind"]=="standard" or d["kind"]=="control" and not enabled(protocol)) and (d["concentration"] is None or d["concentration"] < 0):
            raise ValueError(f"{rid}: concentración nominal obligatoria no negativa")
        if d["kind"] == "control" and (d["expected"] is None or d["expected"] <= 0):
            raise ValueError(f"{rid}: expected debe ser la concentración equivalente positiva en el eje del calibrado")
        if d['kind']=='control' and any(d[k] is not None for k in ('dilution','extract_mL','mass_g')):
            from .i18n import t
            raise ValueError(f"{rid}: "+t('Un control de calidad calcula recuperación (%), no resultado por masa. Para calcular FRAP/TPC/etc. con dilución, volumen y masa, cambia el tipo a Muestra; si realmente es un control, deja esos tres campos vacíos.'))
        if d["kind"] == "sample":
            for key in ("dilution", "extract_mL", "mass_g"):
                if d[key] is None or d[key] <= 0:
                    raise ValueError(f"{rid}: {key} debe ser positivo")
        group = tuple(d[k] for k in ("kind", "sample_id", "bio_id"))
        params = tuple(d[k] for k in ("concentration", "dilution", "extract_mL", "mass_g", "expected"))
        if flexible_dilution:params = tuple(d[k] for k in ("concentration", "extract_mL", "mass_g", "expected"))
        if group in groups and groups[group] != params:
            raise ValueError(f"{rid}: parámetros distintos entre réplicas técnicas; usar otro sample_id o bio_id")
        groups[group] = params
        clean.append(d)
    if len(clean) > 10000:
        raise ValueError("Límite del prototipo: 10000 lecturas")
    from .reading_design import validate_groups
    validate_groups(clean,protocol)
    return clean

def parse_tsv(text):
    matrix = list(csv.reader(io.StringIO(text), delimiter="\t"))
    if matrix and matrix[0] == COLUMNS:
        matrix = matrix[1:]
    return [dict(zip(COLUMNS, row)) for row in matrix if any(row)]

def demo_rows():
    """Synthetic oracle: response = 0.001*C + 0.01; no real measurements."""
    data = []
    def add(kind, sid, bio, tech, c, response, **kw):
        d = dict.fromkeys(COLUMNS, "")
        d.update(record_id=f"R{len(data)+1:04}", kind=kind, sample_id=sid, bio_id=bio, tech_id=str(tech),
                 concentration=c, A_initial=0.02, A_end=round(response + 0.02,12),
                 matrix_blank_delta=0, notes="SINTÉTICO — no usar como resultado experimental", **kw)
        data.append(d)
    for i in range(1, 4):
        add("blank", "RB", "batch", i, "", 0.01)
    for c in (100, 300, 500, 700, 1000):
        for i, err in enumerate((-0.001, 0, 0.001), 1):
            add("standard", f"P{c}", "cal", i, c, 0.01 + 0.001*c + err)
    for bio, c in (("B1", 400), ("B2", 600)):
        for i, err in enumerate((-0.002, 0, 0.002), 1):
            add("sample", "Olivo-demo", bio, i, "", 0.01 + c*0.001 + err,
                dilution=2, extract_mL=10, mass_g=0.5)
    for i in range(1, 4):
        add("control", "QC500", "QC", i, 500, 0.51, expected=500)
    return data


def demo_varieties():
    """Independent synthetic oracle: three varieties, one calibration; means 16, 24, 32."""
    rows=[dict(r) for r in demo_rows() if r['kind']!='sample']
    for variety,level in (('Variety A',400),('Variety B',600),('Variety C',800)):
        for b,offset in enumerate((-40,0,40),1):
            for t,error in enumerate((-0.002,0,0.002),1):
                d=dict.fromkeys(COLUMNS,'')
                d.update(kind='sample',sample_id=variety,bio_id=f'B{b}',tech_id=str(t),
                    A_initial=0.02,A_end=round(0.03+(level+offset)*0.001+error,12),
                    matrix_blank_delta=0,dilution=2,extract_mL=10,mass_g=0.5,
                    notes='SYNTHETIC — shared calibration; not experimental data')
                rows.append(d)
    for i,d in enumerate(rows,1):d['record_id']=f'R{i:04}'
    return rows
