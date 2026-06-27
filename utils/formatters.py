"""Output formatting helpers.

Sprint 1d. Formats the structured plan into readable text for CLI output.
"""


def format_plan_for_cli(plan: dict) -> str:
    """Render a plan dict as human-readable text for the CLI."""
    lines = []
    targets = plan.get("macro_targets", {})
    if targets:
        lines.append(
            f"Daily target: {targets.get('calories')} cal, "
            f"{targets.get('protein_g')}g protein"
        )
        lines.append("")

    for day in plan.get("days", []):
        t = day.get("day_totals", {})
        flag = "" if day.get("on_target", True) else "  (off target)"
        lines.append(f"Day {day.get('day')} — {t.get('calories')} cal, "
                     f"{t.get('protein_g')}P / {t.get('carbs_g')}C / "
                     f"{t.get('fat_g')}F{flag}")
        for meal in day.get("meals", []):
            serv = meal.get("servings", 1)
            serv_txt = f" x{serv}" if serv and serv != 1 else ""
            lines.append(f"  {meal.get('slot', ''):<10} {meal.get('name', '')}"
                         f"{serv_txt} — {meal.get('calories')} cal")
        lines.append("")

    shopping = plan.get("shopping_list", [])
    if shopping:
        lines.append("Shopping list:")
        category = None
        for item in shopping:
            if item.get("category") != category:
                category = item.get("category")
                lines.append(f"  [{category}]")
            lines.append(f"    {item.get('qty')} {item.get('unit')} {item.get('item')}")

    return "\n".join(lines).rstrip()
