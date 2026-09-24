# ⚙️ NanoMill: Planetary Ball Mill Multiphysics Simulation & AI 3D Modeling Suite

A comprehensive, Python-based multiphysics engineering suite designed to model, simulate, and design a **high-energy planetary ball mill** dedicated to the mechanical synthesis of **nanoparticles** (<100 nm).

Compatible with **local execution** (Python CLI & interactive Streamlit web dashboard) and **Google Colab** with zero friction.

---

## 🌟 What is the Best Tool for AI Models to Create 3D Models?

When designing physical machines using AI models (such as Antigravity, Gemini, Claude, or GPT), **the choice of 3D modeling framework is critical**:

### Why AI Models Cannot Generate Binary CAD Files Directly
Binary CAD formats (such as native `.step`, `.iges`, or compiled `.stl` files) are binary byte streams or deeply nested B-Rep data structures with strict floating-point topological references. LLMs produce text, not binary streams; attempting to have an AI generate binary STL directly results in corrupted geometry.

### The Solution: "Code-as-CAD"
The universal, most reliable paradigm is **Code-as-CAD**—where the AI writes human-readable, declarative programming code that is then rendered into 3D solid geometry.

| Tool / Framework | AI Compatibility | Strength | Best Use Case |
| :--- | :--- | :--- | :--- |
| **1. OpenSCAD (`.scad`)** | ⭐⭐⭐⭐⭐ **(The Gold Standard)** | Pure declarative Constructive Solid Geometry (`union()`, `difference()`, `cylinder()`, `rotate()`). AI models have near 100% accuracy writing OpenSCAD. | 3D printing, rapid mechanical prototyping, parametric AI generation. Exports to STL/3MF. |
| **2. Build123d / CadQuery (Python)** | ⭐⭐⭐⭐☆ **(Best for CNC/Machining)** | Python-based solid modeling using the OpenCASCADE CAD kernel. Real fillets, chamfers, and exact B-Rep STEP files. | Precision engineering, CNC milling, injection molding tolerances. |
| **3. Three.js / CSG (JavaScript/WebGL)** | ⭐⭐⭐⭐☆ **(Best for Interactive Web)** | Procedural 3D in the browser. AI can generate JSON specs or JS scripts that render immediately with 60 FPS orbit controls. | Web dashboards, Google Colab visualizers, client demos. |

> **Recommendation implemented in NanoMill:**  
> NanoMill generates **OpenSCAD (`.scad`)** so any AI model can edit and expand your ball mill assembly, **Pure-Python Binary STL (`.stl`)** for immediate 3D printing, and **Interactive Three.js WebGL (`.html`)** for interactive 3D inspection directly in Google Colab and web browsers!

---

## 🔬 Multiphysics Simulation Capabilities

### 1. Mechanical Kinematics & Non-Inertial Dynamics
- **Planetary Kinematics:** Computes sun wheel angular speed $\Omega$, vial relative spin $\omega$, and transmission ratio $k = \omega / \Omega$.
- **Centrifugal & Coriolis Field:** Calculates non-inertial accelerations in the rotating vial frame:
  $$\mathbf{a} = \mathbf{a}_{centrifugal} + 2 (\mathbf{\Omega} \times \mathbf{v}_{rel})$$
- **High-Energy Regime Verification:** Validates that the system operates in the **Cataracting regime** ($>25\text{–}40\text{ G}$) required for shock-induced grain refinement rather than low-energy cascading attrition.
- **Drive Sizing:** Computes rotational inertia ($I_{total}$), startup torque, steady-state milling torque, and required motor power (W / HP).

### 2. DEM Ball Collision Dynamics & Energy Spectra
- **Impact Velocity ($v_{imp}$):** Solves relative detachment and collision velocity across the milling chamber.
- **Single-Ball Impact Energy ($E_k$):** $E_k = \frac{1}{2} m_b v_{eff}^2$.
- **Collision Frequency ($f_{imp}$):** Quantifies impacts per second per vial as a function of relative slip and ball count.
- **Specific Milling Power ($W/g$):** Dissipated mechanical power per gram of powder charge.
- **Pre-loaded Materials Database:** Tungsten Carbide ($WC$, $\rho = 14,900\text{ kg/m}^3$), Zirconia ($ZrO_2$, $\rho = 6,000\text{ kg/m}^3$), Stainless Steel ($AISI\ 316$, $\rho = 7,900\text{ kg/m}^3$), and Agate ($SiO_2$).

