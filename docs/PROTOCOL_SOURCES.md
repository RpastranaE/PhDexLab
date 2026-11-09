# Published protocol sources

These links identify the publication associated with each built-in starting point. Local operating adaptations, unresolved conditions and matrix validation are distinct from the cited original method. Archived experiment snapshots are not rewritten when the built-in catalogue changes. Internal IDs retain their historical spelling for compatibility.

| Protocol | Primary source / adaptation |
|---|---|
| FRAP Fe(II) | [Benzie and Strain, 1996](https://doi.org/10.1006/abio.1996.0292) |
| FRAP Trolox; adapted ABTS, TPC, moisture and ash | [Pineapple-core sequential extraction study, online 2024](https://doi.org/10.1007/s11947-024-03620-9). These adaptations must not be conflated with the original Fe(II) FRAP or base TPC procedures. TAPPI operating conditions remain incomplete. |
| ABTS | [Re et al., 1999](https://doi.org/10.1016/S0891-5849(98)00315-3) |
| CUPRAC | [Apak et al., 2004](https://doi.org/10.1021/jf048741x) |
| DPPH kinetics / EC50 | [Brand-Williams et al., 1995](https://doi.org/10.1016/S0023-6438(95)80008-5) |
| TPC | [Ainsworth and Gillespie, 2007](https://doi.org/10.1038/nprot.2007.102); background [Singleton et al., 1999](https://doi.org/10.1016/S0076-6879(99)99017-1) |
| TFC AlCl3 / quercetin | [Chang et al., 2002](https://doi.org/10.38212/2224-6614.2748); operating adaptation [Scientific Reports, 2023](https://doi.org/10.1038/s41598-023-42418-1). Quercetin and rutin are different calibration variants; changing the reference requires the operator to document the method. |
| Oven moisture | [Ramírez et al., 2022](https://doi.org/10.3390/foods11233879) |
| Dry matter and ash | [de Oliveira et al., 2024](https://doi.org/10.3390/ph17030274) |
| Sieving | [Comparative particle-size study, 2023](https://doi.org/10.1039/D3FB00108C); supplementary [olive-leaf extraction study, 2014](https://doi.org/10.3390/foods3010066) |

Reference protocol is a catalogue label, not a statement of analytical validation. Software QC limits remain illustrative. No missing operating conditions are invented by removing the former draft label.


## Input review for 0.9.2

This review uses the existing operating protocol snapshots and the primary references above. It changes data-entry choices, not chemical validation. Original experiment snapshots are not rewritten. New catalogue variants are version 3.

| Method / variant | Appropriate entries and available choices |
|---|---|
| FRAP Fe(II) reference | Paired initial/final signal as documented; already measured ΔA can be supplied directly. Endpoint input is an explicitly recorded operator adaptation. Individual readings or one supplied mean per biological unit/condition. |
| FRAP Trolox adaptation | Endpoint absorbance at the selected time; no initial required. Reagent composition/range remain subject to the documented operating confirmation. |
| ABTS original/adapted | Endpoint sample/standard absorbance plus a radical control, at matching conditions. The radical control cannot be replaced by zero. Mean n/SD may be supplied; absorbance SD is converted to inhibition SD. |
| CUPRAC | Endpoint 450 nm. Aliquot x and water must be completed consistently with 4.10 mL; the existing 30/60 min source discrepancy remains explicit. No invented aliquot or fixed replicate requirement. |
| TPC base | Endpoint 765 nm; duplicate entry slots are suggested, with any number allowed. |
| TPC adapted | Endpoint **760 nm**, corrected in the new catalogue to match the supplied operating protocol; saved older 765 nm variants remain unchanged. Order of addition, solvent and carbonate qualifications remain distinct from the base method. |
| TFC AlCl3 | Endpoint 415 nm with its selected documented quercetin/rutin calibration variant. No initial absorbance required and no equivalence conversion invented. |
| DPPH / EC50 | Individual absorbances or a mean per dose/time/biological unit; retain final-mixture dose, matched radical control and operator plateau confirmation. A supplied EC50 cannot replace absorbance data. |
| Moisture / dry matter / ash | Tare, initial and final masses; these are weighings, not initial/final absorbances. No replacement with a mean final percentage because raw ratios cannot be recovered. Use distinct units for independent aliquots. |
| Adapted TAPPI methods | Still pending the identified standard/operating conditions; input flexibility does not invent missing conditions. |
| Sieving | One mass per fraction, real aperture limits and loaded mass, another unit for another independent sieving run. No absorbance fields or normalisation to 100%. |

For colorimetric assays, blank handling may explicitly declare instrument-zeroed readings instead of a second subtraction. Additional sample background is disabled by default and requires a separate justified net contribution when enabled. Technical n/SD of supplied means are operator-reported; unknown precision remains unavailable. The minimum calibration-level count is configurable, with 2 as a mathematical minimum rather than a linearly validated method recommendation.
