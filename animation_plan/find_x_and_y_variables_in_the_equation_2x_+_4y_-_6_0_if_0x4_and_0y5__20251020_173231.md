# 1. 🎞️ Step-by-step animation plan

**Scene Setup:**
*   **0:00 - 0:05:** Scene opens to a clean, well-lit 3D coordinate grid. X and Y axes are prominently labeled. The grid extends slightly beyond `x=4` and `y=5`.
*   The initial problem `2x + 4y - 6 = 0` appears centered on a floating EquationPlane.
*   Text overlay: "Problem: Find x and y where 0 < x < 4 and 0 < y < 5"

---

**Step 1: Simplify the given equation**
*   **0:05 - 0:15:** The equation `2x + 4y - 6 = 0` is central.
*   A glowing "Divide by 2" OperationArrow appears and sweeps across the entire equation.
*   The coefficients `2`, `4`, and `6` on the EquationPlane visually shrink and divide by `2` to become `1`, `2`, and `3`. The entire equation rearranges smoothly.
*   **0:15 - 0:20:** The simplified equation `x + 2y - 3 = 0` is now prominently displayed. Text overlay: "Step 1: Simplify the equation".

---

**Step 2: Express one variable in terms of the other**
*   **0:20 - 0:25:** The simplified equation `x + 2y - 3 = 0` is shown. Text overlay: "Step 2: Isolate variables".

    **A. Isolate x:**
    *   **0:25 - 0:35:** `x + 2y - 3 = 0` slides to the left.
    *   The `+2y` term detaches, slides to the right side of the EqualsBar, and flips its sign to become `-2y`.
    *   The `-3` term detaches, slides to the right side, and flips its sign to become `+3`.
    *   The EquationPlane updates: `x = 3 - 2y` appears on the right.
    *   **0:35 - 0:40:** `x = 3 - 2y` is highlighted briefly.

    **B. Isolate y:**
    *   **0:40 - 0:50:** The original `x + 2y - 3 = 0` (or it reappears if it faded) slides to the left again.
    *   The `x` term detaches, slides right, becomes `-x`.
    *   The `-3` term detaches, slides right, becomes `+3`.
    *   The EquationPlane updates: `2y = 3 - x`.
    *   **0:50 - 1:00:** A "Divide by 2" OperationArrow sweeps over `2y = 3 - x`. The `2` in `2y` vanishes, and the entire right side `(3 - x)` is enclosed in parentheses and a `/2` appears.
    *   The EquationPlane updates: `y = (3 - x) / 2`.
    *   **1:00 - 1:05:** `y = (3 - x) / 2` is highlighted briefly.

---

