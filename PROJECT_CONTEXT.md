# Physics I can see — project context and maintenance notes

This document is a handoff for future AI assistants and maintainers. Read it before changing the simulations. It records the implementation as of 28 November 2026; inspect the files for the latest parameter values.

## Purpose and editing conventions

The project teaches particle dynamics through Python notebooks, animated plots, standalone interactive HTML players, and MP4 videos.

- Make focused changes. The user explicitly prefers minimal edits and preservation of existing explanations and notebook structure.
- Keep initialization, physics, visualization, and export cells understandable and in execution order.
- Preserve user changes to initial conditions, field strengths, and other parameters.
- Explain approximations accurately. Do not describe finite-time survival as guaranteed confinement, or a restitution law as conservation of the ball's momentum.
- Browser simulations and Python simulations must agree. Changes to physics usually require changes in both the notebook and its HTML-player helper.

## Files and responsibilities

| Simulation | Python notebook | HTML-generator helper | Exported files |
|---|---|---|---|
| Bouncing ball | `Bouncing Ball/Newton_laws.ipynb` | `Bouncing Ball/bouncing_ball_player.py` | `bouncing_ball.html`, `bouncing_ball.mp4` |
| Uniform Lorentz force | `Lorentz Force/Lorentz_force.ipynb` | `Lorentz Force/lorentz_force_player.py` | `lorentz_force.html`, `lorentz_force.mp4` |
| Tokamak test particle | `Lorentz Force/tokamak.ipynb` | `Lorentz Force/tokamak_player.py` | `tokamak.html`, `tokamak.mp4` |
| Vicsek flocking | `Vicsek model/Viscek.ipynb` | `Vicsek model/vicsek_player.py` | `vicsek.html`, `vicsek.mp4` |
| Vicsek flocking in 3D | Same notebook, appended 3D section | `Vicsek model/vicsek_3d_player.py` | `vicsek_3d.html`, `vicsek_3d.mp4` |
| Vicsek inside a sphere | `Vicsek model/Visceksphere.ipynb` | `Vicsek model/vicsek_sphere_player.py` | `vicsek_sphere.html`, `vicsek_sphere.mp4` |
| Repulsive active particles (MIPS) | `MIPS/Mips.ipynb` | `MIPS/mips_player.py` | `mips.html`, `mips.mp4` |

The helper `.py` files contain the HTML/CSS/JavaScript templates and configuration builders. They are required to regenerate the interactive HTML. Edit these helpers rather than making lasting changes only to the generated `.html` files.

## Execution and saving

Python dependencies are `numpy`, `matplotlib`, `IPython`, and `imageio-ffmpeg`, with a working Jupyter kernel. The `imageio_ffmpeg` package supplies the FFmpeg executable used by `FFMpegWriter`.

1. Open the desired notebook and use its containing folder as the kernel's working directory. Imports of the adjacent helper and relative export paths depend on this.
2. Run the cells in order, preferably with **Restart Kernel and Run All** after changing initialization values. Some function defaults capture parameter values when their definition cells run.
3. The notebook computes position/velocity/time arrays and creates a Matplotlib `FuncAnimation`.
4. Its animation cell builds `player = animation.to_jshtml(...)` for inline playback with a time slider.
5. The final export cell calls the corresponding `make_*_player(...)` helper and writes a separate interactive HTML player using UTF-8.
6. The same export cell saves the Matplotlib animation as an MP4 through FFmpeg.

Exports use relative filenames and overwrite files of the same name in the kernel's working directory. If files appear in the project root unexpectedly, check `Path.cwd()` and run from the notebook folder.

HTML-builder calls currently used by the notebooks:

```python
make_ball_player(x, v, t, epsilon, dt)
make_lorentz_player(x, v, t, E, B, q, m)
make_tokamak_player(R_0, a, B_0, q_s, Q, m, E_params, x, v, t)
make_vicsek_player(N, L, v_0, R, eta, dt, n_steps, seed)
make_vicsek_3d_player(N_3d, L_3d, v_0_3d, R_3d, eta_3d, dt_3d, n_steps_3d, seed_3d)
make_mips_player(N, L, v_0, mu, A, kappa, D_r, dt, n_steps, seed)
```

