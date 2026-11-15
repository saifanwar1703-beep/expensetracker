import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import date, datetime
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import database as db

WARN_AT = 0.8  # warn at 80% of budget


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Expense Tracker")
        self.geometry("760x540")
        db.init_db()
        self.build_form()
        self.build_table()
        self.build_footer()
        self.refresh()

    # ---------- UI ----------
    def build_form(self):
        form = ttk.Frame(self, padding=10)
        form.pack(fill="x")
        self.amount = tk.StringVar()
        self.category = tk.StringVar()
        self.desc = tk.StringVar()
        self.date = tk.StringVar(value=date.today().isoformat())
        fields = [("Amount", self.amount), ("Category", self.category),
                  ("Description", self.desc), ("Date", self.date)]
        for i, (label, var) in enumerate(fields):
            ttk.Label(form, text=label).grid(
                row=0, column=i, sticky="w", padx=4)
            ttk.Entry(form, textvariable=var, width=15).grid(
                row=1, column=i, padx=4)
        ttk.Button(form, text="Add", command=self.add).grid(
            row=1, column=4, padx=8)

    def build_table(self):
        cols = ("id", "date", "category", "amount", "description")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c.title())
            self.tree.column(c, width=50 if c == "id" else 120)
        self.tree.heading("id", text="#")
        self.tree.pack(fill="both", expand=True, padx=10)

    def build_footer(self):
        status = ttk.Frame(self, padding=10)
        status.pack(fill="x")
        self.budget_label = ttk.Label(status, text="")
        self.budget_label.grid(row=0, column=0, sticky="w")
        self.progress = ttk.Progressbar(status, length=250, maximum=100)
        self.progress.grid(row=0, column=1, padx=15)

        buttons = ttk.Frame(self, padding=(10, 0, 10, 10))
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Set budget",
                   command=self.set_budget).pack(side="left")
        ttk.Button(buttons, text="Chart", command=self.show_chart).pack(
            side="left", padx=5)
        ttk.Button(buttons, text="Top expenses",
                   command=self.show_top).pack(side="left")
        ttk.Button(buttons, text="Delete selected",
                   command=self.delete).pack(side="right")

    # ---------- actions ----------
    def add(self):
        try:
            amount = float(self.amount.get())
            if amount <= 0:
                raise ValueError
            exp_date = datetime.strptime(
                self.date.get().strip(), "%Y-%m-%d").date().isoformat()
        except ValueError:
            messagebox.showerror(
                "Invalid input", "Enter a positive amount and date as YYYY-MM-DD.")
            return
        category = self.category.get().strip() or "Other"
        month = exp_date[:7]
        before = db.monthly_total(month)
        db.add_expense(amount, category, self.desc.get().strip(), exp_date)
        self.amount.set("")
        self.category.set("")
        self.desc.set("")
        self.refresh()
        self.check_budget(month, before)

    def delete(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Delete", "Select a row first.")
            return
        expense_id = int(selected[0])  # real DB id stored as row iid
        db.delete_expense(expense_id)
        self.refresh()

    def set_budget(self):
        value = simpledialog.askfloat("Monthly budget", "Enter monthly budget:",
                                      parent=self, minvalue=1)
        if value:
            db.set_budget(value)
            self.refresh()

    def check_budget(self, month, before):
        budget = db.get_budget()
        if not budget:
            return
        after = db.monthly_total(month)
        pct = after / budget * 100
        if before < budget <= after:
            messagebox.showwarning("Over budget",
                                   f"You have exceeded your {month} budget of {budget:.2f}!")
        elif before < WARN_AT * budget <= after:
            messagebox.showwarning("Budget warning",
                                   f"You have used {pct:.0f}% of your {month} budget.")

    def show_chart(self):
        cats = db.total_by_category()
        months = db.monthly_totals()
        if not cats:
            messagebox.showinfo("Chart", "No expenses yet.")
            return
        win = tk.Toplevel(self)
        win.title("Spending overview")
        fig = Figure(figsize=(9, 4), dpi=100)

        ax1 = fig.add_subplot(121)
        ax1.pie([t for _, t in cats], labels=[c for c, _ in cats],
                autopct="%1.0f%%", startangle=90)
        ax1.set_title("By category")

        ax2 = fig.add_subplot(122)
        ax2.bar([m for m, _ in months], [t for _, t in months])
        ax2.set_title("By month")
        ax2.tick_params(axis="x", rotation=45)

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def show_top(self):
        month = date.today().strftime("%Y-%m")
        rows = db.top_expenses(5, month)  # use db.top_expenses(5) for all-time
        if not rows:
            messagebox.showinfo("Top expenses", "No expenses this month.")
            return
        win = tk.Toplevel(self)
        win.title(f"Top 5 expenses ({month})")
        cols = ("date", "category", "amount", "description")
        tree = ttk.Treeview(win, columns=cols,
                            show="headings", height=len(rows))
        for c in cols:
            tree.heading(c, text=c.title())
            tree.column(c, width=120)
        for amount, cat, desc, d in rows:
            tree.insert("", "end", values=(d, cat, f"{amount:.2f}", desc))
        tree.pack(padx=10, pady=10)

    # ---------- display ----------
    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for n, (id_, amount, cat, desc, d) in enumerate(db.get_all_expenses(), start=1):
            self.tree.insert("", "end", iid=str(id_),
                             values=(n, d, cat, f"{amount:.2f}", desc))
        self.update_budget_bar()

    def update_budget_bar(self):
        month = date.today().strftime("%Y-%m")
        spent = db.monthly_total(month)
        budget = db.get_budget()
        if not budget:
            self.budget_label.config(text=f"This month: {spent:.2f} | No budget set",
                                     foreground="")
            self.progress["value"] = 0
            return
        pct = spent / budget * 100
        self.progress["value"] = min(pct, 100)
        self.budget_label.config(
            text=f"This month: {spent:.2f} / {budget:.2f} ({pct:.0f}%)",
            foreground="red" if pct >= WARN_AT * 100 else "")


if __name__ == "__main__":
    App().mainloop()
