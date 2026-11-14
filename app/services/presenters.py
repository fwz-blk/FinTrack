def budget_row(budget):
    total = float(budget.amount)
    spent = float(budget.spent)
    percent = 0 if total <= 0 else min(100, int((spent / total) * 100))
    if percent >= 100:
        tone = "red" if spent > total else "green"
    elif percent >= 80:
        tone = "orange"
    else:
        tone = "green"
    return {
        "name": budget.name,
        "spent": f"${spent:,.2f} / ${total:,.2f}",
        "percent": percent,
        "tone": tone,
        "remaining": max(0.0, total - spent),
        "status": "Over budget" if spent > total else "Near limit" if percent >= 80 else "On track",
    }


def goal_row(goal):
    target = float(goal.target_amount)
    saved = float(goal.saved_amount)
    percent = 0 if target <= 0 else min(100, int((saved / target) * 100))
    return {
        "name": goal.name,
        "deadline": goal.deadline.strftime("%b %d, %Y") if goal.deadline else "No deadline",
        "percent": f"{percent}%",
        "amount": f"${saved:,.2f} / ${target:,.2f}",
        "tone": "green" if percent >= 100 else "blue" if percent >= 50 else "",
        "complete": percent >= 100,
    }
