# Feature Design Document

Detailed breakdown of all features for the Protein Purification webapp, organized into implementation milestones. Each milestone is independently testable and builds on the previous ones.

Cross-references use the format "Spec §N.N" referring to sections in `../spec.md`.

---

## Milestone 1: Core Engine — Protein Data Model

**Goal**: Represent proteins with full biochemical properties and compute pH-dependent charge/isoelectric point.

### 1.1 Protein Dataclass (`backend/engine/protein.py`)

| Field | Type | Description | Spec |
|-------|------|-------------|------|
| `charges[0..6]` | `list[int]` | Residue counts: ASP, GLU, HIS, LYS, ARG, TYR, CYS | §2.1 |
| `mol_wt` | `float` | Native molecular weight (Da) | §2.1 |
| `no_of_sub1/2/3` | `int` | Chain type counts (sub1 ≥ 1) | §2.1 |
| `subunit1/2/3` | `float` | MW per chain type (0 if absent) | §2.1 |
| `original_amount` | `float` | Starting amount (mg) | §2.1 |
| `amount` | `float` | Current amount (mg) — mutated during purification | §2.1 |
| `temp` | `float` | Denaturation temperature (°C) | §2.1 |
| `ph1`, `ph2` | `float` | Stable pH range | §2.1 |
| `hydrophobicity` | `float` | Surface hydrophobicity factor | §2.1 |
| `original_activity` | `int` | Starting specific activity | §2.1 |
| `activity` | `int` | Current specific activity (may drop to 0) | §2.1 |
| `isopoint` | `float` | Isoelectric point (computed at load) | §2.3 |
| `his_tag` | `bool` | True if `charges[2] < -5` | §2.1 |
| `k1`, `k2`, `k3` | `float` | Gaussian peak parameters | §4 |

**Computed property**: `chains = no_of_sub1 + no_of_sub2 + no_of_sub3`

### 1.2 Henderson-Hasselbalch Charge Calculation (`backend/engine/protein_data.py`)

Two helper functions (Spec §2.2):
```
negCharge(pH, pK) = -z / (1 + z)      where z = 10^(pH - pK)
posCharge(pH, pK) = 1.0 / (1 + z)     where z = 10^(pH - pK)
```

Net charge at given pH:
```
Charge(pH) = charges[0]*neg(pH,4.6) + charges[1]*neg(pH,4.6)
           + |charges[2]|*pos(pH,6.65) + charges[3]*pos(pH,10.2)
           + charges[4]  // ARG always fully positive
           + charges[5]*neg(pH,9.95) + charges[6]*neg(pH,8.3)
           + chains*neg(pH,3.75) + chains*pos(pH,7.8)
```

### 1.3 Isoelectric Point Calculation (`backend/engine/protein_data.py`)

Iterative bisection (Spec §2.3):
1. Start at pH 7.0
2. If charge > 0, search upward; if < 0, search downward
3. Three passes with decreasing step sizes: 1.0, 0.1, 0.01
4. Return pH when charge crosses zero

Computed once per protein at load time.

### 1.4 Mixture File Parser (`backend/engine/mixture_io.py`)

**Standard format** (Spec §3.2): Lines starting with `//` are comments. First non-comment line is protein count. Then one line per protein with 22 comma-separated fields (no spaces).

**Save format** (Spec §3.4): Same as standard, optionally appended with:
- `enzymeIndex` (1-based)
- `numberOfSteps`
- One line per step: `stepType,proteinAmount,enzymeUnits,yield,enrichment,cost`

### 1.5 Constants Module (`backend/engine/constants.py`)

All named constants from Spec §15: pKa values, technique costs, matrix properties, position constants, limits.

### 1.6 Enums Module (`backend/engine/enums.py`)

- `SeparationType`: All 6 techniques
- `GelMatrix`: 9 gel filtration matrices
- `IonExchangeMedia`: DEAE-cellulose, CM-cellulose, Q-Sepharose, S-Sepharose
- `GradientType`: SALT, PH
- `HICMedia`: PHENYL_SEPHAROSE, OCTYL_SEPHAROSE
- `AffinityLigand`: 6 ligand types
- `ElutionMethod`: 4 elution methods
- `StainMode`: COOMASSIE, IMMUNOBLOT
- `SessionPhase`: SPLASH, MIXTURE_SELECTION, ENZYME_SELECTION, RUNNING, FINISHED

