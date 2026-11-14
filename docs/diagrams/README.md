# Attention Garden · diagrams

Diagrams for talks and papers (3840 × 2160 PNG). No third-party artwork is included.

| File | What it shows | Basis |
|---|---|---|
| F12_prompt(_min) | Prompt reuse: a feed copies the item, generation copies the recipe | Conceptual; prompts are illustrative |
| F13_attention(_min) | 254,000 images a day from the feed vs 19,200 one person could see | Installation speed; stated assumptions |
| F6_breeding | Spreading vs breeding | Conceptual |
| F7_cost | Energy per generation; data-centre electricity 2024 → 2030 | Luccioni et al. 2024; IEA 2025 |
| F5_system | How the installation works: input, three screens, output | Code |
| F1_growth | One plant, ten states | Code (STG) |
| F2_flow | Where a plant's attention comes from | Code; ribbon widths schematic |
| F3_taxonomy | From images to 8 clusters to 14 species | Code; scatter positions schematic |
| F4_interaction | Gaze, meter, algorithmic gaze priorities | Code |
| F8_anatomy | Anatomy of a flower: what each parameter controls | Code (SPECIES, plantAt) |
| F9_streams | Which species win over 20 minutes | Simulation (data/sp_*.json) |
| F10_agency | Who holds which dial; three settings compared | Code + simulation |
| F11_site | Proposed Sydney setup, plan view | Proposed |

`_min` versions drop titles and footnotes so slide text can be added on top.

## Regenerating

Scripts are in `src/` (Python 3, no dependencies; rendering uses Playwright + Chromium):

```bash
python3 src/final.py src OUT            # F1–F4
python3 src/flow.py src OUT             # F5
python3 src/extra.py src OUT            # F6, F7
python3 src/more.py src OUT data        # F8–F11 (uses data/sp_*.json)
python3 src/prompt2.py src OUT [min]    # F12, F13
node src/svgshot.js OUT/F1_growth.svg OUT/F1_growth.png 2
```

Simulations (`src/sim.js`, `src/simsp.js`) run the piece's own update functions headless for 20 minutes.
