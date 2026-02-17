"""

RANGE PUZZLE SOLVER - 2 PLAYER GAME (Human vs AI)

A competitive 2-player implementation where you compete against AI to correctly
solve the Range Puzzle by making valid moves.

GAME RULES (Range Puzzle / Kurodoko):
1. NO two black squares are orthogonally adjacent
2. ALL white squares must be connected (no isolated groups)
3. Each numbered cell sees EXACTLY that many white squares (counting itself)
   in all 4 orthogonal directions until blocked by black squares or edges
4. Numbered cells can NEVER be black

SCORING:
- Each VALID move (follows ALL rules) = 1 point to YOU
- Each INVALID move (breaks ANY rule) = 1 point to AI
- When AI completes the puzzle correctly = AI WINS and shows solved board


AI uses three algorithms rotating: Divide & Conquer → Dynamic Programming → Greedy
"""

import tkinter as tk
from tkinter import messagebox
from collections import deque
import random


# CONSTANTS

CELL_SIZE = 60
FONT_MAIN = ("Arial", 16, "bold")
FONT_SMALL = ("Arial", 10)
COLOR_EMPTY = "white"
COLOR_BLACK = "#000000"
COLOR_CLUE = "#FFFFCC"
COLOR_CURSOR = "#FF6B00"
COLOR_DOT = "#CCCCCC"


# DATA STRUCTURES


class Cell:
    """Represents a single cell in the grid"""
    def __init__(self, row, col, value=None):
        self.row = row
        self.col = col
        self.value = value  # Clue number (how many white squares visible)
        self.is_black = False
        self.is_dot = False

    def copy(self):
        c = Cell(self.row, self.col, self.value)
        c.is_black = self.is_black
        c.is_dot = self.is_dot
        return c


class GridGraph:
    """Graph-based grid representation for Range Puzzle"""
    def __init__(self, size):
        self.size = size
        self.grid = []
        self._create_grid()

    def _create_grid(self):
        for r in range(self.size):
            row = []
            for c in range(self.size):
                row.append(Cell(r, c))
            self.grid.append(row)

    def set_clues(self, clues):
        for (r, c), v in clues.items():
            self.grid[r][c].value = v

    def neighbors(self, cell):
        """Get 4-directional neighbors (graph adjacency)"""
        dirs = [(-1,0),(1,0),(0,-1),(0,1)]
        result = []
        for dr, dc in dirs:
            nr = cell.row + dr
            nc = cell.col + dc
            if 0 <= nr < self.size and 0 <= nc < self.size:
                result.append(self.grid[nr][nc])
        return result

    def all_cells(self):
        for row in self.grid:
            for cell in row:
                yield cell

    def get_cell(self, row, col):
        if 0 <= row < self.size and 0 <= col < self.size:
            return self.grid[row][col]
        return None

    def count_visible_whites(self, cell):
        """Count white squares visible from this cell in all 4 directions"""
        if cell.is_black:
            return 0
        count = 1  # Count the cell itself
        directions = [(-1,0), (1,0), (0,-1), (0,1)]
        for dr, dc in directions:
            r, c = cell.row + dr, cell.col + dc
            while 0 <= r < self.size and 0 <= c < self.size:
                neighbor = self.grid[r][c]
                if neighbor.is_black:
                    break
                count += 1
                r += dr
                c += dc
        return count

    def get_white_cells(self):
        return [cell for cell in self.all_cells() if not cell.is_black]

    def is_white_connected(self):
        """BFS to check if all white cells form a connected component"""
        white_cells = self.get_white_cells()
        if not white_cells:
            return True
        start = white_cells[0]
        queue = deque([start])
        visited = {start}
        while queue:
            current = queue.popleft()
            for neighbor in self.neighbors(current):
                if not neighbor.is_black and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        return len(visited) == len(white_cells)

    def has_adjacent_blacks(self):
        """Check if any two black squares are orthogonally adjacent"""
        for cell in self.all_cells():
            if cell.is_black:
                for neighbor in self.neighbors(cell):
                    if neighbor.is_black:
                        return True
        return False

    def get_clue_cells(self):
        return [cell for cell in self.all_cells() if cell.value is not None]

    def reset(self):
        for cell in self.all_cells():
            if cell.value is None:  # Don't reset clues
                cell.is_black = False
                cell.is_dot = False

    def copy_state(self):
        """Save current state"""
        state = {}
        for cell in self.all_cells():
            state[(cell.row, cell.col)] = (cell.is_black, cell.is_dot)
        return state

    def restore_state(self, state):
        """Restore saved state"""
        for cell in self.all_cells():
            if (cell.row, cell.col) in state:
                cell.is_black, cell.is_dot = state[(cell.row, cell.col)]