---

## Milestone 2: Core Engine — Separation Techniques

**Goal**: Implement all 7 separation techniques producing Gaussian elution profiles.

All techniques produce profiles over 250 fractions using:
```
Gauss(k1, k2, k3, x) = k3 * exp(-((x - k1) / k2)² / 2)
```
With overflow protection (exponent > 50 → 0) and K2 minimum of 0.00001.

### 2.1 Gaussian Kernel and Plot Array (`backend/engine/separation.py`)

`set_plot_array()` computes `fractions[1..250][0..N]` where:
- Index 0 = sum of all proteins at that fraction
- Index 1..N = individual protein amounts

### 2.2 Ammonium Sulfate Precipitation (Spec §4.1)

**Cost**: 2.0 | **Parameters**: saturation (0-100%)

Algorithm:
1. Spherical protein model: `radius = (MW × 0.75 / π)^(1/3)`
2. Surface area: `area = 4πr²`
3. Negative charges at pH 7: `negCharges = ASP + GLU + C_termini - CYS - TYR`
4. `chargePerArea = negCharges / area`
5. `logSzero = chargePerArea × 600.0`
6. `beta = logSzero / 2.5`
7. `molarity = saturation × 3.9 / 100.0`
8. `solubility = 10^(logSzero - beta × molarity)`
9. Compare against reference concentration (10 mg/mL)
10. User chooses soluble or insoluble fraction

**No Gaussian profile** — direct amount calculation.

### 2.3 Heat Treatment (Spec §4.2)

**Cost**: 1.0 | **Parameters**: temperature (°C), duration (minutes)

First-order kinetics:
```
exponent = (temperature - protein.temp) / 200.0 × duration
if exponent > 0: newAmount = currentAmount × exp(-exponent)
else: newAmount = currentAmount
```

**No Gaussian profile** — direct amount modification.

### 2.4 Gel Filtration (Spec §4.3)

**Cost**: 5.0 | **Parameters**: matrix type (9 options)

Peak position (log-linear MW interpolation):
- MW ≥ excluded: K1 = 50.0 (void volume)
- MW ≤ included: K1 = 220.0 (total volume)
- Otherwise: K1 = 50.0 + 170.0 × (log(excluded) - log(MW)) / (log(excluded) - log(included))

Peak width: `K2 = (K1 / factor) × sqrt(amount)`, min 5.0. Factor = 150 for HiRes, 100 otherwise.

### 2.5 DEAE Ion Exchange — Salt Elution (Spec §4.4)

**Cost**: 5.0 | **Parameters**: startGrad, endGrad (M), pH, titratable

Binds negatively-charged proteins. `molar = -charge / 44.0`

Routing: positive charge → flow-through (K1=40), titratable at pH≥10 → flow-through, molar ≤ startGrad → washed off (K1=85), inverted gradient → stays bound (K1=1000), otherwise → gradient elution.

**Activity loss**: pH outside protein's stable range → activity = 0.

### 2.6 DEAE Ion Exchange — pH Elution (Spec §4.5)

Decreasing pH gradient. Elutes at isoelectric point. K2 multiplied by 10 for wider peaks.

### 2.7 CM Ion Exchange — Salt Elution (Spec §4.6)

Mirror of DEAE: binds positively-charged proteins. `molar = charge / 66.0`. Titratable loses charge at pH ≤ 3.0.

### 2.8 CM Ion Exchange — pH Elution (Spec §4.7)

Increasing pH gradient. Mirror of DEAE pH elution.

### 2.9 Hydrophobic Interaction Chromatography (Spec §4.8)

**Cost**: 5.0 | **Parameters**: startGrad, endGrad (M), medium (Phenyl=100/Octyl=125)

Proteins bind at high salt, elute as salt decreases. Precipitation check uses modified AS calculation with `beta = logSzero / 4.0`.

### 2.10 Affinity Chromatography (Spec §4.9)

**Cost**: 25.0 | **Parameters**: ligand type, elution method

Binding is scrambled by `enzyme % 6`. Six ligands × four elution methods with specific amount/activity loss rules. High affinity → stuck (K1=5000). Low/no affinity → flow-through (K1=50).

### 2.11 Fraction Pooling (Spec §4.10)