Here `x` and `v` contain Cartesian vectors, usually with shape `(N, 3)`, and `t` contains their sample times.

### HTML versus MP4 versus inline notebook animation

These are distinct outputs:

- **Interactive HTML:** a self-contained page with JavaScript physics, a canvas plot, playback controls, and live parameter inputs. It opens directly in a browser, offline, without Python or a server. Open it in Chrome/Firefox rather than the VS Code text editor; refresh after regeneration.
- **MP4:** a fixed recording of the notebook's current Python simulation. Browser parameter changes do not modify or re-export this video.
- **Inline notebook player:** precomputed Matplotlib frames. It has playback/time controls, but does not acquire the live parameter controls of the separately exported HTML.

Editing browser inputs recalculates only that browser session. It does not write back into the notebook, helper, HTML file, or MP4. Reloading restores the configuration embedded at export time. To make different defaults permanent, change the notebook initialization and regenerate the exports.

The standalone players share a dark visual style, glowing particle/trails, play/pause/restart, and a time scrubber. Lorentz and tokamak players also support drag-to-rotate, scroll-to-zoom, and camera reset. Their templates are currently separate; keep shared behavior consistent when editing them.

## Bouncing-ball model

- Cartesian coordinates, upward `z`, fixed floor at `z = 0`, gravity `(0, 0, -m * 9.81)`, SI units.
- `floor_ball_collision(m, h, t, v_0=[0, 0, 0])` returns `x, v, t`. The current implementation uses notebook-global `dt` and `epsilon`.
- Free flight uses backward Euler: update velocity first, then position with the new velocity.
- A step that reaches/breaches the floor is projected to `z = 0`; downward vertical velocity is changed to `-epsilon * v_z`.
- The floor is frictionless: horizontal velocity continues through impacts and after vertical settling. A previous freeze of horizontal position during resting contact was corrected in both Python and JavaScript.
- Collision times/velocities are resolved at step boundaries, not with exact impact-event timing. Even `epsilon = 1` does not imply exact numerical energy conservation.

HTML controls: horizontal initial velocity `v_x`, vertical initial velocity `v_0`, and restitution `epsilon`. Starting height comes from the notebook. Positive `v_x` points right; positive vertical velocity points up. Changing a parameter restarts the trajectory.

## Uniform-field Lorentz model

The nonrelativistic equation is `m * dv/dt = q * (E + v × B)`, with constant, uniform vector fields and normalized units.

`lorentz_motion(q, m, v_0, E, B, *, x_0=..., dt=0.01, t_max=12)` returns `x, v, t`. It uses electric half-kicks around a Boris magnetic rotation and a trapezoidal position update. In a magnetic-only field, the velocity rotation preserves speed to roundoff. Electric work changes kinetic energy.

HTML controls expose all three components of `E`, `B`, and initial velocity, plus signed `q/m`. Zero `q/m` gives straight-line motion. The view automatically fits the new trajectory. Field arrows indicate direction rather than magnitude; they are not a spatial field-line visualization.

## Tokamak model and theory

This is a single test particle in a prescribed, axisymmetric field, with normalized units. It is not a self-consistent plasma or engineering tokamak equilibrium. Collisions, turbulence, radiation, and relativistic dynamics are not modeled.

Fields are expressed using cylindrical coordinates `(R, phi, Z)` around a circular toroidal vessel. `R_0` is the major radius, `a` the minor radius, and `q_s` the twist parameter, distinct from particle charge `Q`:

```text
B_phi = B_0 * R_0 / R
B_R   = -B_0 * Z / (q_s * R)
B_Z   = B_0 * (R - R_0) / (q_s * R)

E_phi = E_phi0 * R_0 / R * cos(omega * time + phase)
E_R   = -k_E * (R - R_0)
E_Z   = -k_E * Z
```

