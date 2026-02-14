# ============================================================================
# FILE 3: graph.py
# ============================================================================
# graph.py - Graph-based grid representation for Range Puzzle

from collections import deque

class Cell:
    def __init__(self, row, col, value=None):
        self.row = row
        self.col = col
        self.value = value  # Clue number (how many white squares visible)
        self.is_black = False  # True if this cell is black
        self.is_dot = False  # True if marked with dot (definitely not black)

    def copy(self):
        c = Cell(self.row, self.col, self.value)
        c.is_black = self.is_black
        c.is_dot = self.is_dot
        return c

    def __repr__(self):
        return f"Cell({self.row},{self.col},val={self.value},black={self.is_black})"


class GridGraph:
    def __init__(self, size):
        self.size = size
        self.grid = []
        self._create_grid()

    def _create_grid(self):
        """Create grid graph structure"""
        for r in range(self.size):
            row = []
            for c in range(self.size):
                row.append(Cell(r, c))
            self.grid.append(row)

    def set_clues(self, clues):
        """Set clue values in the graph"""
        for (r, c), v in clues.items():
            if isinstance(v, tuple):
                # (value, ...) - just use the value
                self.grid[r][c].value = v[0] if v[0] is not None else None
            else:
                self.grid[r][c].value = v

    def neighbors(self, cell):
        """Get graph neighbors (4-directional adjacency)"""
        dirs = [(-1,0),(1,0),(0,-1),(0,1)]  # Up, Down, Left, Right
        result = []
        for dr, dc in dirs:
            nr = cell.row + dr
            nc = cell.col + dc
            if 0 <= nr < self.size and 0 <= nc < self.size:
                result.append(self.grid[nr][nc])
        return result

    def all_cells(self):
        """Iterate over all cells in the grid"""
        for row in self.grid:
            for cell in row:
                yield cell

    def get_cell(self, row, col):
        """Get cell at specific coordinates"""
        if 0 <= row < self.size and 0 <= col < self.size:
            return self.grid[row][col]
        return None

    def count_visible_whites(self, cell):
        """Count white squares visible from this cell in all 4 directions (including itself)
        Range puzzle: count all white squares visible in 4 orthogonal directions + self"""
        if cell.is_black:
            return 0
        
        count = 1  # Count the cell itself first
        # Count in 4 directions: up, down, left, right
        directions = [(-1,0), (1,0), (0,-1), (0,1)]
        
        for dr, dc in directions:
            r, c = cell.row + dr, cell.col + dc  # Start from adjacent cell
            
            # Look in this direction until we hit a black square or edge
            while 0 <= r < self.size and 0 <= c < self.size:
                neighbor = self.grid[r][c]
                if neighbor.is_black:
                    break  # Hit black square, stops visibility
                count += 1
                r += dr
                c += dc
        
        return count

    def get_white_cells(self):
        """Get all white cells using graph traversal"""
        return [cell for cell in self.all_cells() if not cell.is_black]

    def is_white_connected(self):
        """Check if all white cells form a connected component using BFS"""
        white_cells = self.get_white_cells()
        if not white_cells:
            return True
        
        # Start BFS from first white cell
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
        """Get all cells with clues"""
        return [cell for cell in self.all_cells() if cell.value is not None]

    def reset(self):
        """Reset all cell states"""
        for cell in self.all_cells():
            cell.is_black = False
            cell.is_dot = False