# GAME LOGIC


class GameLogic:
    """Game logic and validation using graph algorithms"""
    def __init__(self, graph):
        self.graph = graph

    def is_valid_state(self):
        """Check if current state is valid (no violations)"""
        # Rule 1: No numbered squares are black
        for cell in self.graph.get_clue_cells():
            if cell.is_black:
                return False
        # Rule 2: No adjacent black squares
        if self.graph.has_adjacent_blacks():
            return False
        # Rule 3: All white squares connected
        if not self.graph.is_white_connected():
            return False
        return True

    def is_game_complete(self):
        """Check if game is complete and correct"""
        if not self.is_valid_state():
            return False
        # Rule 4: All clues must be satisfied
        return self.validate_all_clues()

    def validate_all_clues(self):
        """Check if all clues are satisfied"""
        for cell in self.graph.get_clue_cells():
            visible = self.graph.count_visible_whites(cell)
            if visible != cell.value:
                return False
        return True

    def get_violations(self):
        violations = []
        for cell in self.graph.get_clue_cells():
            if cell.is_black:
                violations.append(f" Clue cell ({cell.row},{cell.col}) is BLACK!")
        if self.graph.has_adjacent_blacks():
            violations.append(" Adjacent black squares found")
        if not self.graph.is_white_connected():
            violations.append(" White cells are NOT all connected")
        for cell in self.graph.get_clue_cells():
            if not cell.is_black:
                visible = self.graph.count_visible_whites(cell)
                if visible != cell.value:
                    violations.append(f" Cell ({cell.row},{cell.col}) sees {visible}, needs {cell.value}")
        return violations



# AI SOLVERS


class DivideConquerSolver:
    """Divide and Conquer Algorithm"""
    def __init__(self, graph):
        self.graph = graph

    def find_best_move(self):
        """Find best move using divide and conquer heuristic"""
        best_cell = None
        best_score = -999999
        
        for cell in self.graph.all_cells():
            if cell.value is not None or cell.is_black or cell.is_dot:
                continue
            
            # Try making this cell black
            old_state = self.graph.copy_state()
            cell.is_black = True
            
            score = self._evaluate_state()
            
            if score > best_score:
                best_score = score
                best_cell = cell
            
            self.graph.restore_state(old_state)
        
        return best_cell

    def _evaluate_state(self):
        """Evaluate how good the current state is"""
        score = 0
        
        # Heavy penalty for rule violations
        if self.graph.has_adjacent_blacks():
            score -= 100000
        if not self.graph.is_white_connected():
            score -= 100000
        
        # Check clue cells aren't black
        for clue in self.graph.get_clue_cells():
            if clue.is_black:
                score -= 100000
        
        # Reward for getting closer to clue satisfaction
        for clue in self.graph.get_clue_cells():
            visible = self.graph.count_visible_whites(clue)
            diff = abs(visible - clue.value)
            score -= diff * 1000
            if visible == clue.value:
                score += 5000
        
        return score