Both fields are converted to Cartesian vectors before advancing the particle. The model is singular at `R = 0`, outside a valid vessel with `R_0 > a > 0`.

The magnetic field is divergence-free and tangent to nested surfaces `(R - R_0)^2 + Z^2 = constant`. Its toroidal/poloidal components produce the field-line twist. `q_s` approximates the safety factor near the magnetic axis; it is not an exact global safety-factor profile.

Field lines staying on toroidal surfaces does not mean particles stay on those surfaces. Full particle trajectories include gyromotion and magnetic drifts and may reach the wall. No extra guiding-centre drift forces should be added to the full Lorentz solver.

The notebook's **“Motion of particle in tokamak”** markdown cell develops energy/work, gyromotion, pitch angle, Larmor radius, guiding-centre estimates, magnetic mirrors/trapping, electric and magnetic drifts, electric-field controls, the Boris update, and diagnostics. Keep that theory consistent with implementation. In particular, electric forcing is now implemented, not merely proposed.

### Particle advancement

`tokamak_motion(...)` evaluates fields at the position/time midpoint of a half-step drift, performs electric half-kicks around a Boris magnetic rotation, and finishes the drift. It returns `x, v, t, hit_wall`. It stops at the first sampled point with minor radius at least `a`; wall crossing is approximate to a time step.

The HTML implements the same update but can reduce its step to resolve the selected magnetic strength and `q/m`. It limits a run to 120,000 steps. For parity checks, compare Python and JavaScript using matching effective steps, initial states, and durations. Its velocity controls initialize parallel motion plus a minor-radial perpendicular component, matching the notebook's current initial-state construction.

### Live controls and dotted field lines

The HTML exposes:

- Magnetic `B_0`, twist `q_s`, and signed `Q/m`.
- Electric `E_phi0`, `k_E`, `omega`, and `phase`.
- Initial minor radius `r/a`, poloidal angle in degrees, `v_parallel`, and `v_perpendicular`.
- Vessel `R_0`, `a`, and simulation duration.

The display includes a 3D torus and an R–Z cross-section. Pink is the particle orbit; dotted cyan lines are magnetic; dotted gold lines are electric. Each field overlay has a visibility switch. Actual field lines are traced using normalized-field RK4, in both directions, with termination at the vessel boundary or tracing limit. Arrows indicate direction. Line spacing, thickness, and brightness currently do not encode strength.

- Changing `B_0` scales both magnetic components, so field-line geometry normally stays the same; particle motion still changes.
- Changing `q_s` changes the magnetic twist and visibly changes the lines.
- With `k_E = 0`, changing toroidal electric amplitude keeps circular electric-line geometry, unless the field vanishes; reversing sign reverses arrows.
- A radial electric component can change electric-line geometry.
- `B` is time-independent. `E` is time-independent when `omega = 0`. An oscillating drive uses electric-line snapshots during playback, refreshed at intervals of about 0.25 simulation time units and on scrubbing. The displayed snapshot time identifies the field being traced.

There is also a separate static field-line plotting cell before the notebook's particle animation. Its `field_time` selects the electric-field snapshot. This plot is separate from the dotted overlays in the standalone HTML.

## Vicsek model

Keep the existing filename `Vicsek model/Viscek.ipynb` (including its spelling). The user explicitly requested preservation of the original notation and update convention. Only theta was extended with neighbor alignment.

- Velocity has fixed magnitude: `v = v_0 * (cos(theta), sin(theta))`.
- Positions advance with the **current** velocity: `x[n+1] = (x[n] + dt * v[n]) % L`, not the newly aligned velocity.
- All headings update synchronously using old positions/headings. Neighbors include self and use minimum-image distances in the periodic box.
- Mean direction is `atan2(sum(sin(theta)), sum(cos(theta)))`; if the vector sum cancels, retain the old heading before adding noise.
- `eta` is the width of a uniform **angular-rate** perturbation. The random angular change is `uniform(-eta/2, eta/2) * dt`. Preserve this factor and its interpretation.
- `vicsek_model(...)` returns `x, v, theta, t`; vector histories have shape `(n_steps+1, N, 2)`.

