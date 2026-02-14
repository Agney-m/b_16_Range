   # ============================================================================
# FILE 5: solver.py
# ============================================================================
# solver.py - Backtracking + greedy heuristics solver for Range puzzle

class GreedySolver:
    """
    Uses DFS backtracking with constraint propagation:
    - Clue bounds (min/max visible whites) prune early
    - No adjacent blacks
    - Final connectivity check for white cells
    """
    def __init__(self, graph):
        self.graph = graph
        self.forced_white = set()  # cells assigned as white
        self.unknown = set()       # undecided cells

    # Public API ---------------------------------------------------------
    def solve(self):
        self.graph.reset()
        self.forced_white.clear()
        self.unknown.clear()

        # Initialize sets
        for cell in self.graph.all_cells():
            if cell.value is not None:  # clues are always white
                self.forced_white.add(cell)
            else:
                self.unknown.add(cell)

        return self._backtrack()

    def make_ai_move(self):
        """AI move: make a single greedy move without resetting the grid"""
        # Don't reset - work with current state
        # Find best cell to toggle using greedy heuristic
        best_cell = None
        best_improvement = -999
        
        for cell in self.graph.all_cells():
            if cell.value is not None:  # Skip clue cells
                continue
            if cell.is_dot:  # Skip cells marked as definitely not black
                continue
            
            # Try toggling this cell
            was_black = cell.is_black
            cell.is_black = not cell.is_black
            
            # Evaluate improvement
            improvement = self._evaluate_improvement()
            
            if improvement > best_improvement:
                best_improvement = improvement
                best_cell = cell
            
            # Restore
            cell.is_black = was_black
        
        # Make the best move
        if best_cell and best_improvement > -50:  # Only if it's actually helpful
            best_cell.is_black = not best_cell.is_black
            return True
        return False
    
    def _evaluate_improvement(self):
        """Evaluate how much the current state improves toward solution"""
        score = 0
        
        # Reward: clues closer to target
        for clue in self.graph.get_clue_cells():
            visible = self.graph.count_visible_whites(clue)
            diff = abs(visible - clue.value)
            score -= diff * 10  # Penalty for being wrong
        
        # Heavy penalties for violations
        if self.graph.has_adjacent_blacks():
            score -= 1000
        if not self.graph.is_white_connected():
            score -= 1000
        
        return score

    # Backtracking core --------------------------------------------------
    def _backtrack(self):
        # Early pruning: clue bounds + adjacent black rule
        if not self._bounds_ok():
            return False
        if self.graph.has_adjacent_blacks():
            return False

        # If no unknowns, validate full solution
        if not self.unknown:
            return (self.graph.is_white_connected() and
                    self._all_clues_exact())

        # Select next cell (heuristic: first unknown)
        cell = self._select_cell()

        # Try black then white (black is more restrictive -> good for pruning)
        for choice in (True, False):
            prev_black = cell.is_black
            prev_forced = cell in self.forced_white
            self.unknown.discard(cell)

            if choice:
                cell.is_black = True
                if prev_forced:
                    self.forced_white.discard(cell)
            else:
                cell.is_black = False
                self.forced_white.add(cell)

            if self._backtrack():
                return True

            # revert
            cell.is_black = prev_black
            if prev_forced:
                self.forced_white.add(cell)
            else:
                self.forced_white.discard(cell)

            self.unknown.add(cell)

        return False

    # Helpers ------------------------------------------------------------
    def _select_cell(self):
        # Heuristic: pick the unknown cell nearest to any clue (manhattan)
        clue_cells = self.graph.get_clue_cells()
        best = None
        best_dist = 1e9
        for cell in self.unknown:
            for clue in clue_cells:
                dist = abs(cell.row - clue.row) + abs(cell.col - clue.col)
                if dist < best_dist:
                    best_dist = dist
                    best = cell
        return best or next(iter(self.unknown))

    def _bounds_ok(self):
        """Check every clue's min/max visibility bounds."""
        for clue in self.graph.get_clue_cells():
            min_v, max_v = self._clue_bounds(clue)
            if clue.value < min_v or clue.value > max_v:
                return False
        return True

    def _clue_bounds(self, clue):
        """Return (min_visible, max_visible) for a clue given current partial state."""
        min_v = 1  # counts the clue itself
        max_v = 1
        dirs = [(-1,0),(1,0),(0,-1),(0,1)]

        def is_known_white(cell):
            return (cell.value is not None) or (cell in self.forced_white)

        for dr, dc in dirs:
            r, c = clue.row + dr, clue.col + dc

            # max: treat unknown as white until black or edge
            while 0 <= r < self.graph.size and 0 <= c < self.graph.size:
                cell = self.graph.grid[r][c]
                if cell.is_black:
                    break
                max_v += 1
                r += dr
                c += dc

            # min: traverse again but stop at first unknown/black
            r, c = clue.row + dr, clue.col + dc
            while 0 <= r < self.graph.size and 0 <= c < self.graph.size:
                cell = self.graph.grid[r][c]
                if cell.is_black:
                    break
                if is_known_white(cell):
                    min_v += 1
                    r += dr
                    c += dc
                    continue
                # unknown could be black -> stop min here
                break

        return min_v, max_v

    def _all_clues_exact(self):
        for clue in self.graph.get_clue_cells():
            if self.graph.count_visible_whites(clue) != clue.value:
                return False
        return True