```
totalArea = sqrt(2π) × K2 × K3
pooledArea = Σ Gauss(protein, f) for f in [start..end]
newAmount = currentAmount × (pooledArea / totalArea)
```

Display fractions 1..125 map to internal fractions 1..250 (2:1).

---

## Milestone 3: Core Engine — Accounting & State Machine

**Goal**: Track costs, step records, and enforce session rules.

### 3.1 StepRecord Dataclass (`backend/engine/step_record.py`)

Per-step fields (Spec §5.1):
- `step_type`: Technique identifier
- `protein_amount`: Sum of all proteins' currentAmount
- `enzyme_units`: `amount(enzyme) × activity(enzyme) × 100.0`
- `enzyme_yield`: `(enzymeUnits / initialEnzymeUnits) × 100.0`
- `enrichment`: `(enzymeUnits/proteinAmount) / (initialEU/initialPA)`
- `cost_per_unit`: `totalCost × 100.0 / enzymeUnits`

Step 0 (initial): yield = 100%, enrichment = 1.0.

### 3.2 Cost Tracking (`backend/engine/account.py`)

Accumulated cost per technique (Spec §5.2):

| Technique | Cost |
|-----------|------|
| Ammonium sulfate | 2.0 |
| Heat treatment | 1.0 |
| Gel filtration | 5.0 |
| Ion exchange | 5.0 |
| HIC | 5.0 |
| Affinity | 25.0 |
| 1D PAGE | 3.0 |
| 2D PAGE | 5.0 |
| Enzyme assay | 2.0 |
| Dilution | 1.0 |

### 3.3 Failure Conditions (Spec §1.2)

| Condition | Threshold |
|-----------|-----------|
| Enzyme lost | `enzymeUnits < 0.01` |
| Too many steps | `step == 11` |
| Cost too high | `costPerUnit > 1000.0` |

### 3.4 Session State Machine (`backend/engine/session.py`)

Key state variables (Spec §9.3):

| Variable | Controls |
|----------|----------|
| `pooled` | Separation menu enabled |
| `has_fractions` | Fractions menu enabled |
| `assayed` | Red line on elution profile |
| `has_gradient` | Gradient line on elution profile |
| `scale` | Y-axis range (0.5–16.0) |
| `over_diluted` | Max dilution reached |

State transitions (Spec §9.4):
- After separation: fractions ON, separation OFF
- After pooling: separation ON, fractions OFF
- Assay: disabled after first use per step
- Dilute: disabled when scale = 16.0
- Abandon step: returns to pooled state

---

## Milestone 4: Core Engine — Gel Electrophoresis Calculations

**Goal**: Compute band/spot positions and intensities for PAGE visualization.

### 4.1 1D SDS-PAGE Bands (`backend/engine/gel.py`)

Band position (Spec §6.1): `Mobility(MW) = 120 × (11.5 - log₁₀(MW))`

Shows subunit bands (by subunit MW), not native protein.

Band intensity: `proteinAmount / totalProteinInFraction`

| Intensity | Visual |
|-----------|--------|
| < 0.001 | Invisible |
| 0.001–0.05 | Thin line |
| 0.05–0.2 | Narrow (h=2) |
| 0.2–0.5 | Medium (h=3) |
| ≥ 0.5 | Thick (h=4) |

Lane layout: 30 units width per fraction, starting at x=4. MW markers (left lane): 80K, 60K, 50K, 40K, 30K, 20K, 10K, 5K.

### 4.2 2D PAGE Spots (`backend/engine/gel.py`)

Spot position (Spec §6.2):
- X: `(isopoint - 4.0) × 100.0`
- Y: `Mobility(subunit_MW)`

Spot size (intensity-scaled polygons):

| Intensity | Shape | Vertices |
|-----------|-------|----------|
| 0.0005–0.001 | Line | 2 |
| 0.001–0.01 | Small hexagon | 6 |
| 0.01–0.1 | Medium hexagon | 6 |
| 0.1–0.2 | Octagon | 8 |
| 0.2–0.5 | Large polygon | 10 |
| ≥ 0.5 | Starburst | 16 |

### 4.3 Staining Modes (Spec §6.3)

- **Coomassie blue**: All proteins, drawn in blue (0, 0, 255)
- **Immunoblot**: Target enzyme only, drawn in black (0, 0, 0)

---

## Milestone 5: REST API Layer

