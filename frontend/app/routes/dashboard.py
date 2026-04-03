from flask import Blueprint, render_template, request, redirect, url_for

from app.services import api

bp = Blueprint("dashboard", __name__)


@bp.route("/dashboard")
def global_dashboard():
    overview = api.get_overview()
    characters = api.get_characters()
    cards = api.get_cards(min_appearances=1)
    run_outcomes = api.get_run_outcomes()

    # Sort cards by win rate descending, take top 15
    if cards:
        cards = sorted(cards, key=lambda c: c.get("win_rate_when_present", 0), reverse=True)[:15]

    return render_template(
        "dashboard/global.html",
        overview=overview,
        characters=characters,
        cards=cards,
        run_outcomes=run_outcomes,
        format_character=api.format_character_name,
        format_duration=api.format_duration,
    )


@bp.route("/dashboard/search", methods=["POST"])
def search_player():
    steam_id = request.form.get("steam_id", "").strip()
    if not steam_id:
        return redirect(url_for("dashboard.global_dashboard"))
    return redirect(url_for("dashboard.player_dashboard", steam_id=steam_id))


@bp.route("/dashboard/<steam_id>")
def player_dashboard(steam_id: str):
    overview = api.get_overview(steam_id=steam_id)
    characters = api.get_characters(steam_id=steam_id)
    cards = api.get_cards(steam_id=steam_id, min_appearances=1)
    run_outcomes = api.get_run_outcomes(steam_id=steam_id)

    has_data = overview is not None and overview.get("run_count", 0) > 0

    if cards:
        cards = sorted(cards, key=lambda c: c.get("win_rate_when_present", 0), reverse=True)[:15]

    return render_template(
        "dashboard/player.html",
        steam_id=steam_id,
        overview=overview,
        characters=characters,
        cards=cards,
        run_outcomes=run_outcomes,
        has_data=has_data,
        format_character=api.format_character_name,
        format_duration=api.format_duration,
    )
