# app.py
from flask import Flask, render_template, request, redirect, url_for, jsonify
from scorecard import Scorecard

app = Flask(__name__, static_folder="static", template_folder="templates")

# single global scorecard for demo / local use
SC: Scorecard = None

@app.route("/", methods=["GET"])
def index():
    global SC
    return render_template("index.html", sc=SC)

# start match
@app.route("/start", methods=["POST"])
def start():
    global SC
    data = request.form
    team_name = data.get("team_name", "Team A")
    players_raw = data.get("players", "")
    bowlers_raw = data.get("bowlers", "")
    venue = data.get("venue", "")
    mode = data.get("mode", "first")
    target = int(data.get("target")) if data.get("target") else None
    max_overs = int(data.get("overs") or 20)
    # historical wins (for venue)
    wins_first = int(data.get("wins_first") or 0)
    wins_second = int(data.get("wins_second") or 0)

    # parse players and bowlers
    players = [p.strip() for p in players_raw.split(",") if p.strip()]
    if len(players) < 2:
        # fill defaults
        players = ["P1","P2","P3","P4","P5","P6","P7","P8","P9","P10","P11"]
    bowlers = [b.strip() for b in bowlers_raw.split(",") if b.strip()]
    if not bowlers:
        # default bowlers (take some from players if not provided)
        bowlers = ["Bowler1","Bowler2","Bowler3","Bowler4","Bowler5"]

    SC = Scorecard(team_name, players, bowlers, venue=venue, mode=mode, target=target,
                   max_overs=max_overs, wins_bat_first=wins_first, wins_bat_second=wins_second)
    # set initial bowler if provided
    first_bowler = data.get("first_bowler", "")
    if first_bowler:
        SC.set_bowler(first_bowler)
    return redirect(url_for("index"))

# set bowler (called after over completes or manually)
@app.route("/set_bowler", methods=["POST"])
def set_bowler():
    global SC
    if SC is None:
        return "No match", 400
    bowler = request.form.get("bowler")
    SC.set_bowler(bowler)
    return redirect(url_for("index"))

# add a ball (AJAX-friendly)
@app.route("/ball", methods=["POST"])
def ball():
    global SC
    if SC is None:
        return jsonify({"error": "No active match"}), 400
    outcome = request.form.get("outcome")
    extra_runs = int(request.form.get("extra_runs") or 0)
    wicket_reason = request.form.get("wicket_reason") or None

    # if free hit and outcome is 'W' and reason not runout, block the wicket (front-end should prevent but double-check)
    if SC.free_hit and outcome and outcome.upper() == "W":
        # treat as just '0' (or ignore wicket)
        # For safety, call with no wicket effect and mark display token as "W(FH blocked)"
        token = SC.add_ball("0")
        # We'll still record the ball as 0 and show message back
        response = {"status": "free_hit_blocked", "token": token}
    else:
        token = SC.add_ball(outcome, extra_runs_on_dead_ball=extra_runs, wicket_reason=wicket_reason)
        response = {"status": "ok", "token": token}

    # after adding ball, check if over completed and current_over_balls reset -> ask frontend to prompt bowler selection
    need_bowler = False
    if len(SC.current_over_balls) == 0 and (SC.balls % 6 == 0):
        # over completed
        need_bowler = True

    # prepare small snapshot to return
    snapshot = {
        "total_runs": SC.total_runs,
        "wickets": SC.wickets,
        "overs": SC.overs_str(),
        "current_over_balls": SC.current_over_balls,
        "completed_overs": SC.completed_overs,
        "fall_of_wickets": SC.fall_of_wickets,
        "bowler_stats": SC.bowler_stats,
        "current_bowler": SC.current_bowler,
        "predicted_score_rr": SC.predicted_score(0.0),
        "predicted_score_rr_plus2": SC.predicted_score(2.0),
        "predicted_score_rr_plus4": SC.predicted_score(4.0),
        "need_bowler": need_bowler,
        "free_hit": SC.free_hit,
        "remaining_overs": SC.remaining_overs_str(),
        "current_batting": SC.get_current_batting(),
        "out_batsmen": SC.get_out_batsmen()
    }
    # check innings end
    if SC.innings_over():
        snapshot["innings_over"] = True

    return jsonify(snapshot)

# endpoint to get list of bowlers
@app.route("/bowlers", methods=["GET"])
def bowlers():
    global SC
    if SC is None:
        return jsonify([])
    return jsonify(SC.bowlers)

if __name__ == "__main__":
    app.run(debug=True)