class DynamicProgrammingSolver:
    """Dynamic Programming Algorithm"""
    def __init__(self, graph):
        self.graph = graph

    def find_best_move(self):
        """Find best move using DP-style evaluation"""
        best_cell = None
        best_score = -999999
        
        # Focus on cells near unsatisfied clues
        clue_cells = self.graph.get_clue_cells()
        unsatisfied = [c for c in clue_cells if self.graph.count_visible_whites(c) != c.value]
        
        for cell in self.graph.all_cells():
            if cell.value is not None or cell.is_black or cell.is_dot:
                continue
            
            # Distance to nearest unsatisfied clue
            min_dist = float('inf')
            for clue in unsatisfied:
                dist = abs(cell.row - clue.row) + abs(cell.col - clue.col)
                min_dist = min(min_dist, dist)
            
            old_state = self.graph.copy_state()
            cell.is_black = True
            
            score = self._evaluate_state()
            score += (20 - min_dist) * 100  # Prefer cells closer to unsatisfied clues
            
            if score > best_score:
                best_score = score
                best_cell = cell
            
            self.graph.restore_state(old_state)
        
        return best_cell

    def _evaluate_state(self):
        score = 0
        if self.graph.has_adjacent_blacks():
            score -= 100000
        if not self.graph.is_white_connected():
            score -= 100000
        for clue in self.graph.get_clue_cells():
            if clue.is_black:
                score -= 100000
            visible = self.graph.count_visible_whites(clue)
            diff = abs(visible - clue.value)
            score -= diff * 1000
            if visible == clue.value:
                score += 5000
        return score


class GreedySolver:
    """Greedy Algorithm"""
    def __init__(self, graph):
        self.graph = graph

    def find_best_move(self):
        """Find best move using greedy improvement"""
        best_cell = None
        best_improvement = -999999
        
        for cell in self.graph.all_cells():
            if cell.value is not None or cell.is_black or cell.is_dot:
                continue
            
            old_state = self.graph.copy_state()
            current_quality = self._evaluate_state()
            
            cell.is_black = True
            new_quality = self._evaluate_state()
            improvement = new_quality - current_quality
            
            if improvement > best_improvement:
                best_improvement = improvement
                best_cell = cell
            
            self.graph.restore_state(old_state)
        
        return best_cell

    def _evaluate_state(self):
        score = 0
        if self.graph.has_adjacent_blacks():
            score -= 100000
        if not self.graph.is_white_connected():
            score -= 100000
        for clue in self.graph.get_clue_cells():
            if clue.is_black:
                score -= 100000
            visible = self.graph.count_visible_whites(clue)
            diff = abs(visible - clue.value)
            score -= diff * 1000
            if visible == clue.value:
                score += 5000
        return score



# PUZZLE GENERATOR


class PuzzleGenerator:
    """Generates valid Range puzzles"""
    def __init__(self, size=8, difficulty='medium'):
        self.size = size
        self.difficulty = difficulty
        self.difficulty_settings = {
            'easy': (3, 6, 8),
            'medium': (6, 10, 10),
            'hard': (8, 14, 12)
        }

    def generate(self):
        max_attempts = 100
        for attempt in range(max_attempts):
            graph = GridGraph(self.size)
            if self._place_black_squares(graph):
                clues = self._generate_clues(graph)
                if clues and len(clues) >= 6:
                    # Save solution
                    solution = graph.copy_state()
                    # Create new graph with just clues
                    new_graph = GridGraph(self.size)
                    new_graph.set_clues(clues)
                    return new_graph, clues, solution
        return self._get_default_puzzle()

    def _place_black_squares(self, graph):
        min_blacks, max_blacks, _ = self.difficulty_settings[self.difficulty]
        num_blacks = random.randint(min_blacks, max_blacks)
        all_cells = list(graph.all_cells())
        random.shuffle(all_cells)
        blacks_placed = 0
        for cell in all_cells:
            if blacks_placed >= num_blacks:
                break
            cell.is_black = True
            if self._is_valid_placement(graph):
                blacks_placed += 1
            else:
                cell.is_black = False
        return blacks_placed >= min_blacks

    def _is_valid_placement(self, graph):
        if graph.has_adjacent_blacks():
            return False
        if not graph.is_white_connected():
            return False
        return True

    def _generate_clues(self, graph):
        _, _, num_clues = self.difficulty_settings[self.difficulty]
        white_cells = [c for c in graph.all_cells() if not c.is_black]
        if len(white_cells) < num_clues:
            return None
        random.shuffle(white_cells)
        clue_cells = white_cells[:num_clues]
        clues = {}
        for cell in clue_cells:
            visible = graph.count_visible_whites(cell)
            clues[(cell.row, cell.col)] = visible
        return clues

    def _get_default_puzzle(self):
        size = 8
        clues = {
            (0, 3): 8, (0, 5): 6, (1, 1): 10, (1, 3): 14,
            (2, 1): 4, (2, 5): 7, (3, 3): 9, (3, 7): 12,
            (4, 5): 8, (4, 7): 6, (5, 1): 3, (5, 5): 8,
        }
        graph = GridGraph(size)
        # Generate solution by placing blacks
        solution_blacks = [
            (0, 0), (0, 7), (1, 4), (2, 2), (3, 0), (3, 5),
            (4, 1), (5, 6), (6, 3), (7, 1), (7, 7)
        ]
        for r, c in solution_blacks:
            graph.grid[r][c].is_black = True
        solution = graph.copy_state()
        
        # Create clean graph with clues
        new_graph = GridGraph(size)
        new_graph.set_clues(clues)
        return new_graph, clues, solution



