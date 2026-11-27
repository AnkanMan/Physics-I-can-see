# Physics I can see — project context and maintenance notes

This document is a handoff for future AI assistants and maintainers. Read it before changing the simulations. It records the implementation as of 27 November 2026; inspect the files for the latest parameter values.

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
```

Here `x` and `v` contain Cartesian vectors, usually with shape `(N, 3)`, and `t` contains their sample times.

### HTML versus MP4 versus inline notebook animation

These are distinct outputs:

- **Interactive HTML:** a self-contained page with JavaScript physics, a canvas plot, playback controls, and live parameter inputs. It opens directly in a browser, offline, without Python or a server. Open it in Chrome/Firefox rather than the VS Code text editor; refresh after regeneration.
- **MP4:** a fixed recording of the notebook's current Python simulation. Browser parameter changes do not modify or re-export this video.
- **Inline notebook player:** precomputed Matplotlib frames. It has playback/time controls, but does not acquire the live parameter controls of the separately exported HTML.

Editing browser inputs recalculates only that browser session. It does not write back into the notebook, helper, HTML file, or MP4. Reloading restores the configuration embedded at export time. To make different defaults permanent, change the notebook initialization and regenerate the exports.

The four standalone players share a dark visual style, glowing particle/trails, play/pause/restart, and a time scrubber. Lorentz and tokamak players also support drag-to-rotate, scroll-to-zoom, and camera reset. Their templates are currently separate; keep shared behavior consistent when editing them.

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

The visualization uses colored heading arrows and plots heading alignment `abs(mean(exp(1j*theta)))`, between zero and one. The last two notebook cells create inline Matplotlib playback and export `vicsek.html` and `vicsek.mp4` beside the notebook. Existing physics/initialization cells were preserved when adding these exports.

The standalone HTML has live controls for `N`, `L`, `v_0`, `R`, `eta`, `dt`, step count and random seed. The browser uses its own deterministic seeded generator; NumPy uses `default_rng`. A seed reproduces a run within each implementation, but identical numerical seeds do not imply identical Python/browser realizations. Compare the update rules with matching supplied initial states and random rates when testing parity. The browser limits work to keep parameter changes responsive.

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
