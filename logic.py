
# ============================================================================
# FILE 4: logic.py
# ============================================================================
# logic.py - Game logic and validation for Range Puzzle using graph algorithms

from collections import deque

class GameLogic:
    def __init__(self, graph):
        self.graph = graph

    def is_game_complete(self):
        """Check if game is complete and valid according to Range puzzle rules:
        1. No square with a number is coloured black
        2. No two black squares are adjacent (horizontally or vertically)
        3. For any two white squares, there is a path between them using only white squares
        4. Each numbered square shows total white squares visible in 4 directions (including itself)
        """
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
        
        # Rule 4: Visibility matches clues
        if not self.validate_visibility():
            return False
        
        return True

    def validate_visibility(self):
        """Validate that all clue cells see the correct number of white squares"""
        for cell in self.graph.get_clue_cells():
            visible = self.graph.count_visible_whites(cell)
            if visible != cell.value:
                return False
        return True

    def get_violations(self):
        """Get list of constraint violations (for debugging)"""
        violations = []
        
        if self.graph.has_adjacent_blacks():
            violations.append("Adjacent black squares found")
        
        if not self.graph.is_white_connected():
            violations.append("White cells are not all connected")
        
        if not self.validate_visibility():
            for cell in self.graph.get_clue_cells():
                visible = self.graph.count_visible_whites(cell)
                if visible != cell.value:
                    violations.append(f"Cell ({cell.row},{cell.col}) sees {visible}, needs {cell.value}")
        
        return violations


class GameState:
    def __init__(self, graph):
        self.graph = graph
        self.history = []
        self.current_turn = 'human'  # 'human' or 'ai'

    def save(self):
        """Save current state snapshot"""
        snapshot = {}
        for cell in self.graph.all_cells():
            snapshot[(cell.row, cell.col)] = (cell.is_black, cell.is_dot)
        self.history.append(snapshot)

    def undo(self):
        """Undo last move"""
        if not self.history:
            return False

        snapshot = self.history.pop()
        for cell in self.graph.all_cells():
            is_black, is_dot = snapshot.get((cell.row, cell.col), (False, False))
            cell.is_black = is_black
            cell.is_dot = is_dot
        return True

    def reset(self):
        """Reset game state"""
        self.history.clear()
        self.graph.reset()
        self.current_turn = 'human'

    def toggle_turn(self):
        """Toggle between human and AI turns"""
        self.current_turn = 'ai' if self.current_turn == 'human' else 'human'