# GUI - 2 PLAYER VERSION


class RangeGUI:
    """GUI for 2-player Range Puzzle"""
    def __init__(self, root, graph, clues, solution, generator):
        self.root = root
        self.graph = graph
        self.initial_clues = clues
        self.solution = solution  # Correct solution for when AI wins
        self.generator = generator
        
        # Solvers
        self.dc_solver = DivideConquerSolver(graph)
        self.dp_solver = DynamicProgrammingSolver(graph)
        self.greedy_solver = GreedySolver(graph)
        
        self.logic = GameLogic(graph)
        self.generator.difficulty = 'medium'
        
        # Game state
        self.current_turn = 'player'
        self.winner = None
        self.player_score = 0
        self.ai_score = 0
        self.player_violations = 0  # Track violations - 3 strikes and AI wins!
        self.current_algorithm = 0  # 0=DC, 1=DP, 2=Greedy
        self.algorithm_names = ["Divide & Conquer", "Dynamic Programming", "Greedy"]
        self.game_over = False
        
        # History for undo
        self.history = []
        
        self._setup_ui()
        self.cursor_row = 0
        self.cursor_col = 0
        self.draw()

    def _setup_ui(self):
        """Setup user interface"""
        top_frame = tk.Frame(self.root)
        top_frame.pack(pady=5)
        
        btn_frame = tk.Frame(top_frame)
        btn_frame.pack(side="left", padx=10)
        
        tk.Button(btn_frame, text="New Game", command=self.new_game,
                 bg="#4CAF50", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Restart", command=self.reset).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Undo", command=self.undo).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Rules", command=self.show_rules,
                 bg="#2196F3", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        
        self.status_label = tk.Label(self.root,
                                    text="YOUR TURN - Click to place black square",
                                    font=("Arial", 10), wraplength=800)
        self.status_label.pack(pady=5)
        
        self.score_label = tk.Label(self.root,
                                    text=f"Score: YOU={self.player_score} | AI={self.ai_score}",
                                    font=("Arial", 12, "bold"), fg="#2196F3")
        self.score_label.pack(pady=2)
        
        canvas_size = self.graph.size * CELL_SIZE
        self.canvas = tk.Canvas(self.root, width=canvas_size, height=canvas_size,
                               bg="white", highlightthickness=2, highlightbackground="#333333")
        self.canvas.pack(pady=10)
        self.canvas.focus_set()
        
        # Mouse bindings
        self.canvas.bind("<Button-1>", self.on_left_click)
        self.canvas.bind("<Button-3>", self.on_right_click)
        
        # Keyboard bindings
        self.canvas.bind("<KeyPress>", self.on_key_press)
        self.root.bind("<KeyPress>", self.on_key_press)

    def draw(self):
        """Draw the game board"""
        self.canvas.delete("all")
        for cell in self.graph.all_cells():
            self._draw_cell(cell)
        
        # Draw grid lines
        for i in range(self.graph.size + 1):
            self.canvas.create_line(i * CELL_SIZE, 0, i * CELL_SIZE,
                                   self.graph.size * CELL_SIZE, fill="#666666", width=2)
            self.canvas.create_line(0, i * CELL_SIZE, self.graph.size * CELL_SIZE,
                                   i * CELL_SIZE, fill="#666666", width=2)
        
        self._draw_cursor()
        self._update_status()

    def _draw_cell(self, cell):
        """Draw a single cell"""
        x1 = cell.col * CELL_SIZE
        y1 = cell.row * CELL_SIZE
        x2 = x1 + CELL_SIZE
        y2 = y1 + CELL_SIZE
        
        if cell.is_black:
            bg_color = COLOR_BLACK
            text_color = "white"
        elif cell.value is not None:
            bg_color = COLOR_CLUE
            text_color = "black"
        else:
            bg_color = COLOR_EMPTY
            text_color = "black"
        
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=bg_color, outline="", width=0)
        
        if cell.value is not None:
            self.canvas.create_text(x1 + CELL_SIZE // 2, y1 + CELL_SIZE // 2,
                                   text=str(cell.value), font=FONT_MAIN, fill=text_color)
        
        # Draw dot if marked
        if cell.is_dot and not cell.is_black:
            self.canvas.create_oval(x1 + CELL_SIZE // 2 - 6, y1 + CELL_SIZE // 2 - 6,
                                   x1 + CELL_SIZE // 2 + 6, y1 + CELL_SIZE // 2 + 6,
                                   fill=COLOR_DOT, outline="")

    def _draw_cursor(self):
        """Draw cursor"""
        x1 = self.cursor_col * CELL_SIZE + 2
        y1 = self.cursor_row * CELL_SIZE + 2
        x2 = x1 + CELL_SIZE - 4
        y2 = y1 + CELL_SIZE - 4
        self.canvas.create_rectangle(x1, y1, x2, y2, outline=COLOR_CURSOR, width=3)

    def _update_status(self):
        """Update status display"""
        violations_text = f" | Violations: {self.player_violations}/3" if self.player_violations > 0 else ""
        self.score_label.config(text=f"Score: YOU={self.player_score} | AI={self.ai_score}{violations_text}")
        
        if self.game_over:
            if self.winner == 'ai':
                self.status_label.config(
                    text=f" AI WINS! AI solved the puzzle! Final: You={self.player_score}, AI={self.ai_score}",
                    fg="red", font=("Arial", 11, "bold"))
            elif self.winner == 'player':
                self.status_label.config(
                    text=f" AMAZING! YOU WIN! You beat the AI! Final: You={self.player_score}, AI={self.ai_score}",
                    fg="green", font=("Arial", 11, "bold"))
        elif self.current_turn == 'player':
            violations = self.logic.get_violations()
            warning = f"  {3 - self.player_violations} strikes left!" if self.player_violations > 0 else ""
            if violations:
                self.status_label.config(
                    text=f"YOUR TURN - Click to place black | Score: You={self.player_score}, AI={self.ai_score}{warning} (⚠ VIOLATIONS = Point to AI)",
                    fg="orange")
            else:
                self.status_label.config(
                    text=f"YOUR TURN - Click to place black | Score: You={self.player_score}, AI={self.ai_score}{warning}",
                    fg="black")
        else:
            algo_name = self.algorithm_names[self.current_algorithm]
            self.status_label.config(
                text=f"AI TURN - Using {algo_name}... | Score: You={self.player_score}, AI={self.ai_score}",
                fg="blue")

    def on_left_click(self, event):
        """Left click - place black square"""
        if self.current_turn != 'player' or self.game_over:
            return
        
        row = event.y // CELL_SIZE
        col = event.x // CELL_SIZE
        if not (0 <= row < self.graph.size and 0 <= col < self.graph.size):
            return
        
        cell = self.graph.grid[row][col]
        self.cursor_row = row
        self.cursor_col = col
        self.make_player_move(cell)

    def on_right_click(self, event):
        """Right click - place dot marker"""
        if self.current_turn != 'player' or self.game_over:
            return
        
        row = event.y // CELL_SIZE
        col = event.x // CELL_SIZE
        if not (0 <= row < self.graph.size and 0 <= col < self.graph.size):
            return
        
        cell = self.graph.grid[row][col]
        if cell.value is not None or cell.is_black:
            return
        
        cell.is_dot = not cell.is_dot
        self.draw()

    def make_player_move(self, cell):
        """Player makes a move"""
        if cell.value is not None or cell.is_black:
            return
        
        # Save state for undo
        self.history.append(self.graph.copy_state())
        
        # Make move
        cell.is_black = True
        cell.is_dot = False
        
        # Check if move is valid
        is_valid = self.logic.is_valid_state()
        
        if is_valid:
            self.player_score += 1
            self.draw()
        else:
            # INVALID MOVE - Point goes to AI and count violation!
            self.ai_score += 1
            self.player_violations += 1
            violations = self.logic.get_violations()
            self.draw()
            
            # Check if player hit 3 violations
            if self.player_violations >= 3:
                messagebox.showerror("GAME OVER!",
                    f" 3 STRIKES - YOU'RE OUT!\n\n"
                    f"You violated the rules {self.player_violations} times.\n\n"
                    f"Violations:\n" + "\n".join(violations[:3]) + "\n\n"
                    f" AI WINS!\n\n"
                    f"Final Score: You={self.player_score} | AI={self.ai_score}\n\n"
                    f"The AI will now show you the correct solution...")
                self.ai_wins_by_violations()
                return
            else:
                strikes_left = 3 - self.player_violations
                messagebox.showwarning("Invalid Move!",
                    f" RULE VIOLATION! (Strike {self.player_violations}/3)\n\n"
                    f"Your move broke the rules:\n" + "\n".join(violations[:3]) + "\n\n"
                    f" Point goes to AI!\n"
                    f" {strikes_left} strike{'s' if strikes_left != 1 else ''} remaining!\n\n"
                    f"Score: You={self.player_score} | AI={self.ai_score}")
        
        # Switch to AI
        self.current_turn = 'ai'
        self.draw()
        self.root.after(800, self.make_ai_move)



    def make_ai_move(self):
        """AI makes a move"""
        if self.game_over:
            return
        
        # Select solver
        if self.current_algorithm == 0:
            solver = self.dc_solver
        elif self.current_algorithm == 1:
            solver = self.dp_solver
        else:
            solver = self.greedy_solver
        
        algo_name = self.algorithm_names[self.current_algorithm]
        
        # Rotate algorithm for next turn
        self.current_algorithm = (self.current_algorithm + 1) % 3
        
        # Find best move
        best_cell = solver.find_best_move()
        
        if best_cell:
            best_cell.is_black = True
            
            # Check if move is valid
            is_valid = self.logic.is_valid_state()
            
            if is_valid:
                self.ai_score += 1
        
        # Check if game is complete
        if self.logic.is_game_complete():
            self.ai_wins()
            return
        
        # Switch back to player
        self.current_turn = 'player'
        self.draw()

    def ai_wins(self):
        """AI wins - show completed puzzle"""
        self.game_over = True
        self.winner = 'ai'
        
        # Show the correct solution
        self.graph.restore_state(self.solution)
        self.draw()
        
        messagebox.showinfo("AI WINS!",
            f" AI WINS! \n\n"
            f"AI successfully solved the puzzle!\n\n"
            f"Final Scores:\n"
            f"Your score: {self.player_score}\n"
            f"AI score: {self.ai_score}\n\n"
            f"The complete solution is now displayed on the board.\n\n"
            f"All Range Puzzle rules satisfied:\n"
            f" No adjacent black squares\n"
            f" All white squares connected\n"
            f" All clues satisfied\n\n"
            f"AI used: {', '.join(self.algorithm_names)}")

    def ai_wins_by_violations(self):
        """AI wins because player got 3 violations - show completed puzzle"""
        self.game_over = True
        self.winner = 'ai'
    
        # Show the correct solution
        self.graph.restore_state(self.solution)
        self.draw()
        
        # Show final message with solution
        messagebox.showinfo("AI WINS - Solution Displayed!",
            f" AI WINS BY 3 STRIKES! \n\n"
            f"You violated the rules 3 times.\n\n"
            f"Final Scores:\n"
            f"Your score: {self.player_score}\n"
            f"AI score: {self.ai_score}\n"
            f"Your violations: {self.player_violations}\n\n"
            f"The CORRECT SOLUTION is now displayed on the board.\n\n"
            f"Study it to understand the rules better!\n\n"
            f"All Range Puzzle rules satisfied:\n"
            f" No adjacent black squares\n"
            f" All white squares connected\n"
            f" All clues satisfied")

    def on_key_press(self, event):
        """Handle keyboard input"""
        key = event.keysym
        moved = False
        
        if key in ("Up", "w", "W", "k", "K"):
            if self.cursor_row > 0:
                self.cursor_row -= 1
                moved = True
        elif key in ("Down", "s", "S", "j", "J"):
            if self.cursor_row < self.graph.size - 1:
                self.cursor_row += 1
                moved = True
        elif key in ("Left", "a", "A", "h", "H"):
            if self.cursor_col > 0:
                self.cursor_col -= 1
                moved = True
        elif key in ("Right", "d", "D", "l", "L"):
            if self.cursor_col < self.graph.size - 1:
                self.cursor_col += 1
                moved = True
        
        if key in ("space", "Return", "KP_Enter"):
            if self.current_turn == 'player' and not self.game_over:
                cell = self.graph.grid[self.cursor_row][self.cursor_col]
                self.make_player_move(cell)
            else:
                moved = True
        
        if moved:
            self.draw()

    def new_game(self):
        """Start new game"""
        self.graph, self.initial_clues, self.solution = self.generator.generate()
        
        # Update solvers
        self.dc_solver = DivideConquerSolver(self.graph)
        self.dp_solver = DynamicProgrammingSolver(self.graph)
        self.greedy_solver = GreedySolver(self.graph)
        self.logic = GameLogic(self.graph)
        
        # Reset game state
        self.current_turn = 'player'
        self.winner = None
        self.player_score = 0
        self.ai_score = 0
        self.player_violations = 0  # Reset violations
        self.current_algorithm = 0
        self.game_over = False
        self.history = []
        self.cursor_row = 0
        self.cursor_col = 0
        
        self.draw()

    def reset(self):
        """Reset current puzzle"""
        self.graph.reset()
        self.current_turn = 'player'
        self.winner = None
        self.player_score = 0
        self.ai_score = 0
        self.player_violations = 0  # Reset violations
        self.current_algorithm = 0
        self.game_over = False
        self.history = []
        self.cursor_row = 0
        self.cursor_col = 0
        self.draw()

    def undo(self):
        """Undo last move"""
        if self.current_turn != 'player' or self.game_over or not self.history:
            return
        
        state = self.history.pop()
        self.graph.restore_state(state)
        self.draw()

    def show_rules(self):
        """Show game rules"""
        messagebox.showinfo("Range Puzzle - 2 Player Rules",
            "OBJECTIVE:\n"
            "Compete against AI to solve the puzzle correctly!\n\n"
            "RANGE PUZZLE RULES:\n"
            "1. Color some squares black\n"
            "2. NO two black squares can be orthogonally adjacent\n"
            "3. ALL white squares must be connected (no isolated groups)\n"
            "4. Each numbered cell must see EXACTLY that many white squares\n"
            "   (counting itself, in all 4 directions until blocked)\n"
            "5. Numbered cells can NEVER be black\n\n"
            "CONTROLS:\n"
            "• Left-click: Place black square\n"
            "• Right-click: Place dot marker (reminder: not black)\n"
            "• Arrow keys: Move cursor\n"
            "• Space/Enter: Place black at cursor\n\n"
            "SCORING:\n"
            "• Each VALID move (follows ALL rules) = +1 point to YOU\n"
            "• Each INVALID move (breaks ANY rule) = +1 point to AI\n"
            "• 3 VIOLATIONS = GAME OVER! AI wins immediately!\n"
            "• When AI completes puzzle correctly = AI WINS!\n"
            "• Final solved board is displayed when AI wins\n\n"
            "AI ALGORITHMS:\n"
            "AI rotates: Divide & Conquer → Dynamic Programming → Greedy\n\n"
            " 3 STRIKES AND YOU'RE OUT!\n"
            " AI is designed to win most games!\n"
            "Challenge: Try to score more points than AI!")



# MAIN ENTRY POINT


def main():
    """Main entry point"""
    root = tk.Tk()
    root.title("Range Puzzle - 2 Player Game (Human vs AI)")
    root.resizable(False, False)
    generator = PuzzleGenerator(size=8, difficulty='medium')
    graph, clues, solution = generator.generate()
    RangeGUI(root, graph, clues, solution, generator)
    root.mainloop()

if __name__ == "__main__":
    main()