# ============================================================================
# Divide and Conquer Solver
# ============================================================================
class DivideConquerSolver:
    """
    Divide and Conquer approach:
    - Divides the grid spatially into quadrants/regions
    - Solves each region independently using recursive subdivision
    - Merges solutions while ensuring constraints are satisfied
    - True divide-and-conquer: Divide -> Conquer -> Combine
    """
    def __init__(self, graph):
        self.graph = graph
        self.forced_white = set()
        self.unknown = set()

    def solve(self):
        """Solve using divide and conquer strategy"""
        self.graph.reset()
        self.forced_white.clear()
        self.unknown.clear()

        # Initialize sets
        for cell in self.graph.all_cells():
            if cell.value is not None:
                self.forced_white.add(cell)
            else:
                self.unknown.add(cell)

        # True Divide and Conquer: Divide grid spatially into regions
        # Start with entire grid as one region
        return self._divide_and_conquer(0, 0, self.graph.size, self.graph.size)
    
    def _divide_and_conquer(self, min_row, min_col, max_row, max_col):
        """
        Divide and Conquer recursive function:
        - Divide: Split region into quadrants
        - Conquer: Solve base case (small region) or recurse
        - Combine: Merge solutions from sub-regions
        """
        # Base case: If region is small enough, solve directly
        region_size = (max_row - min_row) * (max_col - min_col)
        if region_size <= 16:  # Small region: solve directly
            return self._solve_region_directly(min_row, min_col, max_row, max_col)
        
        # Divide: Split into quadrants
        mid_row = (min_row + max_row) // 2
        mid_col = (min_col + max_col) // 2
        
        # Get cells in boundary (needed for merging)
        boundary_cells = self._get_boundary_cells(min_row, min_col, max_row, max_col, mid_row, mid_col)
        
        # Conquer: Solve each quadrant recursively
        quadrants = [
            (min_row, min_col, mid_row, mid_col),  # Top-left
            (min_row, mid_col, mid_row, max_col),  # Top-right
            (mid_row, min_col, max_row, mid_col),  # Bottom-left
            (mid_row, mid_col, max_row, max_col)   # Bottom-right
        ]
        
        # Try solving each quadrant
        for q_min_r, q_min_c, q_max_r, q_max_c in quadrants:
            if not self._divide_and_conquer(q_min_r, q_min_c, q_max_r, q_max_c):
                return False
        
        # Combine: Merge solutions and validate constraints
        return self._merge_regions(boundary_cells)
    
    def _solve_region_directly(self, min_row, min_col, max_row, max_col):
        """Solve a small region directly using backtracking"""
        # Get cells in this region that are unknown
        region_cells = []
        for r in range(min_row, max_row):
            for c in range(min_col, max_col):
                cell = self.graph.grid[r][c]
                if cell.value is None and cell in self.unknown:
                    region_cells.append(cell)
        
        # Solve this region
        return self._solve_cell_list(region_cells, 0)
    
    def _solve_cell_list(self, cells, index):
        """Backtrack through a list of cells"""
        if index >= len(cells):
            # Check if constraints are satisfied for this region
            return self._bounds_ok() and not self.graph.has_adjacent_blacks()
        
        cell = cells[index]
        if cell not in self.unknown:
            return self._solve_cell_list(cells, index + 1)
        
        self.unknown.discard(cell)
        
        # Try black then white
        for choice in (True, False):
            prev_black = cell.is_black
            prev_forced = cell in self.forced_white
            
            if choice:
                cell.is_black = True
                if prev_forced:
                    self.forced_white.discard(cell)
            else:
                cell.is_black = False
                self.forced_white.add(cell)
            
            if not self.graph.has_adjacent_blacks():
                if self._solve_cell_list(cells, index + 1):
                    return True
            
            # Revert
            cell.is_black = prev_black
            if prev_forced:
                self.forced_white.add(cell)
            else:
                self.forced_white.discard(cell)
        
        self.unknown.add(cell)
        return False
    
    def _get_boundary_cells(self, min_row, min_col, max_row, max_col, mid_row, mid_col):
        """Get cells on the boundary between quadrants"""
        boundary = set()
        # Vertical boundary
        for r in range(min_row, max_row):
            if mid_col > 0:
                boundary.add(self.graph.grid[r][mid_col - 1])
            if mid_col < self.graph.size:
                boundary.add(self.graph.grid[r][mid_col])
        # Horizontal boundary
        for c in range(min_col, max_col):
            if mid_row > 0:
                boundary.add(self.graph.grid[mid_row - 1][c])
            if mid_row < self.graph.size:
                boundary.add(self.graph.grid[mid_row][c])
        return boundary
    
    def _merge_regions(self, boundary_cells):
        """Merge solutions from sub-regions, ensuring constraints"""
        # After merging, validate that boundary constraints are satisfied
        # Check adjacent blacks across boundaries
        if self.graph.has_adjacent_blacks():
            return False
        
        # If all regions solved, validate complete solution
        if not self.unknown:
            return (self.graph.is_white_connected() and
                    self._all_clues_exact())
        
        # Still have unknowns, continue with remaining cells
        return self._backtrack_remaining()

    def _backtrack_remaining(self):
        """Backtrack through remaining unknown cells"""
        if not self.unknown:
            return (self.graph.is_white_connected() and
                    self._all_clues_exact())
        
        if not self._bounds_ok() or self.graph.has_adjacent_blacks():
            return False
        
        cell = self._select_cell()
        
        for choice in (True, False):
            prev_black = cell.is_black
            prev_forced = cell in self.forced_white
            self.unknown.discard(cell)
            
            if choice:
                cell.is_black = True
                if prev_forced:
                    self.forced_white.discard(cell)
            else:
                cell.is_black = False
                self.forced_white.add(cell)
            
            if self._backtrack_remaining():
                return True
            
            # Revert
            cell.is_black = prev_black
            if prev_forced:
                self.forced_white.add(cell)
            else:
                self.forced_white.discard(cell)
            
            self.unknown.add(cell)
        
        return False
    
    def _select_cell(self):
        """Select next cell (same as GreedySolver)"""
        clue_cells = self.graph.get_clue_cells()
        best = None
        best_dist = 1e9
        for cell in self.unknown:
            for clue in clue_cells:
                dist = abs(cell.row - clue.row) + abs(cell.col - clue.col)
                if dist < best_dist:
                    best_dist = dist
                    best = cell
        return best or next(iter(self.unknown))
    
    def _all_clues_exact(self):
        """Check if all clues are exactly satisfied"""
        for clue in self.graph.get_clue_cells():
            if self.graph.count_visible_whites(clue) != clue.value:
                return False
        return True


    def _bounds_ok(self):
        """Check every clue's min/max visibility bounds (same as GreedySolver)"""
        for clue in self.graph.get_clue_cells():
            min_v, max_v = self._clue_bounds(clue)
            if clue.value < min_v or clue.value > max_v:
                return False
        return True

    def _clue_bounds(self, clue):
        """Return (min_visible, max_visible) for a clue (same as GreedySolver)"""
        min_v = 1
        max_v = 1
        dirs = [(-1,0),(1,0),(0,-1),(0,1)]

        def is_known_white(cell):
            return (cell.value is not None) or (cell in self.forced_white)

        for dr, dc in dirs:
            r, c = clue.row + dr, clue.col + dc

            while 0 <= r < self.graph.size and 0 <= c < self.graph.size:
                cell = self.graph.grid[r][c]
                if cell.is_black:
                    break
                max_v += 1
                r += dr
                c += dc

            r, c = clue.row + dr, clue.col + dc
            while 0 <= r < self.graph.size and 0 <= c < self.graph.size:
                cell = self.graph.grid[r][c]
                if cell.is_black:
                    break
                if is_known_white(cell):
                    min_v += 1
                    r += dr
                    c += dc
                    continue
                break

        return min_v, max_v

    def make_ai_move(self):
        """AI move using divide and conquer heuristic"""
        # Use greedy approach for single moves
        best_cell = None
        best_improvement = -999

        for cell in self.graph.all_cells():
            if cell.value is not None or cell.is_dot:
                continue

            was_black = cell.is_black
            cell.is_black = not cell.is_black

            improvement = self._evaluate_improvement()
            if improvement > best_improvement:
                best_improvement = improvement
                best_cell = cell

            cell.is_black = was_black

        if best_cell and best_improvement > -50:
            best_cell.is_black = not best_cell.is_black
            return True
        return False

    def _evaluate_improvement(self):
        """Evaluate improvement (same as GreedySolver)"""
        score = 0
        for clue in self.graph.get_clue_cells():
            visible = self.graph.count_visible_whites(clue)
            diff = abs(visible - clue.value)
            score -= diff * 10
        if self.graph.has_adjacent_blacks():
            score -= 1000
        if not self.graph.is_white_connected():
            score -= 1000
        return score