The visualization uses colored heading arrows and plots heading alignment `abs(mean(exp(1j*theta)))`, between zero and one. The original 2-D visualization/export cells create inline Matplotlib playback and export `vicsek.html` and `vicsek.mp4` beside the notebook. Existing physics/initialization cells were preserved when adding these exports.

The standalone HTML has live controls for `N`, `L`, `v_0`, `R`, `eta`, `dt`, step count and random seed. The browser uses its own deterministic seeded generator; NumPy uses `default_rng`. A seed reproduces a run within each implementation, but identical numerical seeds do not imply identical Python/browser realizations. Compare the update rules with matching supplied initial states and random rates when testing parity. The browser limits work to keep parameter changes responsive.

### 2-D Vicsek KDE movie and phase scan

New cells between the original 2-D export and 3-D section add the same periodic Gaussian KDE velocity estimator as MIPS: normalized vector averaging, density masking, instantaneous or trailing-window time averages, inline slider/playback and `vicsek_kde.mp4`. The adjacent `vicsek_player.py` embeds its own independent KDE implementation and `vicsek.html` has a synchronized second canvas with width h/L, grid, trailing-window, density-floor and visibility controls. KDE settings redraw without changing trajectories. Browser velocities come directly from fixed speed and recorded theta; retain the current-velocity position convention.

The notebook phase scan uses the unchanged 2-D solver and independent `vicsek_phase_*` settings (64 particles, four densities, seven noise widths, 600 steps, three seeds). Its x-axis is actual angular noise width `eta*dt`, spanning 0 to 2*pi; eta remains an angular-rate width in the solver. It plots mean polarization `Phi=abs(mean(exp(i*theta)))` and per-run temporal fluctuations `N*Var(Phi)`, averaged over seeds after discarding the first half. Data include each seed's late-time order history and early/late means. These are finite-size order/disorder diagnostics, not density-clustering classifications or a proof of chaos or an exact transition boundary. Use longer runs, more particles and seeds to assess convergence. Reference: https://doi.org/10.1103/PhysRevLett.75.1226.

Outputs are `Vicsek model/vicsek_phase_map.png` and `vicsek_phase_scan.npz`. The original 2-D/3-D model, initialization, animation and export source cells are unchanged. The 3-D section and `vicsek_3d.html` do not acquire the 2-D KDE/scan; they retain their existing behavior.

### Long-run Vicsek HTML precomputation

All three Vicsek helpers/HTML exports (2-D, periodic 3-D and sphere) precompute trajectories asynchronously with a roughly 16 ms budget and a deterministic work cap per chunk (at most 250 steps or about 500,000 N²-step operations), with progress, disabled playback while calculating, and cancellation when inputs change. Limits match MIPS: 500 particles, 100,000 steps and one billion N²-step operations. Defaults are unchanged. This is precomputation, not a separate compilation stage.

The solvers use two rolling states for synchronous updates and retain at most about 2,001 sampled frames, always including the initial/final state. `sampleSteps` records actual integration-step indices; playback, alignment charts and 2-D KDE trailing windows use these times. Physics still advances every dt. `simulate(...)` remains a synchronous wrapper for small parity checks, while UI uses the yielding `simulationSteps(...)`. Sampling must not change RNG draws or update rules. Regression checks compare sampled frames with the original solver and Python, including sphere tangency and zero-speed limits. Notebook physics, saved inline players and MP4s are unaffected; regenerate only standalone HTML for helper changes.

### Appended 3-D Vicsek section

The same notebook has a separate 3-D section with `_3d` state/animation names. Preserve the user's two-angle velocity convention:

