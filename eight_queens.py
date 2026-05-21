# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import messagebox

N = 8
CELL = 60
LIGHT = "#f0d9b5"
DARK  = "#b58863"
CONFLICT_LIGHT = "#f4a261"
CONFLICT_DARK  = "#e07a40"
HINT_COLOR = "#a8d8a8"
QUEEN_OK   = "#4a90d9"

class EightQueens:
    def __init__(self, root):
        self.root = root
        self.root.title("Bài toán 8 Hậu")
        self.root.resizable(True, True)
        self.root.configure(bg="#2c2c2c")
        self.root.minsize(520, 620)

        # Căn giữa màn hình
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w, h = 560, 700
        self.root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

        self.queens = [-1] * N  # queens[col] = row, -1 nếu chưa đặt
        self._transient_conflicts = set()
        self._conflict_after_id = None
        self._hint_after_id = None
        self._all_solutions = self._find_all_solutions()  # 92 lời giải
        self._solution_idx = -1

        self._build_ui()
        self._draw_board()
        self._update_status()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        # Scrollable outer container
        outer = tk.Frame(self.root, bg="#2c2c2c")
        outer.pack(fill="both", expand=True)

        vscroll = tk.Scrollbar(outer, orient="vertical")
        vscroll.pack(side="right", fill="y")

        self._scroll_canvas = tk.Canvas(outer, bg="#2c2c2c",
                                        highlightthickness=0,
                                        yscrollcommand=vscroll.set)
        self._scroll_canvas.pack(side="left", fill="both", expand=True)
        vscroll.config(command=self._scroll_canvas.yview)

        self._inner = tk.Frame(self._scroll_canvas, bg="#2c2c2c")
        self._inner_id = self._scroll_canvas.create_window(
            (0, 0), window=self._inner, anchor="n")

        self._inner.bind("<Configure>", self._on_frame_configure)
        self._scroll_canvas.bind("<Configure>", self._on_canvas_configure)
        self._scroll_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        C = self._inner  # alias ngắn cho container

        title = tk.Label(C, text="♛  Bài Toán 8 Hậu  ♛",
                         font=("Georgia", 18, "bold"), bg="#2c2c2c", fg="#f0d9b5", pady=10)
        title.pack()

        # Bàn cờ
        board_frame = tk.Frame(C, bg="#2c2c2c")
        board_frame.pack(padx=20)

        # Nhãn cột (a-h)
        col_frame = tk.Frame(board_frame, bg="#2c2c2c")
        col_frame.grid(row=0, column=1)
        for c in range(N):
            tk.Label(col_frame, text="abcdefgh"[c], width=4,
                     font=("Consolas", 11), bg="#2c2c2c", fg="#aaa").grid(row=0, column=c)

        # Nhãn hàng (8-1)
        for r in range(N):
            tk.Label(board_frame, text=str(8 - r), width=2,
                     font=("Consolas", 11), bg="#2c2c2c", fg="#aaa").grid(row=r + 1, column=0)

        self.canvas = tk.Canvas(board_frame,
                                width=N * CELL, height=N * CELL,
                                highlightthickness=0)
        self.canvas.grid(row=1, column=1, rowspan=N)
        self.canvas.bind("<Button-1>", self._on_click)

        # Thanh trạng thái
        self.msg_var = tk.StringVar(value="Nhấn vào ô để đặt hậu. Nhấn lại ô có hậu để xóa.")
        msg_frame = tk.Frame(C, bg="#3a3a3a", padx=10, pady=6)
        msg_frame.pack(fill="x", padx=20, pady=(8, 0))
        self.msg_label = tk.Label(msg_frame, textvariable=self.msg_var,
                                  font=("Segoe UI", 11), bg="#3a3a3a", fg="#ddd",
                                  wraplength=N * CELL, justify="left")
        self.msg_label.pack(fill="x")

        # Thống kê
        stat_frame = tk.Frame(C, bg="#2c2c2c", pady=6)
        stat_frame.pack()

        self.cnt_var  = tk.StringVar(value="0")
        self.rem_var  = tk.StringVar(value="8")
        self.conf_var = tk.StringVar(value="0")

        for label, var, col in [("Đã đặt", self.cnt_var, 0),
                                 ("Còn lại", self.rem_var, 1),
                                 ("Xung đột", self.conf_var, 2)]:
            box = tk.Frame(stat_frame, bg="#3a3a3a", padx=14, pady=6,
                           relief="flat", bd=0)
            box.grid(row=0, column=col, padx=5)
            tk.Label(box, text=label, font=("Segoe UI", 10),
                     bg="#3a3a3a", fg="#aaa").pack()
            tk.Label(box, textvariable=var, font=("Segoe UI", 18, "bold"),
                     bg="#3a3a3a", fg="#f0d9b5").pack()

        # Nút
        btn_frame = tk.Frame(C, bg="#2c2c2c", pady=10)
        btn_frame.pack()

        btn_style = dict(font=("Segoe UI", 11), relief="flat",
                         padx=14, pady=6, cursor="hand2", bd=0)

        tk.Button(btn_frame, text="🗑  Xóa tất cả",
                  bg="#555", fg="white", activebackground="#666",
                  command=self._clear, **btn_style).grid(row=0, column=0, padx=5)

        tk.Button(btn_frame, text="💡  Gợi ý",
                  bg="#3a7bd5", fg="white", activebackground="#4a8be5",
                  command=self._hint, **btn_style).grid(row=0, column=1, padx=5)

        tk.Button(btn_frame, text="✨  Tự giải",
                  bg="#27ae60", fg="white", activebackground="#2ecc71",
                  command=self._auto_solve, **btn_style).grid(row=0, column=2, padx=5)

    # ---------------------------------------------------------------- Vẽ
    def _draw_board(self):
        self.canvas.delete("all")
        conflicts = self._get_conflicts() | self._transient_conflicts

        for r in range(N):
            for c in range(N):
                x1, y1 = c * CELL, r * CELL
                x2, y2 = x1 + CELL, y1 + CELL

                is_light = (r + c) % 2 == 0
                key = r * N + c

                if key in conflicts:
                    color = CONFLICT_LIGHT if is_light else CONFLICT_DARK
                else:
                    color = LIGHT if is_light else DARK

                self.canvas.create_rectangle(x1, y1, x2, y2,
                                             fill=color, outline="")

                if self.queens[c] == r:
                    # Vẽ nền tròn cho quân hậu
                    pad = 8
                    self.canvas.create_oval(x1 + pad, y1 + pad, x2 - pad, y2 - pad,
                                            fill=QUEEN_OK if key not in conflicts else "#e74c3c",
                                            outline="")
                    self.canvas.create_text(x1 + CELL // 2, y1 + CELL // 2,
                                            text="♛",
                                            font=("Segoe UI", 26),
                                            fill="white")

    # ----------------------------------------------------------- Logic
    def _get_conflicts(self):
        conflict = set()
        placed = [(self.queens[c], c) for c in range(N) if self.queens[c] != -1]
        for i in range(len(placed)):
            for j in range(i + 1, len(placed)):
                r1, c1 = placed[i]
                r2, c2 = placed[j]
                if r1 == r2 or c1 == c2 or abs(r1 - r2) == abs(c1 - c2):
                    conflict.add(r1 * N + c1)
                    conflict.add(r2 * N + c2)
        return conflict

    def _get_attackers(self, row, col):
        attackers = {row * N + col}
        for c in range(N):
            if c == col or self.queens[c] == -1:
                continue
            r = self.queens[c]
            if r == row or abs(r - row) == abs(c - col):
                attackers.add(r * N + c)
        return attackers

    def _is_safe(self, row, col):
        for c in range(N):
            if c == col or self.queens[c] == -1:
                continue
            r = self.queens[c]
            if r == row or abs(r - row) == abs(c - col):
                return False
        return True

    def _on_click(self, event):
        c = event.x // CELL
        r = event.y // CELL
        if not (0 <= r < N and 0 <= c < N):
            return

        self._clear_transient_conflicts(redraw=False)
        self.canvas.delete("hint")
        pos_name = "abcdefgh"[c] + str(8 - r)

        if self.queens[c] == r:
            # Xóa hậu
            self.queens[c] = -1
            self._set_msg(f"Đã xóa hậu tại {pos_name}.", "normal")
        elif not self._is_safe(r, c):
            # Xung đột
            self._set_msg(
                f"❌  Vị trí {pos_name} xung đột! "
                "Hậu này tấn công hậu khác trên cùng hàng, cột hoặc đường chéo. "
                "Hãy chọn ô khác.", "error")
            self._show_transient_conflicts(r, c)
            self._shake()
            return
        else:
            if self.queens[c] != -1:
                # Đã có hậu ở cột này, di chuyển
                self.queens[c] = r
                self._set_msg(f"Di chuyển hậu đến {pos_name}.", "ok")
            else:
                self.queens[c] = r
                self._set_msg(f"✔  Đặt hậu tại {pos_name}.", "ok")

        self._draw_board()
        self._update_status()
        self._check_win()

    def _check_win(self):
        placed = sum(1 for q in self.queens if q != -1)
        if placed == 8 and not self._get_conflicts():
            self._set_msg("🎉  Xuất sắc! Bạn đã giải thành công bài toán 8 hậu!", "win")
            messagebox.showinfo("Thành công!",
                                "🎉 Chúc mừng!\n\nBạn đã giải thành công bài toán 8 Hậu!\n"
                                "Tất cả 8 quân hậu đã được đặt đúng vị trí.")

    def _set_msg(self, text, kind="normal"):
        colors = {
            "normal": ("#ddd",    "#3a3a3a"),
            "ok":     ("#c8f7c5", "#1a4a1a"),
            "error":  ("#fcc",    "#4a1a1a"),
            "win":    ("#ffe58f", "#3a2a00"),
        }
        fg, bg = colors.get(kind, colors["normal"])
        self.msg_var.set(text)
        self.msg_label.config(fg=fg, bg=bg)
        self.msg_label.master.config(bg=bg)

    def _update_status(self):
        placed = sum(1 for q in self.queens if q != -1)
        confl  = len(self._get_conflicts() | self._transient_conflicts)
        self.cnt_var.set(str(placed))
        self.rem_var.set(str(8 - placed))
        self.conf_var.set(str(confl))

    def _clear(self):
        self.queens = [-1] * N
        self._solution_idx = -1
        self._clear_transient_conflicts(redraw=False)
        self.canvas.delete("hint")
        self._set_msg("Đã xóa bàn cờ. Hãy bắt đầu lại!", "normal")
        self._draw_board()
        self._update_status()

    def _hint(self):
        """Làm nổi bật các ô hợp lệ trong cột chưa có hậu đầu tiên."""
        self._clear_transient_conflicts()
        self.canvas.delete("hint")
        if self._hint_after_id is not None:
            self.root.after_cancel(self._hint_after_id)
            self._hint_after_id = None

        for c in range(N):
            if self.queens[c] == -1:
                safe_rows = [r for r in range(N) if self._is_safe(r, c)]
                if not safe_rows:
                    self._set_msg(
                        f"Cột {'abcdefgh'[c]} không còn vị trí hợp lệ. "
                        "Hãy xóa hoặc di chuyển một hậu trước đó.", "error")
                    return

                for r in safe_rows:
                    x1, y1 = c * CELL + 6, r * CELL + 6
                    x2, y2 = (c + 1) * CELL - 6, (r + 1) * CELL - 6
                    self.canvas.create_rectangle(x1, y1, x2, y2,
                                                 fill=HINT_COLOR,
                                                 outline="#3a9a3a",
                                                 width=2,
                                                 tags="hint")
                self._set_msg(
                    f"💡  Ô xanh = vị trí hợp lệ cho cột {'abcdefgh'[c]}. "
                    "Nhấn bất kỳ ô nào để tiếp tục.", "ok")
                self._hint_after_id = self.root.after(2000, self._clear_hints)
                break
        else:
            self._set_msg("Tất cả các cột đã có hậu!", "normal")

    def _find_all_solutions(self):
        """Tìm tất cả 92 lời giải bằng backtracking."""
        solutions = []
        placement = [-1] * N
        used_rows = set()
        used_diag_down = set()  # row - col
        used_diag_up = set()    # row + col

        def solve(col):
            if col == N:
                solutions.append(placement[:])
                return
            for row in range(N):
                diag_down = row - col
                diag_up = row + col
                if (row in used_rows or
                        diag_down in used_diag_down or
                        diag_up in used_diag_up):
                    continue

                placement[col] = row
                used_rows.add(row)
                used_diag_down.add(diag_down)
                used_diag_up.add(diag_up)
                solve(col + 1)
                used_diag_up.remove(diag_up)
                used_diag_down.remove(diag_down)
                used_rows.remove(row)
                placement[col] = -1

        solve(0)
        return solutions

    def _auto_solve(self):
        total = len(self._all_solutions)
        if total == 0:
            self._set_msg("Không tìm thấy lời giải nào.", "error")
            return
        self._clear_transient_conflicts(redraw=False)
        self.canvas.delete("hint")
        self._solution_idx = (self._solution_idx + 1) % total
        self.queens = self._all_solutions[self._solution_idx][:]
        self._set_msg(
            f"✨  Lời giải {self._solution_idx + 1} / {total}  —  "
            "Nhấn lại để xem lời giải tiếp theo.", "win")
        self._draw_board()
        self._update_status()

    def _on_frame_configure(self, event=None):
        self._scroll_canvas.configure(
            scrollregion=self._scroll_canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self._scroll_canvas.itemconfig(self._inner_id, width=event.width)

    def _on_mousewheel(self, event):
        self._scroll_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _clear_hints(self):
        self.canvas.delete("hint")
        self._hint_after_id = None

    def _show_transient_conflicts(self, row, col):
        if self._conflict_after_id is not None:
            self.root.after_cancel(self._conflict_after_id)

        self._transient_conflicts = self._get_attackers(row, col)
        self._draw_board()
        self._update_status()
        self._conflict_after_id = self.root.after(
            1200, lambda: self._clear_transient_conflicts(cancel_timer=False))

    def _clear_transient_conflicts(self, redraw=True, cancel_timer=True):
        if cancel_timer and self._conflict_after_id is not None:
            self.root.after_cancel(self._conflict_after_id)
        self._conflict_after_id = None

        if not self._transient_conflicts:
            return

        self._transient_conflicts = set()
        if redraw:
            self._draw_board()
            self._update_status()

    def _shake(self):
        """Hiệu ứng nhấp nháy viền đỏ khi đặt sai (không dùng place để tránh phá layout)."""
        steps = ["#e74c3c", "#2c2c2c", "#e74c3c", "#2c2c2c", "#e74c3c", "#2c2c2c"]
        def flash(i=0):
            if i < len(steps):
                self.canvas.config(highlightthickness=3 if i % 2 == 0 else 0,
                                   highlightbackground=steps[i])
                self.root.after(80, lambda: flash(i + 1))
            else:
                self.canvas.config(highlightthickness=0)
        flash()


# ------------------------------------------------------------------ Main
if __name__ == "__main__":
    root = tk.Tk()
    app = EightQueens(root)
    root.mainloop()
