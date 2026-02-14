# ============================================================================
# FILE 8: main.py
# ============================================================================
# main.py - Range Puzzle Game (Simon Tatham's Puzzles style)

import tkinter as tk
from graph import GridGraph
from gui import RangeGUI
from generator import PuzzleGenerator

def main():
    root = tk.Tk()
    root.title("Range Puzzle - DAA Project")
    root.resizable(False, False)

    # Initialize puzzle generator
    generator = PuzzleGenerator(size=8, difficulty='medium')
    
    # Generate initial puzzle
    graph, clues = generator.generate()

    # Create GUI with generator
    RangeGUI(root, graph, clues, generator)
    root.mainloop()

if __name__ == "__main__":
    main()
