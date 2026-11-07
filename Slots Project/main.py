import tkinter as tk
from tkinter import simpledialog, messagebox
import random
import time
from PIL import Image, ImageTk  # pip install pillow

# Symbols + image mapping
symbols = {
    "cherry": "symbols/cherry.jpg",
    "lemon": "symbols/lemon.jpg",
    "grape": "symbols/grape.jpg",
    "bell": "symbols/bell.jpg",
    "seven": "symbols/seven.jpg",
    "diamond": "symbols/diamond.jpg",
    "bar": "symbols/bar.jpg",
    "wild": "symbols/wild.jpg",
    "scatter": "symbols/scatter.jpg"
}

WILD = "wild"
SCATTER = "scatter"

# Payouts (symbol : {3 in a row, 4 in a row, 5 in a row})
payouts = {
    "seven":   {3: 50, 4: 200, 5: 1000},
    "diamond": {3: 40, 4: 150, 5: 500},
    "bell":    {3: 30, 4: 100, 5: 300},
    "bar":     {3: 20, 4: 75,  5: 200},
    "cherry":  {3: 15, 4: 50,  5: 150},
    "lemon":   {3: 10, 4: 30,  5: 100},
    "grape":   {3: 5,  4: 20,  5: 80},
    WILD:      {3: 100, 4: 300, 5: 2000},  # Jackpot wilds
}

# Paylines (5x3 layout)
paylines = [
    [(0,0),(0,1),(0,2),(0,3),(0,4)], # Top row
    [(1,0),(1,1),(1,2),(1,3),(1,4)], # Middle row
    [(2,0),(2,1),(2,2),(2,3),(2,4)], # Bottom row
    [(0,0),(1,1),(2,2),(1,3),(0,4)], # V shape
    [(2,0),(1,1),(0,2),(1,3),(2,4)], # Inverted V
]

