
# ============================================================================
# FILE 7: gui.py
# ============================================================================
# gui.py - Range Puzzle GUI matching Simon Tatham's style

from tkinter import messagebox
import tkinter as tk
from utils import CELL_SIZE, FONT_MAIN, COLOR_EMPTY, COLOR_BLACK, COLOR_CLUE, COLOR_CURSOR
from solver import GreedySolver, DivideConquerSolver, DynamicProgrammingSolver
from logic import GameLogic, GameState
from generator import PuzzleGenerator


class RangeGUI:
    def __init__(self, root, graph, clues, generator):
        self.root = root
        self.graph = graph
        self.initial_clues = clues
        self.generator = generator
        # Initialize all three solvers
        self.divide_conquer_solver = DivideConquerSolver(graph)
        self.dp_solver = DynamicProgrammingSolver(graph)
        self.greedy_solver = GreedySolver(graph)
        self.logic = GameLogic(graph)
        self.state = GameState(graph)
        # Default difficulty is medium
        self.generator.difficulty = 'medium'

        # Top control frame
        top_frame = tk.Frame(root)
        top_frame.pack(pady=5)

        # Button frame
        btn_frame = tk.Frame(top_frame)
        btn_frame.pack(side="left", padx=10)

        tk.Button(btn_frame, text="New Game", command=self.new_game, 
                 bg="#4CAF50", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Solve", command=self.solve_full,
                 bg="#2196F3", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Restart", command=self.reset).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Undo", command=self.undo).pack(side="left", padx=5)
        
        # Status label - matching Simon Tatham's style
        self.status_label = tk.Label(root, 
                                    text="Click to fill/empty squares. Number shows visible white squares in all 4 directions.",
                                    font=("Arial", 9), wraplength=800)
        self.status_label.pack(pady=5)

        # Canvas for grid
        canvas_size = graph.size * CELL_SIZE
        self.canvas = tk.Canvas(
            root,
            width=canvas_size,
            height=canvas_size,
            bg="white",
            highlightthickness=2,
            highlightbackground="#333333"
        )
        self.canvas.pack(pady=10)
        self.canvas.focus_set()
        
        # Mouse controls - single click to toggle
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Button-1>", lambda e: self.canvas.focus_set(), add="+")
        
        # Keyboard controls
        self.canvas.bind("<KeyPress>", self.on_key_press)
        root.bind("<KeyPress>", self.on_key_press)
        
        # Cursor position
        self.cursor_row = 0
        self.cursor_col = 0

        self.draw()

    def _update_solvers(self):
        """Update all solvers when graph changes"""
        self.divide_conquer_solver = DivideConquerSolver(self.graph)
        self.dp_solver = DynamicProgrammingSolver(self.graph)
        self.greedy_solver = GreedySolver(self.graph)

    def draw(self):
        """Draw the entire grid - Simon Tatham style"""
        self.canvas.delete("all")
        
        # Draw cells
        for cell in self.graph.all_cells():
            self._draw_cell(cell)
        
        # Draw grid lines on top
        for i in range(self.graph.size + 1):
            # Vertical lines
            self.canvas.create_line(
                i * CELL_SIZE, 0,
                i * CELL_SIZE, self.graph.size * CELL_SIZE,
                fill="#666666", width=2
            )
            # Horizontal lines
            self.canvas.create_line(
                0, i * CELL_SIZE,
                self.graph.size * CELL_SIZE, i * CELL_SIZE,
                fill="#666666", width=2
            )
        
        # Draw cursor highlight
        self._draw_cursor()

        # Update status
        if self.logic.is_game_complete():
            self.status_label.config(text="✓ Puzzle Solved! All clues satisfied.", fg="green")
        else:
            violations = self.logic.get_violations()
            if violations:
                self.status_label.config(text="⚠ " + violations[0], fg="red")
            else:
                self.status_label.config(text="Click to fill/empty squares. Arrow keys to move cursor.", fg="black")

    def _draw_cell(self, cell):
        """Draw a single cell"""
        x1 = cell.col * CELL_SIZE
        y1 = cell.row * CELL_SIZE
        x2 = x1 + CELL_SIZE
        y2 = y1 + CELL_SIZE

        # Determine cell background
        if cell.is_black:
            bg_color = COLOR_BLACK
            text_color = "white"
        elif cell.value is not None:  # Clue cell
            bg_color = COLOR_CLUE
            text_color = "black"
        else:
            bg_color = COLOR_EMPTY
            text_color = "black"

        # Draw cell background
        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill=bg_color,
            outline="",
            width=0
        )

        # Draw number if present (clue)
        if cell.value is not None:
            self.canvas.create_text(
                x1 + CELL_SIZE // 2,
                y1 + CELL_SIZE // 2,
                text=str(cell.value),
                font=FONT_MAIN,
                fill=text_color
            )
    
    def _draw_cursor(self):
        """Draw cursor highlight"""
        x1 = self.cursor_col * CELL_SIZE + 2
        y1 = self.cursor_row * CELL_SIZE + 2
        x2 = x1 + CELL_SIZE - 4
        y2 = y1 + CELL_SIZE - 4
        
        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            outline=COLOR_CURSOR,
            width=3,
            tags="cursor"
        )

    def toggle_cell(self, cell):
        """Toggle cell between empty and black (Simon Tatham style)"""
        if cell.value is not None:  # Can't modify clue cells
            return
        
        self.state.save()
        cell.is_black = not cell.is_black
        cell.is_dot = False  # Remove dot marking
        self.draw()

    def on_click(self, event):
        """Handle mouse click - toggle cell"""
        row = event.y // CELL_SIZE
        col = event.x // CELL_SIZE

        if row < 0 or col < 0 or row >= self.graph.size or col >= self.graph.size:
            return

        cell = self.graph.grid[row][col]
        self.cursor_row = row
        self.cursor_col = col
        
        self.toggle_cell(cell)

    def on_key_press(self, event):
        """Handle keyboard input - Simon Tatham style"""
        key = event.keysym
        
        # Cursor movement
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
        
        # Space or Enter = toggle current cell
        if key in ("space", "Return", "KP_Enter"):
            cell = self.graph.grid[self.cursor_row][self.cursor_col]
            self.toggle_cell(cell)
        
        # Redraw if needed
        if moved or key in ("space", "Return", "KP_Enter"):
            self.draw()

    def new_game(self):
        """Generate a completely new puzzle with different numbers and positions"""
        self.status_label.config(text="Generating new puzzle...", fg="blue")
        self.root.update()
        
        # Use medium difficulty (default)
        self.generator.difficulty = 'medium'
        
        # Generate new puzzle
        new_graph, new_clues = self.generator.generate()
        
        # Update the game with new puzzle
        self.graph = new_graph
        self.initial_clues = new_clues
        self._update_solvers()  # Update all solvers
        self.logic = GameLogic(self.graph)
        self.state = GameState(self.graph)
        
        # Reset cursor
        self.cursor_row = 0
        self.cursor_col = 0
        
        self.status_label.config(text="New puzzle generated! Good luck!", fg="green")
        self.draw()

    def solve_full(self):
        """Solve entire puzzle using all three algorithms with focus on Divide & Conquer and DP"""
        # Update all solvers with current graph
        self._update_solvers()
        
        self.state.save()
        
        # Ensure clues are set (solve() will reset graph but clues persist)
        self.graph.set_clues(self.initial_clues)
        
        # Try algorithms in order: Divide & Conquer (primary) -> DP (primary) -> Greedy (fallback)
        algorithms = [
            (self.divide_conquer_solver, "Divide and Conquer"),
            (self.dp_solver, "Dynamic Programming"),
            (self.greedy_solver, "Backtracking + Greedy Heuristics")
        ]
        
        success = False
        successful_algorithm = None
        
        for solver, algo_name in algorithms:
            self.status_label.config(text=f"Trying {algo_name}... Please wait.", fg="blue")
            self.root.update()
            
            # Ensure clues are set before each attempt (solve() resets internally)
            self.graph.set_clues(self.initial_clues)
            
            # Try solving with this algorithm
            if solver.solve():
                # Validate the solution
                if self.logic.is_game_complete():
                    success = True
                    successful_algorithm = algo_name
                    break
                else:
                    # Solution found but invalid, restore clues and continue to next algorithm
                    self.graph.set_clues(self.initial_clues)
                    continue
        
        if not success:
            self.state.undo()
            messagebox.showerror("AI Solver", 
                "Could not find a solution using any algorithm.\n\n"
                "The puzzle may be:\n"
                "• Unsolvable with current clues\n"
                "• Too difficult for the solvers\n"
                "• Already partially filled incorrectly\n\n"
                "Try 'Restart' to clear your moves or 'New Game' for a different puzzle.")
        else:
            messagebox.showinfo("AI Solver - Success!", 
                f"Puzzle solved successfully using {successful_algorithm}!\n\n"
                "All clues satisfied:\n"
                "✓ No numbered squares are black\n"
                "✓ No adjacent black squares\n"
                "✓ All white squares connected\n"
                "✓ Visibility matches all clues\n\n"
                f"Algorithm used: {successful_algorithm}\n"
                f"Algorithms tried: Divide & Conquer → DP → Greedy")
        
        self.draw()

    def undo(self):
        """Undo last move"""
        if not self.state.undo():
            messagebox.showinfo("Undo", "Nothing to undo")
        else:
            self.draw()

    def reset(self):
        """Reset current puzzle to starting position (keep same clues)"""
        self.state.reset()
        # Restore original clues
        self.graph.set_clues(self.initial_clues)
        self.cursor_row = 0
        self.cursor_col = 0
        self.draw()