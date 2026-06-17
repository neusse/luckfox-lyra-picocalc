import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))


class SudokuModelTests(unittest.TestCase):
    def test_finds_row_column_and_box_conflicts(self):
        from picogames.sudoku import compute_conflict_cells

        grid = [[0 for _ in range(9)] for _ in range(9)]
        grid[0][0] = grid[0][4] = 7
        grid[1][1] = grid[8][1] = 4
        grid[3][3] = grid[5][5] = 9

        conflicts = compute_conflict_cells(grid)

        self.assertEqual(
            conflicts,
            {(0, 0), (0, 4), (1, 1), (8, 1), (3, 3), (5, 5)},
        )

    def test_givens_cannot_be_changed(self):
        from picogames.sudoku import SudokuGame

        game = SudokuGame("easy")
        game.grid[0][0] = 8
        game.given[0][0] = True

        changed = game.set_cell(0, 0, 1)

        self.assertFalse(changed)
        self.assertEqual(game.grid[0][0], 8)

    def test_user_cells_can_be_set_and_cleared(self):
        from picogames.sudoku import SudokuGame

        game = SudokuGame("medium")

        self.assertTrue(game.set_cell(2, 3, 6))
        self.assertEqual(game.grid[2][3], 6)
        self.assertTrue(game.clear_cell(2, 3))
        self.assertEqual(game.grid[2][3], 0)

    def test_state_round_trip_keeps_board_cursor_and_elapsed(self):
        from picogames.sudoku import SudokuGame

        game = SudokuGame("hard")
        game.grid[4][4] = 5
        game.given[4][4] = True
        game.cursor_row = 4
        game.cursor_col = 4
        game.set_elapsed(123)

        restored = SudokuGame.from_state(game.to_state())

        self.assertEqual(restored.difficulty, "hard")
        self.assertEqual(restored.grid[4][4], 5)
        self.assertTrue(restored.given[4][4])
        self.assertEqual((restored.cursor_row, restored.cursor_col), (4, 4))
        self.assertGreaterEqual(restored.elapsed_seconds(), 123)


if __name__ == "__main__":
    unittest.main()
