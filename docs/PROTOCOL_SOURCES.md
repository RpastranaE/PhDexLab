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

## Calculation and methodology audit for 0.9.3

The audit separates published chemistry, the chosen operating adaptation, dimensional correctness and software verification. A matching synthetic workbook does not establish chemical validation, extraction recovery, a suitable linear range or biological independence. New catalogue snapshots are version 4; previously saved conditions remain unchanged.

### Concentration, amount and result per mass

For FRAP, ABTS, CUPRAC, TPC and TFC the common mass-normalisation equation is:

`result = C_axis × R × FD × (V_extract_mL / 1000) / m_g × F`

- `C_axis = (response − fitted intercept) / fitted slope`. The fit uses level means, equal weight per level and a free intercept. Coefficients are retained at full precision. A blank is subtracted once; instrument-zeroed input must be declared. No sample background is invented.
- `R = 1` for an axis giving the concentration **before reaction**. For a **final-mixture** axis, `R = total reaction volume / sample aliquot`. Standards and samples must have comparable reaction conditions. Entering the reaction dilution again in `FD` counts it twice.
- `FD` is prior sample dilution, including the product of serial dilutions. `V_extract_mL` is the total extraction/reconstitution volume represented by `m_g`, not the reaction volume. Enter grams, not milligrams, in `mass_g`. Do not use an initial solvent volume when evaporation, pooling or reconstitution changed it.
- `F` is the stated unit/reporting conversion. Expressing mg per 100 g uses a factor of 100 but **does not make the result a percentage**. A mass-equivalent result per gram of extract cannot be renamed per gram of leaf without the represented leaf mass/extraction yield.

The Excel Processing sheet exposes this chain in columns G:M, with the final result in E and its unit in F. Results also states each row's unit. A control is a calibration quality check: `100 × C_axis / expected`, in **% recovery**, with expected expressed on the same axis. Controls are excluded from biological summaries and sample figures. A control carrying extraction mass/volume/dilution is now rejected rather than silently ignoring them. This is a confirmed ambiguity/validation defect, not evidence that the previous sample normalisation had an extra percent factor.

Individual observations at several prior dilutions can share one sample and biological-unit ID. Normalise each observation first, then average all entered observations with equal weight within the unit. Technical n counts those observations; biological n still counts independent extractions. More observations at one dilution give it more weight: select a balanced design or document the chosen observations. Their within-unit SD includes dilution-to-dilution variation. One supplied mean per unit is supported; different-dilution means cannot be silently combined without the underlying observations.

### Review of every included variant

`R` below is applied only when **final** is selected. With **before**, it is always 1. These factors follow the recorded volumes, not a second arbitrary correction.