### 3. Nanoparticle Comminution Kinetics
- **Micro-to-Nano Transition:** Simulates size reduction from micro-powders ($45\,\mu\text{m}$) down to the sub-50 nm regime.
- **Hall-Petch & Dislocation Limit:** Incorporates dislocation pile-up breakdown at sub-micron scales.
- **Agglomeration & Surfactant Model:** Predicts cold-welding behavior and highlights the necessity of Process Control Agents (PCA / surfactants) to reach the $<25\text{ nm}$ grind limit.

### 4. Thermal & Heat Dissipation Simulation
- **Inelastic Thermal Generation:** ~90% of dissipated collision energy converts directly into thermal energy inside the vial.
- **Conduction & Convection:** Computes cylinder wall conduction and turbulent forced convection ($h_{conv}$) driven by high peripheral spin velocities.
- **Transient Heating Curves:** Tracks $T(t)$ over time, computes equilibrium temperature ($T_{eq}$), and prevents O-ring seal failure and powder thermal oxidation.

### 5. Automated Engineering Report Generator
- Produces complete, publication-grade technical reports in **Markdown (`.md`)** and **Printable HTML (`.html`)**.
- Automatically generates 3 high-resolution diagnostic plots:
  1. `mill_kinematics_trajectories.png` (Ball flight paths and circumferential G-force distribution).
  2. `nano_comminution_kinetics.png` (Evolution of $D_{50}$, $D_{90}$, and Specific Surface Area $SSA$).
  3. `thermal_transient_profile.png` (Transient heating curve vs safety limits).
- Provides a comprehensive Bill of Materials (BOM) for fabrication.

---

## 🚀 How to Run

### Method 1: Interactive Local Web Dashboard (Streamlit)
The easiest way to design, tune parameters with live sliders, and inspect the 3D model:
```bash
streamlit run app.py
```
Open `http://localhost:8501` in your browser.

---

### Method 2: Google Colab
1. Upload the provided notebook **`Ball_Mill_Nano_Simulation.ipynb`** directly to [Google Colab](https://colab.research.google.com).
2. Upload the `nanomill/` folder to the Colab session files.
3. Run all cells:
   - Interactive 3D WebGL viewer runs inside the notebook cells.
   - Live plots and markdown reports display inline.
   - OpenSCAD (`.scad`) and STL (`.stl`) files can be downloaded directly from Colab.

---

### Method 3: Command-Line Simulation Runner
To run batch simulations or export files directly:
```bash
python simulation_cli.py --sun-rpm 480 --gear-ratio -2.0 --media "Zirconia (ZrO2 - YSZ)" --ball-diam 8.0 --hours 12.0
```
All outputs are saved to the `output/` directory:
- `output/ball_mill_assembly.scad` (AI-editable OpenSCAD model)
- `output/ball_mill_assembly.stl` (Binary 3D mesh)
- `output/ball_mill_3d_viewer.html` (Interactive 3D WebGL viewer)
- `output/engineering_report.md` & `output/engineering_report.html` (Full report)
- `output/*.png` (Engineering figures)

---

## 🤖 Prompting AI Models to Modify the 3D Model
To have Antigravity or any LLM modify the 3D model, simply paste `output/ball_mill_assembly.scad` into the chat and instruct:
- *"Add an external cooling fin jacket around each vial to improve convective heat dissipation."*
- *"Increase the number of planetary vials to 8 and adjust the sun disc radius to maintain 35G."*
- *"Add a quick-release cam latch mechanism to the vial clamping lids."*

The AI will output modified OpenSCAD code that you can preview in OpenSCAD or export directly to STL for 3D printing.
