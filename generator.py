# ============================================================================
# FILE 6: generator.py
# ============================================================================
# generator.py - Random Range Puzzle Generator

import random
from graph import GridGraph

class PuzzleGenerator:
    """Generates valid Range puzzles with random black square patterns"""
    
    def __init__(self, size=8, difficulty='medium'):
        self.size = size
        self.difficulty = difficulty
        
        # Difficulty settings: (min_blacks, max_blacks, num_clues)
        self.difficulty_settings = {
            'easy': (3, 6, 8),
            'medium': (6, 10, 10),
            'hard': (8, 14, 12)
        }
    
    def generate(self):
        """Generate a new random valid puzzle"""
        max_attempts = 100
        
        for attempt in range(max_attempts):
            graph = GridGraph(self.size)
            
            # Place random black squares
            if self._place_black_squares(graph):
                # Generate clues from the solution
                clues = self._generate_clues(graph)
                
                if clues and len(clues) >= 6:  # Ensure minimum clues
                    # Reset grid but keep clues
                    new_graph = GridGraph(self.size)
                    new_graph.set_clues(clues)
                    return new_graph, clues
        
        # Fallback to default puzzle if generation fails
        return self._get_default_puzzle()
    
    def _place_black_squares(self, graph):
        """Randomly place black squares following Range puzzle rules"""
        min_blacks, max_blacks, _ = self.difficulty_settings[self.difficulty]
        num_blacks = random.randint(min_blacks, max_blacks)
        
        # Get all cells
        all_cells = list(graph.all_cells())
        random.shuffle(all_cells)
        
        blacks_placed = 0
        
        for cell in all_cells:
            if blacks_placed >= num_blacks:
                break
            
            # Try to place black square
            cell.is_black = True
            
            # Check if valid (no adjacent blacks, whites still connected)
            if self._is_valid_placement(graph):
                blacks_placed += 1
            else:
                cell.is_black = False  # Revert
        
        # Need at least minimum blacks
        return blacks_placed >= min_blacks
    
    def _is_valid_placement(self, graph):
        """Check if current black placement is valid"""
        # Rule: No adjacent black squares
        if graph.has_adjacent_blacks():
            return False
        
        # Rule: All white squares must be connected
        if not graph.is_white_connected():
            return False
        
        return True
    
    def _generate_clues(self, graph):
        """Generate clues from a solved grid"""
        _, _, num_clues = self.difficulty_settings[self.difficulty]
        
        # Get all white cells (potential clue positions)
        white_cells = [c for c in graph.all_cells() if not c.is_black]
        
        if len(white_cells) < num_clues:
            return None
        
        # Randomly select clue positions
        random.shuffle(white_cells)
        clue_cells = white_cells[:num_clues]
        
        clues = {}
        for cell in clue_cells:
            # Calculate visibility from this position
            visible = graph.count_visible_whites(cell)
            clues[(cell.row, cell.col)] = visible
        
        return clues
    
    def _get_default_puzzle(self):
        """Return default puzzle if generation fails"""
        size = 8
        clues = {
            (0, 3): 8,
            (0, 5): 6,
            (1, 1): 10,
            (1, 3): 14,
            (2, 1): 4,
            (2, 5): 7,
            (3, 3): 9,
            (3, 7): 12,
            (4, 5): 8,
            (4, 7): 6,
            (5, 1): 3,
            (5, 5): 8,
        }
        
        graph = GridGraph(size)
        graph.set_clues(clues)
        return graph, clues