| Included variant | Response / interpretation | Final-axis R; F; resulting unit | Source and operating qualification |
|---|---|---|---|
| FRAP Fe(II) | Matched blank-corrected ΔA at 593 nm; endpoint is a documented adaptation | 34; 1; µmol eq Fe(II)/g | Benzie–Strain. Original plasma measurement and adaptation to leaf/extract mass are distinct. Trolox is not Fe(II). |
| FRAP Trolox, adapted | Blank-corrected endpoint | 16; 100; mg TE/100 g | Pineapple-core study. Establish the working reagent, range and represented sample mass. |
| ABTS, Re | `100 × (A_radical − A_corrected)/A_radical`; interpolate against Trolox | 101; 1; µmol TE/g | Re et al. Final-mixture axis by default. Inhibition is an intermediate percentage; the final TE/g result is not. |
| ABTS, adapted | Same inhibition definition at the documented endpoint | 16; 100; mg TE/100 g | Pineapple-core adaptation; do not substitute the original reaction conditions. |
| CUPRAC | Blank-corrected endpoint at 450 nm | `4100 / aliquot_uL`; 1; µmol TE/g | Apak normal procedure uses a 4.1 mL mixture and a 1 h reading; its introduction also discusses 30–60 min. Complete x and water. Published molar absorptivity uses final concentration; a before-axis calibration requires a fixed common aliquot, not one stock concentration for varying x. No automatic hydrolysis/heating. |
| TPC, base Folin | Blank-corrected endpoint, operational reducing response | 11; 0.17012; mg GAE/g | Ainsworth–Gillespie. Conversion is 170.12 g/mol for anhydrous gallic-acid equivalents, divided by 1000. Correct reagent purity/hydration when preparing molar standards. Transferring an aliquot to a plate does not dilute it. |
| TPC, adapted | Blank-corrected endpoint; its own addition order | 6.5; 100; mg GAE/100 g | Pineapple-core study. The already corrected 760 nm default is retained; carbonate concentration basis/range need operating confirmation. |
| TFC, AlCl3/quercetin | Blank-corrected endpoint | 10; 1; mg QE/g **dry extract** | Chang reference and the Scientific Reports operating adaptation. The latter redissolves freeze-dried extract; the former inherited dry-leaf default was wrong for that source and is corrected. Quercetin, rutin and epicatechin equivalents are not interchangeable. |
| DPPH, kinetics/EC50 | Matched-time radical control; inhibition at operator-confirmed plateau | No extraction-mass normalisation; mg extract/mL final mixture | Brand-Williams reports pure-compound molar-ratio EC50. This app explicitly adapts the dose to extract mass, with local linear interpolation across 50%, no extrapolation and no automatic plateau. It does not calculate the original molar EC50 or reciprocal antiradical power. Final dose is aliquot dose/40 for the recorded 0.1 + 3.9 mL mixture; do not divide twice. |
| Moisture, oven | `100 × (m_initial − m_final)/(m_initial − tare)` | % of initial net mass | Ramírez et al.; drying to constant mass. Loss on drying need not be chemically specific water. |
| Dry matter | `100 × (m_final − tare)/(m_initial − tare)` | % of initial net mass | de Oliveira et al., oven determination. Complements moisture only for the same aliquot and endpoint. |
| Ash, 500 °C | `100 × (m_residue − tare)/(m_initial − tare)` | % initial mass; divide by dry fraction only for dry-basis reporting | de Oliveira et al. Record which initial mass was weighed; do not correct already-dry material twice. `dry_fraction` is 0–1, not 0–100. |
| Moisture, TAPPI adaptation | Same moisture equation after completing operating conditions | % initial mass | Remains blocked until standard/conditions are identified. A synthetic equation check does not supply the missing standard. |
| Ash, TAPPI adaptation | Same ash equation after completing operating conditions | % on the declared basis | Remains blocked. Nitrogen-atmosphere thermal residue is not oxidative ash. |
| Sieving | `100 × fraction retained mass / loaded mass`; separate recovery balance | % loaded mass | Explicit mass-distribution adaptation using the cited particle-size studies. Actual sieve limits are µm (1 mm = 1000 µm). Lost mass is visible; fractions are not renormalised to 100%. These papers do not constitute a universal standard for sieve operation. |

The primary links for each row are in the source table above. Full-text checks additionally used [Apak's original article](https://doi.org/10.1021/jf048741x), [the pineapple study's assay section](https://link.springer.com/article/10.1007/s11947-024-03620-9), [the TFC operating procedure](https://pmc.ncbi.nlm.nih.gov/articles/PMC10497595/), [the moisture procedure](https://pmc.ncbi.nlm.nih.gov/articles/PMC9738326/), [the dry-matter/ash procedure](https://pmc.ncbi.nlm.nih.gov/articles/PMC10975974/) and [the particle-size study](https://pubs.rsc.org/en/content/articlehtml/2023/fb/d3fb00108c). The TPC original publisher PDF was inaccessible during this audit; its operating details were checked against the available supplied protocol and publisher abstract, not claimed re-read from that PDF.

### The supplied FRAP benchmark is a test, not the method authority

The [Zen-Bio AOX-11 manual](https://www.zen-bio.com/pdf/cell-manuals/ZBM0119.pdf), pp. 5–7, describes an endpoint kit procedure, different from the 4 min paired-read reference. Its example curve is explicitly not a substitute for measuring a calibration. The attached benchmark's calibration transcribes the example; its olive observations are labelled simulated. Its sample-example cell D8 contains 0.303 whereas the original gives 0.3033. The manufacturer's displayed example calculations also use rounded regression coefficients. Full-precision regression is retained in software; differences caused by rounded coefficients are not corrected by adding an empirical factor.

The local cross-check uses raw observations and an independently computed OLS fit, followed by dimensional normalisation for each reading. No coefficients, targets or expected result are read from the benchmark's calculation cells. All nine extraction means and within-unit SDs match the generated Excel; biological n is three for each lot. This numerical agreement does not validate simulated olive chemistry or resolve the exact inputs in a separate, unprovided app-generated workbook. Details and repeatable commands are in [Validation](VALIDATION.md) and [Development](DEVELOPMENT.md).