**Step 3: Apply the constraints to find the valid ranges for x and y**
*   **1:05 - 1:15:** The initial constraints `0 < x < 4` and `0 < y < 5` appear.
*   On the 3D grid, the region defined by these constraints is visually highlighted. A transparent, glowing rectangular region (ConstraintHighlight) on the XY plane forms, extending from `x=0` to `x=4` and `y=0` to `y=5`. Open circles (Point Markers) at `(0,0)`, `(4,0)`, `(0,5)`, `(4,5)` indicate strict inequalities.
*   Text overlay: "Step 3: Apply initial constraints to define a search region."

    **A. Determine the valid range for y:**
    *   **1:15 - 1:20:** The equation `x = 3 - 2y` is shown again.
    *   Text overlay: "Using 0 < x < 4 with x = 3 - 2y"
    *   **1:20 - 1:25:** The `x` in `0 < x < 4` is replaced by `(3 - 2y)`, forming `0 < 3 - 2y < 4`.
    *   **1:25 - 1:35:** Animation of solving `0 < 3 - 2y < 4`:
        *   `+2y` operation is shown, leading to `2y < 3`.
        *   `/2` operation is shown, leading to `y < 3/2`.
    *   **1:35 - 1:45:** Animation of solving `3 - 2y < 4`:
        *   `-3` operation is shown, leading to `-2y < 1`.
        *   `/-2` operation (with a subtle visual cue of the inequality sign flipping), leading to `y > -1/2`.
    *   **1:45 - 1:50:** Both results combine: `-1/2 < y < 3/2` is displayed.
    *   **1:50 - 2:00:** On the Y-axis, a new ConstraintHighlight appears for `-1/2 < y < 3/2`. The existing `0 < y < 5` highlight remains. The intersection (`0 < y < 3/2`) is then highlighted with a stronger glow, and the `-1/2 < y < 0` and `3/2 < y < 5` parts fade out.
    *   **2:00 - 2:05:** Final valid range for `y`: `0 < y < 3/2` is displayed.

    **B. Determine the valid range for x:**
    *   **2:05 - 2:10:** The equation `y = (3 - x) / 2` is shown again.
    *   Text overlay: "Using 0 < y < 5 with y = (3 - x) / 2"
    *   **2:10 - 2:15:** The `y` in `0 < y < 5` is replaced by `(3 - x) / 2`, forming `0 < (3 - x) / 2 < 5`.
    *   **2:15 - 2:25:** Animation of solving `0 < (3 - x) / 2 < 5`:
        *   `*2` operation is shown, leading to `0 < 3 - x < 10`.
    *   **2:25 - 2:35:** Animation of solving `0 < 3 - x`:
        *   `+x` operation is shown, leading to `x < 3`.
    *   **2:35 - 2:45:** Animation of solving `3 - x < 10`:
        *   `-3` operation is shown, leading to `-x < 7`.
        *   `*-1` operation (with inequality sign flip), leading to `x > -7`.
    *   **2:45 - 2:50:** Both results combine: `-7 < x < 3` is displayed.
    *   **2:50 - 3:00:** On the X-axis, a new ConstraintHighlight appears for `-7 < x < 3`. The existing `0 < x < 4` highlight remains. The intersection (`0 < x < 3`) is then highlighted with a stronger glow, and the `-7 < x < 0` and `3 < x < 4` parts fade out.
    *   **3:00 - 3:05:** Final valid range for `x`: `0 < x < 3` is displayed.

---

**Step 4: Final Solution Visualization**
*   **3:05 - 3:15:** The `3D Grid` fades to show only the `X` and `Y` axes.
*   The final constraint ranges (`0 < x < 3` and `0 < y < 3/2`) are re-highlighted on their respective axes.
*   The transparent rectangular ConstraintHighlight from `(0,0)` to `(3, 3/2)` forms on the grid.
*   **3:15 - 3:25:** The simplified equation `x + 2y - 3 = 0` (or `2x + 4y - 6 = 0`) reappears.
*   A thick, glowing `SolutionLine` begins to draw itself across the 3D grid, representing the line `x + 2y - 3 = 0`.
*   As the `SolutionLine` enters the `(0, 3/2)` to `(3, 0)` region of the previously highlighted rectangle, it glows even brighter. The portions of the infinite line outside this region fade out or become transparent.
*   **3:25 - 3:35:** The `SolutionLine` is now a vibrant segment, connecting the theoretical points `(0, 3/2)` and `(3, 0)`.
*   At these theoretical endpoints, small, hollow Point Markers (glowing rings) appear, signifying that these exact points are *not included* in the solution (due to strict inequalities).
*   **3:35 - 3:50:** Introduce `VariableBall(x)` and `VariableBall(y)`.
    *   `VariableBall(x)` (red) rolls along the X-axis, from `x` just above `0` towards `3` (not reaching `3`).
    *   `VariableBall(y)` (blue) simultaneously rolls along the Y-axis, its position dynamically linked to `VariableBall(x)` by the equation `y = (3 - x) / 2`.
    *   A transparent "rod" or "beam" connects `VariableBall(x)` and `VariableBall(y)` to a point on the `SolutionLine`. As the balls move within their valid ranges, the connecting point slides along the `SolutionLine` segment.
    *   This shows the interactive relationship: as `x` changes, `y` changes to satisfy the equation, and both stay within their bounds.
*   **3:50 - 4:00:** Text overlay: "Final Solution: The set of (x, y) pairs on this line segment, where 0 < x < 3 and 0 < y < 3/2."
*   The camera slowly rotates around the final visualization, highlighting the line segment, the valid ranges on the axes, and the linked variable balls. Fade to black.

---

