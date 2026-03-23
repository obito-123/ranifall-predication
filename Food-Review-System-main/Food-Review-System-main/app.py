
import customtkinter as ctk
from PIL import Image
import sqlite3
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from tkinter import messagebox, ttk
import os

# ---------------- SETUP ----------------
ctk.set_appearance_mode("light")

try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon')

FOOD_ITEMS = [
    'Idli', 'Dosa', 'Vada', 'Roti',
    'Veg Biryani', 'Mutton Biryani',
    'Ice Cream', 'Noodles'
]

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect('restaurant_feedback.db')
    conn.execute(
        '''CREATE TABLE IF NOT EXISTS reviews
        (id INTEGER PRIMARY KEY,
        item TEXT,
        review TEXT,
        sentiment TEXT)'''
    )
    conn.commit()
    conn.close()


def analyze_sentiment(text):
    sia = SentimentIntensityAnalyzer()
    score = sia.polarity_scores(text)

    if score['compound'] >= 0.05:
        return "Positive"
    elif score['compound'] <= -0.05:
        return "Negative"
    else:
        return "Neutral"


# ---------------- OWNER DASHBOARD ----------------
class OwnerDashboard(ctk.CTkToplevel):

    def __init__(self, master):
        super().__init__(master)

        self.title("Admin Insights")
        self.geometry("900x600")

        banner = ctk.CTkFrame(self, fg_color="#1e293b", height=100)
        banner.pack(fill="x")

        ctk.CTkLabel(
            banner,
            text="Restaurant Analytics Dashboard",
            font=("Segoe UI", 24, "bold"),
            text_color="white"
        ).pack(pady=30)

        content = ctk.CTkFrame(self)
        content.pack(fill="both", expand=True, padx=30, pady=30)

        style = ttk.Style()
        style.theme_use("clam")

        self.tree = ttk.Treeview(
            content,
            columns=("Item", "Pos", "Neu", "Neg"),
            show="headings"
        )

        self.tree.heading("Item", text="Dish Name")
        self.tree.heading("Pos", text="Positive")
        self.tree.heading("Neu", text="Neutral")
        self.tree.heading("Neg", text="Negative")

        self.tree.column("Item", width=250)

        for col in ["Pos", "Neu", "Neg"]:
            self.tree.column(col, anchor="center", width=120)

        self.tree.pack(fill="both", expand=True)

        ctrl = ctk.CTkFrame(self)
        ctrl.pack(pady=20)

        ctk.CTkButton(ctrl, text="Update Stats",
                      command=self.refresh).grid(row=0, column=0, padx=10)

        ctk.CTkButton(ctrl, text="Clear Database",
                      fg_color="#ef4444",
                      command=self.clear).grid(row=0, column=1, padx=10)

        self.refresh()

    def refresh(self):

        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = sqlite3.connect('restaurant_feedback.db')
        cursor = conn.cursor()

        for item in FOOD_ITEMS:

            cursor.execute(
                "SELECT sentiment, COUNT(*) FROM reviews WHERE item=? GROUP BY sentiment",
                (item,)
            )

            counts = dict(cursor.fetchall())

            pos = counts.get('Positive', 0)
            neu = counts.get('Neutral', 0)
            neg = counts.get('Negative', 0)

            if pos or neu or neg:
                self.tree.insert("", "end",
                                 values=(item, pos, neu, neg))

        conn.close()

    def clear(self):

        if messagebox.askyesno("Confirm", "Delete all records?"):

            conn = sqlite3.connect('restaurant_feedback.db')
            conn.execute("DELETE FROM reviews")
            conn.commit()
            conn.close()

            self.refresh()


# ---------------- MAIN APP ----------------
class FoodReviewAI(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Food Review AI")
        self.geometry("1000x700")

        # -------- BACKGROUND IMAGE --------
        script_dir = os.path.dirname(os.path.abspath(__file__))

        found_image = None
        for file in os.listdir(script_dir):
            if file.lower().startswith("background") and file.lower().endswith(
                    (".jpg", ".jpeg", ".png")):
                found_image = os.path.join(script_dir, file)
                break

        if found_image:

            raw = Image.open(found_image)

            self.bg_image = ctk.CTkImage(
                light_image=raw,
                dark_image=raw,
                size=(1000, 700)
            )

            bg_label = ctk.CTkLabel(self, image=self.bg_image, text="")
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            bg_label.lower()

        # -------- GLASS STYLE CARD --------
        self.card = ctk.CTkFrame(
            self,
            corner_radius=20,
            fg_color="#f2f2f2",
            border_width=1,
            border_color="#ffffff"
        )

        self.card.place(
            relx=0.5,
            rely=0.5,
            anchor="center",
            relwidth=0.32,
            relheight=0.65
        )

        self.setup_ui()

    # -------- UI --------
    def setup_ui(self):

        ctk.CTkLabel(
            self.card,
            text="🍴 Food Review AI",
            font=("Segoe UI", 24, "bold")
        ).pack(pady=(30, 5))

        ctk.CTkLabel(
            self.card,
            text="Smart Sentiment Analysis System",
            font=("Segoe UI", 11),
            text_color="gray"
        ).pack(pady=(0, 20))

        ctk.CTkLabel(
            self.card,
            text="Select Food",
            font=("Segoe UI", 12, "bold")
        ).pack(pady=(5, 2))

        self.food_var = ctk.StringVar(value=FOOD_ITEMS[0])

        self.combo = ctk.CTkComboBox(
            self.card,
            values=FOOD_ITEMS,
            variable=self.food_var,
            height=35,
            fg_color="#ffffff"
        )

        self.combo.pack(pady=5, padx=35, fill="x")

        ctk.CTkLabel(
            self.card,
            text="Your Review",
            font=("Segoe UI", 12, "bold")
        ).pack(pady=(15, 2))

        self.entry = ctk.CTkEntry(
            self.card,
            placeholder_text="Type your feedback...",
            height=40,
            fg_color="#ffffff"
        )

        self.entry.pack(pady=5, padx=35, fill="x")

        self.btn = ctk.CTkButton(
            self.card,
            text="Analyze Review",
            fg_color="#ff8a8a",
            hover_color="#ff7070",
            height=45,
            command=self.save
        )

        self.btn.pack(pady=(25, 10), padx=35, fill="x")

        self.dash_btn = ctk.CTkButton(
            self.card,
            text="Owner Dashboard",
            fg_color="transparent",
            text_color="#ff8a8a",
            hover=False,
            command=self.login
        )

        self.dash_btn.pack(pady=5)

    # -------- SAVE REVIEW --------
    def save(self):

        food = self.food_var.get()
        text = self.entry.get().strip()

        if text:

            sent = analyze_sentiment(text)

            conn = sqlite3.connect('restaurant_feedback.db')

            conn.execute(
                "INSERT INTO reviews (item, review, sentiment) VALUES (?, ?, ?)",
                (food, text, sent)
            )

            conn.commit()
            conn.close()

            messagebox.showinfo(
                "Result",
                f"The review is {sent}!"
            )

            self.entry.delete(0, 'end')

    # -------- LOGIN --------
    def login(self):

        pw = ctk.CTkInputDialog(
            text="Passcode:",
            title="Security"
        ).get_input()

        if pw == "1234":
            OwnerDashboard(self)


# ---------------- RUN ----------------
if __name__ == "__main__":
    init_db()
    app = FoodReviewAI()
    app.mainloop()