```text
v = v_0 * (cos(theta)*sin(phi), cos(theta)*cos(phi), sin(theta))
```

Theta is elevation; phi runs from +y toward +x. Do not swap the x/y sine and cosine. `vicsek_model_3d(...)` returns `x, v, theta, phi, t`: vector histories have shape `(n_steps+1, N, 3)`, and angle histories `(n_steps+1, N)`. `direction_3d` is derived from the angles for rendering/diagnostics.

**Current noise rule:** align neighbors' unit direction vectors, then sample uniformly in solid angle inside a cone about the mean. Its half-angle is `alpha = min(pi, eta * dt / 2)`. `add_direction_noise_3d(...)` samples `cos(beta)` uniformly in `[cos(alpha), 1]` and tangent-plane azimuth uniformly in `[0, 2*pi)`, constructing the new direction in an orthonormal local basis. Recover theta with `atan2(uz, hypot(ux, uy))` and phi with `atan2(ux, uy)` modulo 2*pi. At a vertical heading retain old phi; if neighboring directions cancel, use the old heading as cone axis. Zero noise gives alignment, and a cone reaching pi samples the full sphere.

The user first requested independent theta/phi noise, then explicitly requested this cone-based correction after discussing coordinate bias. Keep both angle histories and the exact velocity formula, but do not restore independent angle increments. Initial headings remain uniform on the sphere. Positions still advance with the **current** velocity, and neighbors/positions are periodic in a cube.

The notebook and standalone HTML implement this same cone rule. Matching random tapes for tests now contain two uniform `[0,1]` draws per particle (cosine and tangent azimuth), not angular-rate increments. The browser uses its own seeded generator, so parity tests supply shared initial theta/phi and random draws.

The separate exports are `vicsek_3d.html` and `vicsek_3d.mp4`; 2-D exports stay intact. The HTML has live model controls and drag/zoom/reset camera. Colors encode phi, while arrows show full 3-D direction. Rendered labels should describe uniform cone noise and theta/phi state.

### Vicsek inside a sphere

`Vicsek model/Visceksphere.ipynb` initializes particles uniformly in the ball volume and preserves the theta/phi heading convention and uniform-cone noise. Neighbors use Euclidean distances, without periodic images. `vicsek_sphere(...)` returns x, v, theta, phi, t. `v_0` is preferred propulsion speed; actual speed can decrease at the wall. Angles track actual velocity direction when moving; preserve the candidate heading when stopped.

The user corrected the original boundary implementation: wall response must act only on radial velocity and preserve the tangential vector exactly. In the wall layer, `radial_repulsion(position, velocity, a, width, strength, dt)` returns a purely radial velocity correction damping **outward** radial motion with exact exponential factor `exp(-strength*ramp*dt)`. It is zero for zero/inward radial velocity or zero ramp. At contact, `tangent_wall_velocity` subtracts the radial projection, enforcing v.n=0 for either radial sign. Do not renormalize speed, turn a tangential vector inward or invent a perpendicular fallback for purely radial motion. Vicsek's next alignment/propulsion update may set a new preferred velocity; the wall operator itself never increases tangential velocity. `apply_wall_response` combines damping and contact projection.

Positions advance with current actual v and are projected inside the ball. Strict tangency at every contact keeps contacted particles on the surface. Boundary-event timing remains approximate to dt. No particle–particle repulsion has been added. The local sphere notebook stores the actual Matplotlib HTML playback/slider output and an embedded MP4 output. Do not substitute a static PNG preview for these playable outputs after edits; regenerate and save the notebook outputs. Commit upload copies may still clear outputs under the repository convention. Inline 3-D animation uses actual velocity arrows, including zero-length glyphs for stopped particles; the final cell saves `vicsek_sphere.mp4`. Regenerate the video after physics changes. Existing other simulations and HTML players are unchanged; the sphere notebook now exports `vicsek_sphere.html` through the adjacent `vicsek_sphere_player.py` helper. The browser uses the same radial-only exponential damping, tangent projection and projected current-velocity position update. Controls expose sphere radius, N, preferred speed, neighbor radius, noise, dt, step count, seed, wall width and radial damping rate. It supports drag/zoom/reset and playback scrubbing. NumPy/browser seeded generators differ; compare using shared raw initial states and two uniform cone-noise draws per particle per step.