class SlotMachine:
    def __init__(self, root):
        self.root = root
        self.root.title("🎰 Casino Slot Machine 🎰")
        self.root.config(bg="darkgreen")

        # Starting balance
        self.balance = simpledialog.askinteger("Balance", "Enter your starting balance:", minvalue=50, maxvalue=10000)
        if not self.balance:
            self.balance = 500

        self.bet = 10
        self.free_spins = 0

        # UI
        self.balance_label = tk.Label(root, text=f"Balance: R{self.balance}", font=("Arial", 16, "bold"), bg="darkgreen", fg="white")
        self.balance_label.pack(pady=10)

        self.canvas = tk.Canvas(root, width=600, height=400, bg="black")
        self.canvas.pack()

        # Load images
        self.images = {name: ImageTk.PhotoImage(Image.open(path).resize((80,80))) for name, path in symbols.items()}

        # Display reels (3 rows x 5 columns)
        self.reels = [[self.canvas.create_image(100*c+60, 100*r+80, image=self.images["cherry"]) for c in range(5)] for r in range(3)]

        # Bet controls
        self.controls = tk.Frame(root, bg="darkgreen")
        self.controls.pack(pady=10)
        self.dec_btn = tk.Button(self.controls, text="Decrease Bet", command=self.decrease_bet)
        self.dec_btn.pack(side="left", padx=5)
        self.inc_btn = tk.Button(self.controls, text="Increase Bet", command=self.increase_bet)
        self.inc_btn.pack(side="left", padx=5)
        self.bet_label = tk.Label(self.controls, text=f"Bet: R{self.bet}", font=("Arial", 14), bg="darkgreen", fg="white")
        self.bet_label.pack(side="left", padx=10)

        self.spin_button = tk.Button(root, text="🎲 SPIN 🎲", font=("Arial", 18), command=self.spin, bg="gold", fg="black")
        self.spin_button.pack(pady=20)

        self.message_label = tk.Label(root, text="", font=("Arial", 14), bg="darkgreen", fg="white")
        self.message_label.pack(pady=10)

    def decrease_bet(self):
        if self.free_spins > 0:
            return  # Bet cannot change during free games
        if self.bet > 1:
            self.bet -= 1
            self.bet_label.config(text=f"Bet: R{self.bet}")

    def increase_bet(self):
        if self.free_spins > 0:
            return  # Bet cannot change during free games
        if self.bet < self.balance:
            self.bet += 1
            self.bet_label.config(text=f"Bet: R{self.bet}")

    def spin(self):
        if self.free_spins == 0:
            if self.bet > self.balance:
                self.message_label.config(text="❌ Not enough balance!", fg="red")
                return
            self.balance -= self.bet

        self.balance_label.config(text=f"Balance: R{self.balance}")
        self.message_label.config(text="Spinning...", fg="white")
        self.root.update()

        # Animate spin
        for _ in range(8):
            for r in range(3):
                for c in range(5):
                    sym = random.choice(list(symbols.keys()))
                    self.canvas.itemconfig(self.reels[r][c], image=self.images[sym])
            self.root.update()
            time.sleep(0.08)

        # Final grid with scatter rarity
        self.grid = [[self.random_symbol() for _ in range(5)] for _ in range(3)]
        for r in range(3):
            for c in range(5):
                self.canvas.itemconfig(self.reels[r][c], image=self.images[self.grid[r][c]])

        # Evaluate results
        winnings, details, scatters_triggered = self.check_payouts(self.grid)
        self.balance += winnings
        self.balance_label.config(text=f"Balance: R{self.balance}")

        # Message
        if winnings > 0:
            win_msg = " | ".join(details)
            self.message_label.config(text=f"🎉 {win_msg}", fg="gold")
        else:
            self.message_label.config(text="😢 No win!", fg="red")

        # Scatter free spins
        if scatters_triggered:
            self.free_spins += 10
            self.message_label.config(text=f"✨ 3+ Scatters! You won 10 Free Spins!", fg="cyan")

        # Free spins logic
        if self.free_spins > 0:
            self.free_spins -= 1
            self.message_label.config(text=f"🎁 Free Spin! ({self.free_spins} left)", fg="purple")

        # Out of money
        if self.balance <= 0 and self.free_spins == 0:
            messagebox.showinfo("Game Over", "You're out of money!")
            self.spin_button.config(state="disabled")

    def random_symbol(self):
        """Weighted random symbol to make scatters rarer."""
        roll = random.random()
        if roll < 0.07:   # ~7% chance scatter
            return SCATTER
        else:
            pool = [s for s in symbols.keys() if s != SCATTER]
            return random.choice(pool)

    def check_payouts(self, grid):
        winnings = 0
        details = []
        scatter_count = sum(grid[r][c] == SCATTER for r in range(3) for c in range(5))
        scatters_triggered = scatter_count >= 3

        # Scatter pays only if 3+
        if scatter_count >= 3:
            scatter_win = self.bet * scatter_count
            winnings += scatter_win
            details.append(f"Scatter x{scatter_count} = R{scatter_win}")

        # Clear old lines
        self.canvas.delete("line")

        # Check paylines
        for line in paylines:
            line_symbols = [grid[r][c] for (r,c) in line]

            # Left-to-right matching
            base = None
            count = 0
            for sym in line_symbols:
                if sym == WILD:
                    count += 1
                elif base is None:
                    base = sym
                    count += 1
                elif sym == base or sym == WILD:
                    count += 1
                else:
                    break

            if base and count >= 3 and base in payouts:
                payout = payouts[base][count] * self.bet // 10
                winnings += payout
                details.append(f"{base.capitalize()} x{count} = R{payout}")

                # Draw winning line
                coords = [(100*c+60, 100*r+80) for r,c in line]
                self.canvas.create_line(*[p for xy in coords for p in xy], fill="yellow", width=3, tags="line")

        return winnings, details, scatters_triggered


if __name__ == "__main__":
    root = tk.Tk()
    app = SlotMachine(root)
    root.mainloop()