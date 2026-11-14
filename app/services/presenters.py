def budget_row(budget, spent=None, limit=None):
    total = float(limit if limit is not None else budget.amount)
    spent = float(budget.spent if spent is None else spent)
    raw_percent = 0 if total <= 0 else int((spent / total) * 100)
    percent = max(0, raw_percent)
    if percent >= 100:
        tone = "red" if spent > total else "green"
    elif percent >= budget.warning_threshold:
        tone = "orange"
    else:
        tone = "green"
    return {
        "id": budget.id,
        "name": budget.name,
        "category": budget.category,
        "period": budget.period,
        "rollover": budget.rollover,
        "warning_threshold": budget.warning_threshold,
        "spent": f"${spent:,.2f} / ${total:,.2f}",
        "percent": percent,
        "tone": tone,
        "remaining": total - spent,
        "status": "Over budget" if spent > total else "Near limit" if percent >= budget.warning_threshold else "On track",
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
