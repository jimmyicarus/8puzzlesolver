import tkinter as tk
from tkinter import ttk, messagebox
import time
import random

import importlib.util
import os

_spec = importlib.util.spec_from_file_location(
    "solver", os.path.join(os.path.dirname(os.path.abspath(__file__)), "8puzzlesolver.py")
)
solver = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(solver)

GOAL = [1, 2, 3, 4, 5, 6, 7, 8, 0]

TILE_SIZE = 100
FONT_TILE = ("Segoe UI", 28, "bold")
FONT_LABEL = ("Segoe UI", 11)
FONT_HEADER = ("Segoe UI", 13, "bold")
FONT_SMALL = ("Segoe UI", 9)

COLOR_BG = "#f5f5f0"
COLOR_TILE = "#4CAF50"
COLOR_TILE_MISPLACED = "#FF9800"
COLOR_TILE_TEXT = "#ffffff"
COLOR_BLANK = "#e0e0e0"
COLOR_ACCENT = "#2196F3"
COLOR_HEADER_BG = "#ffffff"


class PuzzleGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("8-Puzzle Solver A*, UCS, Greedy, BFS, DFS")
        self.root.configure(bg=COLOR_BG)
        self.root.resizable(False, False)

        self.state = [1, 2, 3, 4, 0, 6, 7, 5, 8]
        self.solving = False
        self.animation_speed = 400

        self._build_ui()
        self._draw_board()
        self._update_heuristics()

    def _build_ui(self):
        main_frame = tk.Frame(self.root, bg=COLOR_BG, padx=20, pady=20)
        main_frame.pack()

        left_frame = tk.Frame(main_frame, bg=COLOR_BG)
        left_frame.grid(row=0, column=0, sticky="n")

        right_frame = tk.Frame(main_frame, bg=COLOR_BG, padx=20)
        right_frame.grid(row=0, column=1, sticky="n")

        # --- Puzzle Board ---
        board_label = tk.Label(left_frame, text="Puzzle Board", font=FONT_HEADER, bg=COLOR_BG)
        board_label.pack(pady=(0, 8))

        self.canvas = tk.Canvas(
            left_frame, width=TILE_SIZE * 3 + 4, height=TILE_SIZE * 3 + 4,
            bg=COLOR_BLANK, highlightthickness=1, highlightbackground="#bbb"
        )
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self._on_tile_click)

        # --- Controls under board ---
        ctrl_frame = tk.Frame(left_frame, bg=COLOR_BG, pady=10)
        ctrl_frame.pack()

        self.btn_scramble = tk.Button(
            ctrl_frame, text="Scramble", font=FONT_LABEL,
            command=self._scramble, width=10, bg="#607D8B", fg="white",
            relief="flat", cursor="hand2"
        )
        self.btn_scramble.grid(row=0, column=0, padx=4)

        self.btn_reset = tk.Button(
            ctrl_frame, text="Reset", font=FONT_LABEL,
            command=self._reset, width=10, bg="#9E9E9E", fg="white",
            relief="flat", cursor="hand2"
        )
        self.btn_reset.grid(row=0, column=1, padx=4)

        # Speed slider
        speed_frame = tk.Frame(left_frame, bg=COLOR_BG)
        speed_frame.pack(pady=(5, 0))
        tk.Label(speed_frame, text="Animation Speed:", font=FONT_SMALL, bg=COLOR_BG).pack(side="left")
        self.speed_slider = tk.Scale(
            speed_frame, from_=50, to=1000, orient="horizontal",
            length=150, bg=COLOR_BG, highlightthickness=0,
            command=self._update_speed
        )
        self.speed_slider.set(400)
        self.speed_slider.pack(side="left", padx=5)
        tk.Label(speed_frame, text="ms", font=FONT_SMALL, bg=COLOR_BG).pack(side="left")

        # --- Right Panel: Heuristics ---
        heur_label = tk.Label(right_frame, text="Heuristic Values", font=FONT_HEADER, bg=COLOR_BG)
        heur_label.grid(row=0, column=0, columnspan=2, pady=(0, 8), sticky="w")

        self.heur_vars = {}
        heuristics = [
            ("h1 Misplaced Tiles", "h1", "#FF9800"),
            ("h2 Manhattan Distance", "h2", COLOR_ACCENT),
            ("h3 Linear Conflict", "h3", COLOR_TILE),
        ]
        for i, (label, key, color) in enumerate(heuristics):
            tk.Label(right_frame, text=label, font=FONT_LABEL, bg=COLOR_BG).grid(
                row=i + 1, column=0, sticky="w", pady=2
            )
            var = tk.StringVar(value="0")
            self.heur_vars[key] = var
            lbl = tk.Label(right_frame, textvariable=var, font=("Segoe UI", 14, "bold"),
                           fg=color, bg=COLOR_BG, width=4)
            lbl.grid(row=i + 1, column=1, sticky="e", pady=2)

        # Dominance indicator
        self.dominance_var = tk.StringVar(value="")
        tk.Label(right_frame, textvariable=self.dominance_var, font=FONT_SMALL,
                 fg="#666", bg=COLOR_BG).grid(row=5, column=0, columnspan=2, sticky="w", pady=(4, 0))

        # --- Solve Buttons ---
        sep = ttk.Separator(right_frame, orient="horizontal")
        sep.grid(row=6, column=0, columnspan=2, sticky="ew", pady=12)

        solve_label = tk.Label(right_frame, text="Solve With", font=FONT_HEADER, bg=COLOR_BG)
        solve_label.grid(row=7, column=0, columnspan=2, sticky="w", pady=(0, 8))

        algorithms = [
            ("A* Search", self._solve_astar, "#4CAF50"),
            ("UCS", self._solve_ucs, "#2196F3"),
            ("Greedy BFS", self._solve_greedy, "#FF5722"),
            ("BFS", self._solve_bfs, "#00897B"),
            ("DFS", self._solve_dfs, "#795548"),
        ]
        for i, (name, cmd, color) in enumerate(algorithms):
            btn = tk.Button(
                right_frame, text=name, font=FONT_LABEL, command=cmd,
                width=14, bg=color, fg="white", relief="flat", cursor="hand2"
            )
            btn.grid(row=8 + i, column=0, columnspan=2, pady=3, sticky="ew")

        # --- DFS depth limit ---
        dfs_frame = tk.Frame(right_frame, bg=COLOR_BG)
        dfs_frame.grid(row=8 + len(algorithms), column=0, columnspan=2, sticky="ew", pady=(4, 0))
        tk.Label(dfs_frame, text="DFS depth limit:", font=FONT_SMALL, bg=COLOR_BG).pack(side="left")
        self.dfs_depth_var = tk.IntVar(value=50)
        tk.Spinbox(
            dfs_frame, from_=1, to=200, width=5, textvariable=self.dfs_depth_var,
            font=FONT_SMALL
        ).pack(side="left", padx=4)

        # --- Results ---
        sep2 = ttk.Separator(right_frame, orient="horizontal")
        sep2.grid(row=14, column=0, columnspan=2, sticky="ew", pady=12)

        results_label = tk.Label(right_frame, text="Results", font=FONT_HEADER, bg=COLOR_BG)
        results_label.grid(row=15, column=0, columnspan=2, sticky="w", pady=(0, 4))

        self.result_text = tk.Text(
            right_frame, width=36, height=14, font=("Consolas", 9),
            bg="#ffffff", relief="solid", borderwidth=1, wrap="word"
        )
        self.result_text.grid(row=16, column=0, columnspan=2, sticky="ew")

        # --- Benchmark Button ---
        self.btn_benchmark = tk.Button(
            right_frame, text="Run Benchmark (all algorithms)", font=FONT_LABEL,
            command=self._benchmark, bg="#9C27B0", fg="white", relief="flat", cursor="hand2"
        )
        self.btn_benchmark.grid(row=17, column=0, columnspan=2, pady=(10, 0), sticky="ew")

    def _draw_board(self):
        self.canvas.delete("all")
        for i in range(9):
            row, col = divmod(i, 3)
            x = col * TILE_SIZE + 2
            y = row * TILE_SIZE + 2
            tile = self.state[i]

            if tile == 0:
                self.canvas.create_rectangle(
                    x, y, x + TILE_SIZE, y + TILE_SIZE,
                    fill=COLOR_BLANK, outline="#ccc", width=1
                )
            else:
                goal_pos = GOAL.index(tile)
                is_correct = (i == goal_pos)
                color = COLOR_TILE if is_correct else COLOR_TILE_MISPLACED

                self.canvas.create_rectangle(
                    x + 2, y + 2, x + TILE_SIZE - 2, y + TILE_SIZE - 2,
                    fill=color, outline="", width=0
                )
                self.canvas.create_text(
                    x + TILE_SIZE // 2, y + TILE_SIZE // 2,
                    text=str(tile), font=FONT_TILE, fill=COLOR_TILE_TEXT
                )

    def _update_heuristics(self):
        h1 = solver.h_misplaced(self.state)
        h2 = solver.h_manhattan(self.state)
        h3 = solver.h_linear_conflict(self.state)
        self.heur_vars["h1"].set(str(h1))
        self.heur_vars["h2"].set(str(h2))
        self.heur_vars["h3"].set(str(h3))

        if h3 >= h2 >= h1 >= 0:
            self.dominance_var.set(f"h3({h3}) >= h2({h2}) >= h1({h1}) >= 0  ✓ dominance holds")
        else:
            self.dominance_var.set("⚠ dominance violation!")

    def _on_tile_click(self, event):
        if self.solving:
            return
        col = (event.x - 2) // TILE_SIZE
        row = (event.y - 2) // TILE_SIZE
        if not (0 <= row < 3 and 0 <= col < 3):
            return

        idx = row * 3 + col
        blank_idx = self.state.index(0)
        blank_row, blank_col = divmod(blank_idx, 3)

        if (abs(row - blank_row) + abs(col - blank_col)) == 1:
            self.state[blank_idx], self.state[idx] = self.state[idx], self.state[blank_idx]
            self._draw_board()
            self._update_heuristics()

    def _scramble(self):
        if self.solving:
            return
        state = GOAL[:]
        for _ in range(100):
            neighbors = solver.get_neighbors(state)
            _, state = random.choice(neighbors)
        self.state = state
        self._draw_board()
        self._update_heuristics()

    def _reset(self):
        if self.solving:
            return
        self.state = GOAL[:]
        self._draw_board()
        self._update_heuristics()

    def _update_speed(self, val):
        self.animation_speed = int(val)

    def _log(self, text):
        self.result_text.insert("end", text + "\n")
        self.result_text.see("end")

    def _clear_log(self):
        self.result_text.delete("1.0", "end")

    def _solve_astar(self):
        self._run_solver("A*", "Astar")

    def _solve_ucs(self):
        self._run_solver("UCS", "UCS")

    def _solve_greedy(self):
        self._run_solver("Greedy BFS", "Greedy")

    def _solve_bfs(self):
        self._run_solver("BFS", "BFS")

    def _solve_dfs(self):
        self._run_solver("DFS", "DFS", method_args=(self.dfs_depth_var.get(),))

    def _run_solver(self, name, method, method_args=()):
        if self.solving:
            return
        if self.state == GOAL:
            messagebox.showinfo("Already Solved", "The puzzle is already in the goal state!")
            return

        self.solving = True
        self._clear_log()
        self._log(f"Running {name}...")

        start_state = self.state[:]
        s = solver.SearchAlgorithms(start_state, GOAL)

        t0 = time.perf_counter()
        path, full_path, cost = getattr(s, method)(*method_args)
        elapsed = time.perf_counter() - t0

        if cost == -1:
            self._log("No solution found!")
            if method == "DFS":
                self._log("Try increasing the DFS depth limit.")
            self.solving = False
            return

        self._log(f"Solution found in {elapsed*1000:.1f} ms")
        self._log(f"Path cost: {cost}")
        self._log(f"Moves: {' -> '.join(path)}")
        self._log(f"States explored: {len(full_path)}")
        self._log("")
        self._log("Animating solution...")

        self._animate_solution(full_path, 0)

    def _animate_solution(self, full_path, idx):
        if idx >= len(full_path):
            self.solving = False
            self._log("Done!")
            return

        self.state = full_path[idx][:]
        self._draw_board()
        self._update_heuristics()
        self.root.after(self.animation_speed, self._animate_solution, full_path, idx + 1)

    def _benchmark(self):
        if self.solving:
            return
        if self.state == GOAL:
            messagebox.showinfo("Already Solved", "Scramble the puzzle first!")
            return

        self.solving = True
        self._clear_log()
        self._log("=" * 36)
        self._log("  BENCHMARK Current Puzzle State")
        self._log("=" * 36)
        self._log("")

        start_state = self.state[:]

        dfs_limit = self.dfs_depth_var.get()
        results = []
        algos = [
            ("A* (Manhattan)",      "Astar",  ()),
            ("UCS",                 "UCS",    ()),
            ("Greedy (Manhattan)",  "Greedy", ()),
            ("BFS",                 "BFS",    ()),
            (f"DFS (limit={dfs_limit})", "DFS", (dfs_limit,)),
        ]
        for name, method, args in algos:
            s = solver.SearchAlgorithms(start_state[:], GOAL)
            t0 = time.perf_counter()
            path, full_path, cost = getattr(s, method)(*args)
            elapsed = time.perf_counter() - t0
            results.append((name, path, full_path, cost, elapsed))

        for name, path, full_path, cost, elapsed in results:
            self._log(f"  {name}")
            if cost == -1:
                self._log(f"    No solution found within limits.")
                self._log(f"    Time:   {elapsed*1000:.2f} ms")
            else:
                self._log(f"    Cost:   {cost}")
                self._log(f"    Moves:  {len(path)}")
                self._log(f"    Time:   {elapsed*1000:.2f} ms")
                self._log(f"    Path:   {' -> '.join(path[:7])}")
                if len(path) > 8:
                    self._log(f"            ... ({len(path)} total moves)")
            self._log("")

        self._log("-" * 36)
        self._log("  h1 (Misplaced):   " + self.heur_vars["h1"].get())
        self._log("  h2 (Manhattan):   " + self.heur_vars["h2"].get())
        self._log("  h3 (Lin.Conflict):" + self.heur_vars["h3"].get())
        self._log("-" * 36)

        self.solving = False


def main():
    root = tk.Tk()
    app = PuzzleGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