# 2. 🧱 Asset suggestions

*   **3D Grid:** A customizable grid plane with major axes (X, Y) clearly distinguishable (e.g., thicker lines, distinct colors like red for X, green for Y). Values (0, 1, 2, 3...) marked along the axes. Could have a subtle texture like graph paper.
*   **VariableBall(x), VariableBall(y):**
    *   `VariableBall(x)`: A glossy, semi-transparent red sphere with a glowing internal core. A stylized 'x' (or `x` in a distinct math font) floats above it.
    *   `VariableBall(y)`: A glossy, semi-transparent blue sphere with a glowing internal core. A stylized 'y' floats above it.
*   **EquationPlane:** A semi-transparent rectangular glass or frosted acrylic panel that floats in the air. Text (equations, operators) appears on its surface with a glow effect. Can slide in, out, and reposition.
*   **NumberBlock:** Simple 3D blocks (cubes or rounded rectangles) with numbers (2, 4, 6, 0, 3, 1, etc.) on their faces. They can detach from the EquationPlane, move, and disappear/reappear.
*   **OperationArrow:** A dynamic, glowing arrow with an operation symbol (e.g., `÷2`, `+3`, `-2y`, `*2`, `-1`). It animates its path to indicate the algebraic operation being performed. Can change color based on operation type (e.g., green for addition/multiplication, red for subtraction/division).
*   **EqualsBar:** A glowing, stylized '=' sign that can animate its position and length to accommodate equation changes.
*   **ConstraintHighlight (Axis):** A glowing line segment that overlays portions of the X and Y axes to show valid ranges. Distinct color (e.g., bright yellow).
*   **ConstraintHighlight (Region):** A transparent, glowing rectangular plane that defines the 2D solution space on the grid. Could have a subtle pulsating glow.
*   **SolutionLine:** A thick, vibrant, pulsating line that draws itself along the final solution path. It should stand out clearly.
*   **Point Markers:** Small, hollow, glowing rings or open spheres used to denote points on axes or endpoints of a line segment that are *not included* (strict inequalities).
*   **Connecting Rod/Beam:** A subtle, transparent, ethereal beam or line that connects the VariableBalls to the SolutionLine, illustrating their coupled movement.
*   **Background elements:** Optional subtle classroom elements like a floating chalkboard (for text overlays), or simply a soft gradient skybox.

---

# 3. ⏱️ Timing and transitions

*   **Overall Pace:** Moderate to slow, allowing time for comprehension of each algebraic step and its visual representation. Each key operation should have a distinct, observable animation.
*   **Algebraic Operations:** Quick, snappy transitions.
    *   **NumberBlock movement:** 0.5-1 second for a number or term to detach, slide, and reposition/change sign.
    *   **OperationArrow sweep:** 0.75 seconds for the arrow to appear, sweep, and trigger the change.
    *   **Text/Equation Updates:** 0.2-0.5 seconds for text to update or morph.
*   **Visualizations (Highlights, Grids):** Smooth fade in/out transitions.
    *   **Highlight appearance/disappearance:** 1-1.5 seconds fade duration.
    *   **Grid/Plane fade:** 1.5-2 seconds for overall scene changes.
*   **Camera Movement:** Slow, deliberate pans and rotations to keep the focus on the current action. Smooth easing in/out for all camera movements.
    *   A slight zoom in/out for emphasis at key moments.
*   **VariableBall Interaction:** The movement of `VariableBall(x)` and `VariableBall(y)` should be fluid and interactive, taking about 10-15 seconds to demonstrate the range of motion along the `SolutionLine`.
*   **Pauses:** Introduce 2-3 second pauses after major results are displayed (e.g., `x = 3 - 2y`, `0 < y < 3/2`, `Final Solution`) to allow students to process the information.
*   **Transitions between steps:** Smooth wipes or fades between the main problem-solving phases (Simplify, Isolate, Constrain, Visualize).
*   **Emphasis:** Use short, sharp glows or pulses on specific numbers, terms, or parts of the grid to draw attention.

This structure ensures a logical flow, visually intuitive explanations for algebraic operations, and an interactive climax that ties the abstract problem to a concrete geometric representation.