**Goal**: Expose the engine via a stateful REST API. Each mutation returns full `SessionState`.

### 5.1 Session Lifecycle (`backend/api/sessions.py`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/sessions` | POST | Create new session |
| `/api/sessions/load` | POST | Upload .ppmixture file |
| `/api/sessions/{id}/state` | GET | Full state snapshot |
| `/api/sessions/{id}` | DELETE | Abandon session |
| `/api/sessions/{id}/choose-mixture` | POST | Select mixture by name |
| `/api/sessions/{id}/choose-enzyme` | POST | Select target enzyme |

### 5.2 Separation (`backend/api/separation.py`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/sessions/{id}/separate` | POST | Run separation with params |
| `/api/sessions/{id}/as-choice` | POST | AS soluble/insoluble choice |
| `/api/sessions/{id}/abandon-step` | POST | Discard current separation |

### 5.3 Fractions (`backend/api/fractions.py`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/sessions/{id}/assay` | POST | Run enzyme assay |
| `/api/sessions/{id}/dilute` | POST | Dilute (2× scale) |
| `/api/sessions/{id}/pool` | POST | Pool fraction range |

### 5.4 Electrophoresis (`backend/api/electrophoresis.py`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/sessions/{id}/page-1d` | POST | Run 1D PAGE |
| `/api/sessions/{id}/page-2d` | POST | Run 2D PAGE |
| `/api/sessions/{id}/toggle-stain` | POST | Switch stain mode |

### 5.5 Files (`backend/api/files.py`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/sessions/{id}/save` | GET | Download .ppmixture |

### 5.6 Mixtures (`backend/api/mixtures.py`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/mixtures` | GET | List available mixtures |

### 5.7 Session State Response Schema

Every mutation endpoint returns `SessionState`:

```json
{
  "sessionId": "uuid",
  "phase": "running",
  "mixtureName": "Default Mixture",
  "enzymeIndex": 3,
  "pooled": true,
  "hasFractions": false,
  "assayed": false,
  "hasGradient": false,
  "twoDGel": false,
  "showBlot": false,
  "scale": 0.5,
  "overDiluted": false,
  "step": 2,
  "fractions": [[0.0, "..."], "..."],
  "records": [{"stepType": "Initial", "...": ""}],
  "gradientStart": 0.0,
  "gradientEnd": 0.0,
  "gradientType": "",
  "separationTitle": ""
}
```

---

## Milestone 6: Frontend — Core UI

**Goal**: Build the main application shell and all parameter dialogs.

### 6.1 Splash Screen (`frontend/src/views/splash.ts`)

Text display with 3D shadow effect (Spec §14):
- Application title (large, bold)
- Author: Prof. Andrew Booth
- "New Session" and "Load Saved" buttons

### 6.2 Toolbar (`frontend/src/components/toolbar.ts`)

Horizontal action bar with sections:
- **Separation**: Ammonium Sulfate, Heat Treatment, Gel Filtration, Ion Exchange, HIC, Affinity
- **Analysis**: 1D PAGE, 2D PAGE, Coomassie/Immunoblot toggle, Hide Gel, Assay, Dilute
- **Fractions**: Pool, Abandon Step

Buttons enabled/disabled by `SessionState` flags (Spec §9.4).

### 6.3 Mixture Selection Dialog

Radio buttons for 4 bundled mixtures + file upload for .ppmixture.

### 6.4 Enzyme Selection Dialog

Numbered list of proteins in mixture. User selects target enzyme.

### 6.5 Parameter Dialogs (one per technique)

| Dialog | Inputs | Spec |
|--------|--------|------|
| Ammonium Sulfate | Saturation % spinner, then soluble/insoluble choice | §10.1 |
| Heat Treatment | Temperature spinner, Duration spinner | §10.2 |
| Gel Filtration | 9 matrix radio buttons | §10.3 |
| Ion Exchange | Media radios → pH spinner → gradient type + start/end | §10.4 |
| HIC | Medium radios → salt gradient start/end | §10.5 |
| Affinity | Ligand radios → elution method dropdown | §10.6 |

### 6.6 Fraction Selection Dialogs (Spec §10.7)

- 1D PAGE: Multi-select checkbox list
- 2D PAGE: Single fraction select
- Pool: Start/end fraction spinners

### 6.7 Step Result Dialog (Spec §8.2)

