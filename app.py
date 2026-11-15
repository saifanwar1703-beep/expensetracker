from datetime import date, datetime
from flask import Flask, render_template, request, redirect, url_for, flash
import database as db

app = Flask(__name__)
app.secret_key = "change-this-later"  # needed for flash messages
WARN_AT = 0.8

db.init_db()


@app.route("/")
def index():
    month = date.today().strftime("%Y-%m")
    spent = db.monthly_total(month)
    budget = db.get_budget()
    pct = round(spent / budget * 100) if budget else 0
    cats = db.total_by_category()
    months = db.monthly_totals()
    return render_template(
        "index.html",
        expenses=db.get_all_expenses(),
        today=date.today().isoformat(),
        month=month, spent=spent, budget=budget, pct=pct,
        top=db.top_expenses(5, month),
        cat_labels=[c for c, _ in cats],
        cat_values=[round(t, 2) for _, t in cats],
        month_labels=[m for m, _ in months],
        month_values=[round(t, 2) for _, t in months],
    )


@app.route("/add", methods=["POST"])
def add():
    try:
        amount = float(request.form["amount"])
        if amount <= 0:
            raise ValueError
        exp_date = datetime.strptime(
            request.form["date"].strip(), "%Y-%m-%d").date().isoformat()
    except (ValueError, KeyError):
        flash("Enter a positive amount and a valid date.", "danger")
        return redirect(url_for("index"))

    category = request.form.get("category", "").strip() or "Other"
    description = request.form.get("description", "").strip()
    month = exp_date[:7]

    before = db.monthly_total(month)
    db.add_expense(amount, category, description, exp_date)

    budget = db.get_budget()
    if budget:
        after = db.monthly_total(month)
        if before < budget <= after:
            flash(
                f"You have exceeded your {month} budget of {budget:.2f}!", "danger")
        elif before < WARN_AT * budget <= after:
            flash(
                f"You have used {after / budget * 100:.0f}% of your {month} budget.", "warning")
    return redirect(url_for("index"))


@app.route("/delete/<int:expense_id>", methods=["POST"])
def delete(expense_id):
    db.delete_expense(expense_id)
    return redirect(url_for("index"))


@app.route("/budget", methods=["POST"])
def budget():
    try:
        value = float(request.form["budget"])
        if value <= 0:
            raise ValueError
        db.set_budget(value)
    except (ValueError, KeyError):
        flash("Enter a valid budget amount.", "danger")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