## MIPS / repulsive active particles

`MIPS/Mips.ipynb` keeps the original model cells, followed by visualization and export cells. `mips_model(...)` returns `x, v, theta, t`, with vector histories shaped `(n_steps+1, N, 2)`.

- Overdamped drift: `v = v_0 * (cos(theta), sin(theta)) + mu * force`.
- Pair potential: `U(r) = A * exp(-kappa*r) / r`, repulsive for nonnegative `A`. Forces use the nearest periodic image, not a full periodic lattice sum.
- Synchronous Euler positions: `x[n+1] = (x[n] + dt*v[n]) % L`.
- Brownian turning: `theta[n+1] = (theta[n] + sqrt(2*D_r*dt)*Z) % (2*pi)`, independent standard Gaussian `Z`. There is no alignment. This square-root time scaling differs from the Vicsek noise convention.
- Initialization uses a jittered grid without overlap; forces are singular at zero separation. Strong forces require a suitably small time step.

The visualization uses cosmetic arrows/colors for propulsion heading and a chart of mean **total drift speed**; arrows are not physical particle diameters or total velocity vectors. The short default run is not evidence of phase separation. Density, persistence, and duration determine whether it develops.

The last cells create inline playback with a slider and regenerate `mips.html` and `mips.mp4` in the `MIPS` working directory. HTML controls expose `N`, `L`, `v_0`, `mu`, `A`, `kappa`, `D_r`, `dt`, step count, and seed. The HTML export uses an exploratory clustering preset (`L=7`, `D_r=0.02`, `n_steps=100000`); notebook simulation defaults and MP4 stay independent. This does not guarantee clustering. The browser permits up to 100,000 steps and one billion N²-step operations, advances asynchronously in chunks, and stores at most about 2,001 snapshots for playback. The underlying time step is unchanged by snapshot sampling. It implements the same drift/turning rules, with pairwise antisymmetric forces. Its seeded generator differs from NumPy; identical seeds reproduce runs within each implementation, not identical Python/browser paths. Use shared initial states and Gaussian draws for trajectory comparisons.

### KDE velocity field and movie

The cell after visualization/export defines `periodic_kde_velocity(...)` and creates a separate animated field with inline play/pause/slider, exporting `MIPS/mips_kde.mp4` through the same FFmpeg workflow. It computes Gaussian-weighted vector averages `sum(K*v)/sum(K)` using wrapped periodic image sums (tails beyond at least eight bandwidths neglected). Returned density is mean number per area; average vectors before taking their magnitude. Input velocities are the actual total overdamped drift, not propulsion headings or differences of wrapped coordinates.

Notebook controls: `kde_bandwidth=0.06*L`, grid 32×32, `kde_window=0` for instantaneous spatial averaging; positive windows average at most seven equally weighted snapshots in a trailing interval. The movie samples at most 121 times and uses a fixed color/arrow scale across frames. Low-density vectors are masked; main trajectory and particle animation variables remain unchanged.

`mips.html` has a second, synchronized KDE canvas using the existing particle playback/time slider. Controls expose width h/L, grid size (12–48), trailing time window, density-floor fraction and visibility. Changes redraw KDE without rerunning the particle solver. The browser stores total drift vectors alongside sampled positions/headings, averages up to seven stored snapshots and caches at most 32 fields. Its displayed color/arrow scale is per frame and labeled. Python/browser use the same wrapped Gaussian normalization and vector averaging; temporal sampling depends on the retained frame grids. HTML configuration remains the longer exploratory preset; the KDE MP4 records the notebook run. Regenerate HTML using the helper/export cell, not the inline frame player.

