import random
import time
import tkinter as tk
from tkinter import messagebox
import threading
import os
import sys

# Try to import pygame for custom audio support
try:
    import pygame
    pygame.mixer.init()
    PYGAME_AVAILABLE = True
except:
    messagebox.showerror("Missing Dependency", 
                         "pygame is not installed.\n\n"
                         "Please install it with:\n"
                         "pip install pygame")
    sys.exit(1)

class ConcentrationGame:
    def __init__(self, rows=4, cols=6):
        self.rows = rows
        self.cols = cols
        self.total_pairs = (rows * cols) // 2
        self.cards = self._create_deck()
        self.revealed = set()
        self.matched = set()
        self.start_time = None
        self.moves = 0
        self.matches = 0
        self.adjusted_moves = 0
        self.adjusted_matches = 0
        self.selected_cards = []
    def _create_deck(self):
        deck = list(range(1, self.total_pairs + 1)) * 2
        random.shuffle(deck)
        return deck

    def is_complete(self):
        return len(self.matched) == self.rows * self.cols

    def get_stats(self):
        elapsed_time = time.time() - self.start_time if self.start_time else 0
        accuracy = (self.matches / self.moves * 100) if self.moves > 0 else 0
        adjusted_accuracy = (
            self.adjusted_matches / self.adjusted_moves * 100
            if self.adjusted_moves > 0 else 0
        )
        return {
            "time": round(elapsed_time, 2),
            "moves": self.moves,
            "matches": self.matches,
            "accuracy": round(accuracy, 2),
            "adjusted_accuracy": round(adjusted_accuracy, 2)
        }

    def start(self):
        self.start_time = time.time()


class ConcentrationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Concentration Game")
        self.root.configure(bg="#2c3e50")
        
        self.game = ConcentrationGame(4, 6)
        self.buttons = []
        self.selected_cards = []
        self.pending_check = None
        self.pending_pair_sound_played = False
        self.previously_revealed = set()
        self.audio_only_mode = False
        
        # Load custom audio files if available
        self.load_audio_files()
        
        self.setup_ui()
        self.update_stats()

    def load_audio_files(self):
        """Load custom audio files from the same directory as the script (REQUIRED)"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Define required audio files
        required_files = {
            'click.wav': 'click_sound',
            'correct.wav': 'correct_sound',
            'wrong.wav': 'wrong_sound'
        }
        
        missing_files = []
        
        # Check and load each required file
        for filename, attr_name in required_files.items():
            filepath = os.path.join(script_dir, filename)
            
            if not os.path.exists(filepath):
                missing_files.append(filename)
                setattr(self, attr_name, None)
            else:
                try:
                    sound = pygame.mixer.Sound(filepath)
                    if attr_name == 'click_sound':
                        sound.set_volume(0.35)
                    setattr(self, attr_name, sound)
                except Exception as e:
                    messagebox.showerror("Audio File Error",
                                         f"Failed to load {filename}:\n{str(e)}")
                    sys.exit(1)
        
        # Exit if any files are missing
        if missing_files:
            missing_list = '\n'.join(f'  - {f}' for f in missing_files)
            messagebox.showerror("Missing Audio Files",
                                 f"The following audio files are required but not found:\n\n"
                                 f"{missing_list}\n\n"
                                 f"Please place these files in:\n"
                                 f"{script_dir}")
            sys.exit(1)
    
    def setup_ui(self):
        # Stats frame
        stats_frame = tk.Frame(self.root, bg="#34495e", pady=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.moves_label = tk.Label(stats_frame, text="Moves: 0", 
                                     font=("Arial", 12, "bold"), 
                                     bg="#34495e", fg="white")
        self.moves_label.pack(side=tk.LEFT, padx=20)
        
        self.matches_label = tk.Label(stats_frame, text="Matches: 0", 
                                       font=("Arial", 12, "bold"), 
                                       bg="#34495e", fg="white")
        self.matches_label.pack(side=tk.LEFT, padx=20)

        # Temporary debug metrics for adjusted accuracy inputs
        self.adjusted_pairs_label = tk.Label(stats_frame, text="Adjusted Pairs: 0",
                             font=("Arial", 12, "bold"),
                             bg="#34495e", fg="white")
        self.adjusted_pairs_label.pack(side=tk.LEFT, padx=20)

        self.adjusted_matches_label = tk.Label(stats_frame, text="Adjusted Matches: 0",
                               font=("Arial", 12, "bold"),
                               bg="#34495e", fg="white")
        self.adjusted_matches_label.pack(side=tk.LEFT, padx=20)
        
        self.time_label = tk.Label(stats_frame, text="Time: 0.0s", 
                                    font=("Arial", 12, "bold"), 
                                    bg="#34495e", fg="white")
        self.time_label.pack(side=tk.LEFT, padx=20)
        
        # New Game button
        new_game_btn = tk.Button(stats_frame, text="New Game", 
                                  command=self.new_game,
                                  font=("Arial", 10, "bold"),
                                  bg="#27ae60", highlightbackground="#3498db", fg="white",
                                  relief=tk.RAISED, bd=3)
        new_game_btn.pack(side=tk.RIGHT, padx=20)
        
        # Audio mode toggle
        self.audio_mode_var = tk.BooleanVar(value=False)
        audio_check = tk.Checkbutton(stats_frame, text="Audio Feedback Only",
                                      variable=self.audio_mode_var,
                                      command=self.toggle_audio_mode,
                                      font=("Arial", 10, "bold"),
                                      bg="#34495e", fg="white",
                                      selectcolor="#2c3e50",
                                      activebackground="#34495e",
                                      activeforeground="white")
        audio_check.pack(side=tk.RIGHT, padx=10)
        
        # Cards frame
        cards_frame = tk.Frame(self.root, bg="#2c3e50")
        cards_frame.pack(pady=10, padx=10)
        
        # Create card buttons
        for i in range(self.game.rows):
            for j in range(self.game.cols):
                idx = i * self.game.cols + j
                btn = tk.Button(cards_frame, text="?", 
                                font=("Arial", 24, "bold"),
                                width=5, height=2,
                                bg="#3498db", fg="black",
                                highlightbackground="#3498db",
                                activebackground="#2980b9",
                                relief=tk.RAISED, bd=5,
                                command=lambda x=idx: self.card_clicked(x))
                btn.grid(row=i, column=j, padx=5, pady=5)
                self.buttons.append(btn)
        
        # Update timer every 100ms
        self.update_timer()

    def card_clicked(self, index):
        # Start timer on first card click
        if self.game.start_time is None:
            self.game.start()
        
        # Ignore if already matched or already selected
        if index in self.game.matched or index in self.selected_cards:
            return
        
        # If there's a pending pair, resolve it immediately
        if len(self.selected_cards) == 2:
            if self.pending_check:
                self.root.after_cancel(self.pending_check)
            self.check_match_now(play_sound=not self.pending_pair_sound_played)
        
        # Reveal the card
        is_second_card = len(self.selected_cards) == 1
        adjusted_qualified_pair = is_second_card and (index in self.previously_revealed)

        self.selected_cards.append(index)
        
        # Play click sound for every valid card selection in audio mode
        if self.audio_only_mode:
            self.play_neutral_sound()
        
        if not self.audio_only_mode:
            self.buttons[index].config(text=str(self.game.cards[index]), 
                                        bg="#ecf0f1", highlightbackground="#ecf0f1", fg="black")
        else:
            self.buttons[index].config(text=str(self.game.cards[index]))

        # Track that this card has now been seen at least once.
        self.previously_revealed.add(index)
        
        # If two cards are selected, keep them revealed until the next click.
        # Auto-resolve only when this is the final pair so completion still triggers.
        if len(self.selected_cards) == 2:
            self.game.moves += 1
            self.update_stats()
            idx1, idx2 = self.selected_cards
            is_match = self.game.cards[idx1] == self.game.cards[idx2]

            if adjusted_qualified_pair:
                self.game.adjusted_moves += 1
                if is_match:
                    self.game.adjusted_matches += 1

            # In audio mode, give match feedback immediately on second selection,
            # but keep visual card resolution deferred until the next click.
            if self.audio_only_mode:
                self.pending_pair_sound_played = True
                if is_match:
                    self.play_correct_sound()
                else:
                    self.play_incorrect_sound()
            else:
                self.pending_pair_sound_played = False
            
            if is_match:
                self.check_match_now(play_sound=not self.pending_pair_sound_played)
            else:
                self.pending_check = self.root.after(
                    100,
                    lambda: self.check_match_now(play_sound=not self.pending_pair_sound_played)
                )

    def play_neutral_sound(self):
        """Play a click sound for first card selection"""
        if not self.audio_only_mode:
            return
        
        if self.click_sound:
            self.click_sound.play()
    
    def play_correct_sound(self):
        """Play a ding sound for correct matches"""
        if not self.audio_only_mode:
            return
        
        if self.correct_sound:
            self.correct_sound.play()
    
    def play_incorrect_sound(self):
        """Play a buzzer sound for incorrect matches"""
        if not self.audio_only_mode:
            return
        
        if self.wrong_sound:
            self.wrong_sound.play()
    
    def toggle_audio_mode(self):
        """Toggle audio feedback only mode"""
        self.audio_only_mode = self.audio_mode_var.get()
        # Reset all card colors to default if entering audio mode
        if self.audio_only_mode:
            for i, btn in enumerate(self.buttons):
                if i not in self.game.matched:
                    btn.config(bg="#3498db", highlightbackground="#3498db")
    
    def check_match_now(self, play_sound=True):
        if len(self.selected_cards) != 2:
            return
            
        idx1, idx2 = self.selected_cards
        self.pending_check = None
        
        if self.game.cards[idx1] == self.game.cards[idx2]:
            # Match found
            if play_sound:
                self.play_correct_sound()
            self.game.matched.add(idx1)
            self.game.matched.add(idx2)
            self.game.matches += 1
            if not self.audio_only_mode:
                self.buttons[idx1].config(bg="#27ae60", highlightbackground="#27ae60", state=tk.DISABLED)
                self.buttons[idx2].config(bg="#27ae60", highlightbackground="#27ae60", state=tk.DISABLED)
            else:
                self.buttons[idx1].config(state=tk.DISABLED)
                self.buttons[idx2].config(state=tk.DISABLED)
            
            # Check if game is complete
            if self.game.is_complete():
                self.game_complete()
        else:
            # No match, hide cards
            if not self.audio_only_mode:
                self.buttons[idx1].config(text=str(self.game.cards[idx1]), bg="#e74c3c", highlightbackground="#e74c3c")
                self.buttons[idx2].config(text=str(self.game.cards[idx2]), bg="#e74c3c", highlightbackground="#e74c3c")
                self.root.after(800, lambda: self._hide_cards(idx1, idx2))
            else:
                self.root.after(800, lambda: self._hide_cards(idx1, idx2))
                #self.buttons[idx1].config(text="?")
                #self.buttons[idx2].config(text="?")
        
        self.selected_cards = []
        self.pending_pair_sound_played = False
        self.update_stats()

    def _hide_cards(self, idx1, idx2):
        if idx1 not in self.game.matched:
            self.buttons[idx1].config(text="?", bg="#3498db", highlightbackground="#3498db")
        if idx2 not in self.game.matched:
            self.buttons[idx2].config(text="?", bg="#3498db", highlightbackground="#3498db")

    def update_stats(self):
        stats = self.game.get_stats()
        self.moves_label.config(text=f"Moves: {stats['moves']}")
        self.matches_label.config(text=f"Matches: {stats['matches']}")
        self.adjusted_pairs_label.config(text=f"Adjusted Pairs: {self.game.adjusted_moves}")
        self.adjusted_matches_label.config(text=f"Adjusted Matches: {self.game.adjusted_matches}")

    def update_timer(self):
        if self.game.start_time:
            elapsed = time.time() - self.game.start_time
            self.time_label.config(text=f"Time: {elapsed:.1f}s")
        self.root.after(100, self.update_timer)

    def game_complete(self):
        stats = self.game.get_stats()
        messagebox.showinfo("Congratulations! 🎉", 
                            f"You completed the game!\n\n"
                            f"Time: {stats['time']}s\n"
                            f"Moves: {stats['moves']}\n"
                            f"Accuracy: {stats['accuracy']}%\n"
                            f"Adjusted Accuracy: {stats['adjusted_accuracy']}%")

    def new_game(self):
        # Cancel any pending checks
        if self.pending_check:
            self.root.after_cancel(self.pending_check)
        
        # Reset game
        self.game = ConcentrationGame(4, 6)
        self.selected_cards = []
        self.pending_check = None
        self.pending_pair_sound_played = False
        self.previously_revealed = set()
        
        # Reset all buttons
        for i, btn in enumerate(self.buttons):
            btn.config(text="?", bg="#3498db", highlightbackground="#3498db", state=tk.NORMAL)
        
        self.update_stats()


def main():
    root = tk.Tk()
    app = ConcentrationGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