# ============================================================================
# Dynamic Programming Solver
# ============================================================================
class DynamicProgrammingSolver:
    """
    Dynamic Programming approach:
    - Uses memoization to cache sub-problem solutions
    - Builds solutions from smaller sub-problems (bottom-up approach)
    - Avoids redundant computations through optimal substructure
    - Uses compact state representation for efficient caching
    """
    def __init__(self, graph):
        self.graph = graph
        self.memo = {}  # Memoization cache: state -> bool
        self.forced_white = set()
        self.unknown = set()
        self.cell_order = []  # Order cells for DP processing

    def solve(self):
        """Solve using dynamic programming with memoization"""
        self.graph.reset()
        self.memo.clear()
        self.forced_white.clear()
        self.unknown.clear()
        self.cell_order = []

        # Initialize sets
        for cell in self.graph.all_cells():
            if cell.value is not None:
                self.forced_white.add(cell)
            else:
                self.unknown.add(cell)
        
        # Order cells for DP: process cells near clues first (optimal substructure)
        self._compute_cell_order()

        # Convert to state representation and solve
        state = self._get_state()
        return self._dp_solve(state, 0)

    def _compute_cell_order(self):
        """Compute optimal order for processing cells (closest to clues first)"""
        clue_cells = self.graph.get_clue_cells()
        unknown_list = list(self.unknown)
        
        # Sort by distance to nearest clue
        def distance_to_nearest_clue(cell):
            min_dist = float('inf')
            for clue in clue_cells:
                dist = abs(cell.row - clue.row) + abs(cell.col - clue.col)
                min_dist = min(min_dist, dist)
            return min_dist
        
        unknown_list.sort(key=distance_to_nearest_clue)
        self.cell_order = unknown_list

    def _get_state(self):
        """Get a hashable representation of current state (compact bitmask-like)"""
        # Use a more compact representation: only store decisions for cells
        # in the order they'll be processed
        state_list = []
        for cell in self.cell_order:
            # 0 = undecided/unknown, 1 = black, 2 = white
            if cell.is_black:
                state_list.append(1)
            elif cell in self.forced_white or cell.value is not None:
                state_list.append(2)
            else:
                state_list.append(0)  # Undecided
        return tuple(state_list)

    def _dp_solve(self, state, cell_index):
        """
        Solve using dynamic programming with memoization
        - Optimal substructure: solution depends on sub-problems
        - Overlapping subproblems: memoization avoids recomputation
        """
        # Check memoization cache
        if state in self.memo:
            return self.memo[state]

        # Base case: if all cells are decided, validate solution
        if cell_index >= len(self.cell_order):
            result = self._validate_solution()
            self.memo[state] = result
            return result

        # Check constraints early (pruning)
        if not self._bounds_ok() or self.graph.has_adjacent_blacks():
            self.memo[state] = False
            return False

        # Get next cell to process
        next_cell = self.cell_order[cell_index]
        
        # Skip if already decided (clue cell or already processed)
        if next_cell.value is not None:
            return self._dp_solve(state, cell_index + 1)
        
        # Check current state of this cell from state tuple
        cell_state = state[cell_index] if cell_index < len(state) else 0
        
        # If already decided in this state (not undecided), move to next
        if cell_state != 0:
            # Update actual cell state to match state tuple
            if cell_state == 1:
                next_cell.is_black = True
                self.unknown.discard(next_cell)
            elif cell_state == 2:
                next_cell.is_black = False
                self.forced_white.add(next_cell)
                self.unknown.discard(next_cell)
            return self._dp_solve(state, cell_index + 1)

        # Try both choices (black and white) for this cell
        success = False
        self.unknown.discard(next_cell)

        # Try making it black (if valid)
        if self._can_be_black(next_cell):
            prev_black = next_cell.is_black
            prev_forced = next_cell in self.forced_white
            next_cell.is_black = True
            if prev_forced:
                self.forced_white.discard(next_cell)
            
            new_state = self._get_state()
            if self._dp_solve(new_state, cell_index + 1):
                success = True
            else:
                # Revert
                next_cell.is_black = prev_black
                if prev_forced:
                    self.forced_white.add(next_cell)

        # Try making it white if black didn't work
        if not success:
            prev_black = next_cell.is_black
            prev_forced = next_cell in self.forced_white
            next_cell.is_black = False
            self.forced_white.add(next_cell)
            
            new_state = self._get_state()
            if self._dp_solve(new_state, cell_index + 1):
                success = True
            else:
                # Revert
                next_cell.is_black = prev_black
                if prev_forced:
                    self.forced_white.add(next_cell)
                else:
                    self.forced_white.discard(next_cell)
        
        self.unknown.add(next_cell)

        self.memo[state] = success
        return success

    def _can_be_black(self, cell):
        """Check if a cell can be black without violating constraints"""
        # Check if neighbors are already black
        for neighbor in self.graph.neighbors(cell):
            if neighbor.is_black:
                return False
        return True

    def _validate_solution(self):
        """Validate complete solution"""
        if self.graph.has_adjacent_blacks():
            return False
        if not self.graph.is_white_connected():
            return False
        for clue in self.graph.get_clue_cells():
            if self.graph.count_visible_whites(clue) != clue.value:
                return False
        return True

    def _bounds_ok(self):
        """Check every clue's min/max visibility bounds"""
        for clue in self.graph.get_clue_cells():
            min_v, max_v = self._clue_bounds(clue)
            if clue.value < min_v or clue.value > max_v:
                return False
        return True

    def _clue_bounds(self, clue):
        """Return (min_visible, max_visible) for a clue"""
        min_v = 1
        max_v = 1
        dirs = [(-1,0),(1,0),(0,-1),(0,1)]

        def is_known_white(cell):
            return (cell.value is not None) or (cell in self.forced_white)

        for dr, dc in dirs:
            r, c = clue.row + dr, clue.col + dc

            while 0 <= r < self.graph.size and 0 <= c < self.graph.size:
                cell = self.graph.grid[r][c]
                if cell.is_black:
                    break
                max_v += 1
                r += dr
                c += dc

            r, c = clue.row + dr, clue.col + dc
            while 0 <= r < self.graph.size and 0 <= c < self.graph.size:
                cell = self.graph.grid[r][c]
                if cell.is_black:
                    break
                if is_known_white(cell):
                    min_v += 1
                    r += dr
                    c += dc
                    continue
                break

        return min_v, max_v

    def make_ai_move(self):
        """AI move using DP heuristic"""
        # Use greedy approach for single moves
        best_cell = None
        best_improvement = -999

        for cell in self.graph.all_cells():
            if cell.value is not None or cell.is_dot:
                continue

            was_black = cell.is_black
            cell.is_black = not cell.is_black

            improvement = self._evaluate_improvement()
            if improvement > best_improvement:
                best_improvement = improvement
                best_cell = cell

            cell.is_black = was_black

        if best_cell and best_improvement > -50:
            best_cell.is_black = not best_cell.is_black
            return True
        return False

    def _evaluate_improvement(self):
        """Evaluate improvement"""
        score = 0
        for clue in self.graph.get_clue_cells():
            visible = self.graph.count_visible_whites(clue)
            diff = abs(visible - clue.value)
            score -= diff * 10
        if self.graph.has_adjacent_blacks():
            score -= 1000
        if not self.graph.is_white_connected():
            score -= 1000
        return score