### MIPS parameter scan (diagnostic version 2)

The notebook scans number density `N/L**2` against `D_r` using the existing Yukawa solver, with independent `phase_*` settings (64 particles, 3×3 points, two seeds, duration 30). The ABP drift, repulsive Yukawa derivative, synchronous Euler stepping and sqrt(2 D_r dt) noise are correct. This potential has no fixed disk diameter; do not apply published disk packing-fraction boundaries directly or silently replace it with WCA.

An earlier implementation classified phases using a 95th-percentile uniform-cloud score and a 50%-of-time vote. That classifier was ad hoc and was removed. Its all-dispersed map is not evidence of absence of MIPS. The revised maps show standard `S(k_min)` (mean of x/y wavevector structure factors, normalized so independent uniform points give one) and mean drift projected onto propulsion heading divided by `v_0` (undefined at zero propulsion), rather than assigning phases. The previous four-mode normalized contrast included diagonal modes at a different wavevector length.

Scan data retain per-seed early/late S values, projected motility and final snapshots. T*D_r is recorded; hatched cells have less than one persistence time. At the smallest D_r=0.005, T=30 spans only 0.15 persistence times. Absence of hatching is not a convergence check. Confirm duration, particle-number, seed and time-step convergence and inspect density distributions and snapshots before drawing phase boundaries. Nonclustered states are not automatically chaotic. Main arrays and HTML/video presets are unchanged.

Outputs: `MIPS/mips_phase_map.png` and `MIPS/mips_phase_scan.npz` (`diagnostic_version=2`); rerun scan/plot cells together to regenerate matching results. Sources: https://arxiv.org/abs/1201.4847 and https://arxiv.org/abs/1406.3533.

## Verification expectations

There is currently no committed automated test suite. Earlier checks used temporary scripts and headless Chrome. They covered:

- Browser/Python trajectory agreement, including positive, negative, and zero charge-to-mass ratios.
- Bouncing-ball free flight, restitution, nonpenetration, horizontal motion during resting contact, and independent velocity controls.
- Magnetic-only speed conservation; straight-line zero-force motion; constant-electric-field acceleration; electric work versus kinetic-energy change.
- Tokamak magnetic-field divergence, surface tangency, orbit step convergence, and wall-loss detection.
- Field-line tangency, zero-field handling, and static versus oscillating electric snapshots.
- Browser input changes, invalid inputs, time scrubbing, playback, restart, camera controls, and field visibility.
- MP4 decoding and HTML slider generation when those exports were introduced.

Run checks appropriate to the change. Changing a browser solver requires comparison with Python, not just a screenshot. For visual changes, inspect a real browser rendering. For a Markdown-only edit, rerendering all videos is unnecessary.

## GitHub and large-file handling

Repository: https://github.com/AnkanMan/Physics-I-can-see, branch `main`. The user initially said GitLab, then confirmed this GitHub destination.

GitHub publishing has used the connected GitHub tools because local Git metadata was unavailable in some sessions. Inspect the current branch head/tree, preserve unrelated files, use a normal branch update with the expected previous head, and verify uploaded blob hashes. Do not assume a previous commit also connected the local folder as a checkout.

Notebook execution can embed tens of megabytes of animation frames. Previous large uploads were interrupted when VS Code closed; memory pressure was suspected but not confirmed from crash evidence.

Established commit convention:

- Create upload copies of notebooks with code-cell `outputs = []` and `execution_count = None`.
- Preserve the user's local notebook outputs and all source/Markdown cells.
- Include the player helpers, standalone HTML, and requested MP4 artifacts.
- Exclude `__pycache__` and temporary debugging files.
- Prefer small transfers and reuse already uploaded blobs when retrying.
- Commit/push when requested; document changes do not by themselves authorize a new push.

Interactive HTML is now lightweight canvas/JavaScript rather than a large collection of embedded Matplotlib frames. Do not replace it with the old frame-only `player` on export, or the live parameter controls will disappear.