Shows after pooling: protein (mg), enzyme units, enrichment, yield %, cost/unit.

### 6.8 Failure Dialog (Spec §1.2)

"Oops" with specific message. Retry (abandon step) or quit options.

### 6.9 Purification Record Table (`frontend/src/views/record.ts`)

HTML table (Spec §8.1):

| Method | Protein (mg) | Enzyme (Units) | Yield (%) | Enrichment | Cost |
|--------|-------------|----------------|-----------|------------|------|

Row 0 = Initial, then one row per completed step.

---

## Milestone 7: Frontend — Interactive Visualizations

**Goal**: Chromatograms with Plotly.js, gel images with Canvas.

### 7.1 Elution Profile / Chromatogram (`frontend/src/views/elution.ts`)

**Renderer**: Plotly.js

Traces:
- **Blue**: Absorbance at 280 nm (fractions[i][0])
- **Red**: Enzyme activity (when assayed)
- **Magenta**: Gradient line (salt or pH, when applicable)
- **Black cross-hatch**: Pooled fraction region

Axes:
- X: Fraction number 1-125
- Y-left (blue): Absorbance, scale-dependent
- Y-right (red): Enzyme activity
- Y-right (magenta): Gradient values

Title format: "[Technique] on [Medium]"

Interactive: Plotly drag-select for pooling fraction range.

### 7.2 Scale / Dilution Display

Initial scale = 0.5. Each dilution doubles (0.5 → 1.0 → ... → 16.0 max). Y-axis adjusts. Resets after pooling.

### 7.3 1D PAGE Gel (`frontend/src/views/gel.ts`)

**Renderer**: HTML5 Canvas

- Gray background (208, 208, 224) with 3D shadow
- MW markers in left lane
- Band thickness by intensity
- Blue (Coomassie) or black (Immunoblot)
- Lane width: 30 units, starting at x=4

### 7.4 2D PAGE Gel (`frontend/src/views/gel.ts`)

**Renderer**: HTML5 Canvas

- IEF x SDS-PAGE
- pH axis 4-9 at top
- Intensity-scaled polygon spots (2-16 vertices)
- Same stain toggle

---

## Milestone 8: Localization & Polish

**Goal**: Multi-language support, file I/O, help, and responsiveness.

### 8.1 i18n Resource Files (`frontend/src/i18n/`)

Extract strings from existing `Localizable.strings` (macOS/iOS) and `.rc` resource files (Windows) into JSON:
- `en.json` --- English
- `es.json` --- Spanish
- `fr.json` --- French
- `id.json` --- Indonesian

### 8.2 Language Switcher

Dropdown in toolbar. Switches all UI text via i18next.

### 8.3 .ppmixture Save/Load

- **Save**: Download current state as .ppmixture with purification history
- **Load**: Upload .ppmixture file to restore session

### 8.4 Help System (Spec §13)

- About dialog with credits
- Help index (embedded HTML)
- Context-sensitive help per technique dialog

### 8.5 Session Timeout

Auto-cleanup after 2 hours of inactivity. Background task in FastAPI lifespan.

### 8.6 Responsive Layout

Tablet-friendly (min ~768px width). Flexbox layout. Toolbar wraps gracefully.

---

## Key Design Decisions

1. **Engine is a pure Python package** (`backend/engine/`) with zero web dependencies --- testable with pytest alone, importable from Jupyter notebooks or CLI scripts.

2. **Server-authoritative state** --- all simulation runs on the server. Students cannot manipulate data client-side. The frontend is a "dumb" display layer.

3. **In-memory session store** --- `dict[str, PurificationSession]` with timeout cleanup. No database needed; sessions are transient educational exercises.

4. **Full state snapshots** --- every mutation endpoint returns the complete `SessionState`. The frontend replaces its local state entirely, avoiding synchronization bugs.

5. **Plotly.js for chromatograms** --- interactive zoom, hover tooltips, and native drag-select for fraction pooling. Much richer than the original static GDI/Quartz rendering.

6. **Canvas for gels** --- custom polygon rendering for bands and spots doesn't suit charting libraries. Direct Canvas drawing matches the original platform-native approach.

7. **Numerical fidelity** --- Python float64 vs legacy C++ float32/float64 mix may cause tiny differences. Tests use relative tolerance (1e-6) for numerical comparisons.
