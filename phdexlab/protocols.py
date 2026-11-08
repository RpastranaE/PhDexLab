"""Versioned protocol definitions; user-supplied drafts, never claimed validated."""
import copy
import hashlib
import json
from pathlib import Path

BASE = {
    "method": "FRAP", "version": 1, "status": "BORRADOR — transferencia pendiente de validar",
    "calibration_basis": "before", "concentration_unit": "umol/L", "equivalent": "Fe(II)",
    "response": "delta", "wavelength_nm": 593, "temperature_C": 37,
    "time_min": 4, "aliquot_uL": 10, "reagent_uL": 300, "water_uL": 30,
    "report_factor": 1, "result_unit": "umol eq Fe(II)/g", "mass_basis": "hoja seca",
    "r2_min": 0.99, "cv_max_percent": 10, "recovery_min_percent": 80,
    "recovery_max_percent": 120,
    "qc_policy": "Umbrales de software ilustrativos; no criterios de validación del método",
    "reagents": "Acetato 300 mM pH 3.6; TPTZ 10 mM en HCl 40 mM; FeCl3 20 mM; 10:1:1 v/v/v",
    "notes": "Restar delta del blanco de reactivos una vez. matrix_blank_delta es corrección adicional neta, no otro blanco de reactivos.",
}
FE = dict(BASE, id="frap-fe-draft", name="FRAP Fe(II) · 4 min · BORRADOR",
          source="Local protocol reference: personal-reference-pro-01",
          source_updated="2026-10-28", standard_range="100–1000 umol/L antes de reacción")
TROLOX = dict(BASE, id="frap-trolox-draft", name="FRAP Trolox · 30 min · BORRADOR",
             source="Local protocol reference: personal-reference-pro-02",
             source_updated="2026-11-02", equivalent="Trolox", concentration_unit="mg/L",
             response="endpoint", temperature_C=None, time_min=30, aliquot_uL=200,
             reagent_uL=3000, water_uL=0, report_factor=100, result_unit="mg TE/100 g",
             reagents="No confirmados para esta variante; consultar fuente. Receta 10:1:1 es complemento provisional.",
             standard_range="No especificado en fuente; definir experimentalmente",
             notes="Temperatura ambiente, oscuridad; registrar temperatura efectiva. Receta y calibración pendientes de cerrar.")
BUILTINS = [FE, TROLOX]
METHODS = ["FRAP", "ABTS", "DPPH", "CUPRAC", "TPC", "TFC"]

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)

def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()

def validate(p):
    if p.get("method") != "FRAP":
        raise ValueError("Solo FRAP está implementado; los demás métodos son puntos de extensión.")
    if p.get("response") not in ("endpoint", "delta") or p.get("calibration_basis") not in ("before", "final"):
        raise ValueError("response: endpoint/delta; calibration_basis: before/final")
    expected = {"Fe(II)": ("umol/L", 1, "umol eq Fe(II)/g"), "Trolox": ("mg/L", 100, "mg TE/100 g")}
    if p.get("equivalent") not in expected:
        raise ValueError("Calibrante no soportado")
    unit, factor, result = expected[p["equivalent"]]
    if (p.get("concentration_unit"), p.get("report_factor"), p.get("result_unit")) != (unit, factor, result):
        raise ValueError("Unidades, calibrante y factor de expresión incompatibles")
    for key in ("aliquot_uL", "reagent_uL", "time_min", "wavelength_nm"):
        if not isinstance(p[key], (int, float)) or not 0 < p[key] < 1e9:
            raise ValueError(f"Parámetro positivo y finito requerido: {key}")
    if not 0 <= p["water_uL"] < 1e9 or not 0 <= p["r2_min"] <= 1 or not 0 < p["cv_max_percent"] < 1e9:
        raise ValueError("Agua, R² o CV inválidos")
    if not 0 <= p["recovery_min_percent"] < p["recovery_max_percent"] < 1e9:
        raise ValueError("Intervalo de recuperación inválido")
    if p["temperature_C"] is not None and not -273.15 < p["temperature_C"] < 1000:
        raise ValueError("Temperatura inválida")
    canonical(p)
    return p

def catalog(folder=None):
    values = copy.deepcopy(BUILTINS)
    if folder and Path(folder).exists():
        values.extend(json.loads(f.read_text(encoding="utf-8")) for f in sorted(Path(folder).glob("*.json")))
    return values

def save_variant(folder, protocol):
    p = validate(copy.deepcopy(protocol))
    folder = Path(folder); folder.mkdir(parents=True, exist_ok=True)
    path = folder / (digest(p) + ".json")
    if not path.exists():
        with path.open("x", encoding="utf-8") as f:
            f.write(canonical(p))
    return path


_legacy_validate=validate
def validate(p):
    if p.get('method')=='FRAP' and not p.get('engine'):return _legacy_validate(p)
    from .assay_engine import validate_protocol
    return validate_protocol(p)
