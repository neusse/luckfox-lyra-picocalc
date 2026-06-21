import random
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))


class MinesweeperModelTests(unittest.TestCase):
    def test_first_reveal_places_mines_away_from_first_cell(self):
        from picogames.minesweeper import MinesweeperGame

        game = MinesweeperGame(width=8, height=8, mines=10, rng=random.Random(7))

        result = game.reveal(3, 4)

        self.assertNotEqual(game.grid[4][3], -1)
        self.assertEqual(game.count_mines(), 10)
        self.assertTrue(game.revealed[4][3])
        self.assertIn(result, {"revealed", "expanded"})

    def test_flagged_cells_do_not_reveal(self):
        from picogames.minesweeper import MinesweeperGame

        game = MinesweeperGame(width=4, height=4, mines=2, rng=random.Random(1))
        game.toggle_flag(1, 1)

        result = game.reveal(1, 1)

        self.assertEqual(result, "blocked")
        self.assertFalse(game.revealed[1][1])
        self.assertTrue(game.flagged[1][1])

    def test_revealing_mine_loses_and_reveals_all_mines(self):
        from picogames.minesweeper import MinesweeperGame

        game = MinesweeperGame(width=3, height=3, mines=1, rng=random.Random(1))
        game.grid = [
            [-1, 1, 0],
            [1, 1, 0],
            [0, 0, 0],
        ]
        game.mines_placed = True

        result = game.reveal(0, 0)

        self.assertEqual(result, "lost")
        self.assertTrue(game.lost)
        self.assertTrue(game.revealed[0][0])

    def test_win_detects_all_safe_cells_revealed(self):
        from picogames.minesweeper import MinesweeperGame

        game = MinesweeperGame(width=2, height=2, mines=1, rng=random.Random(1))
        game.grid = [[-1, 1], [1, 1]]
        game.mines_placed = True

        game.reveal(1, 0)
        game.reveal(0, 1)
        result = game.reveal(1, 1)

        self.assertEqual(result, "won")
        self.assertTrue(game.won)


if __name__ == "__main__":
    unittest.main()
