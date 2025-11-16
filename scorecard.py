# scorecard.py
from typing import List, Dict, Optional

class Scorecard:
    def __init__(self, team_name: str, players: List[str], bowlers: List[str],
                 venue: str = "", mode: str = "first", target: Optional[int] = None, max_overs: int = 20,
                 wins_bat_first: int = 0, wins_bat_second: int = 0):
        self.team_name = team_name
        self.players = players[:]  # batting order
        self.bowlers = bowlers[:]  # allowed bowlers to pick from
        self.venue = venue
        self.mode = mode  # "first" or "chase"
        self.target = target
        self.max_overs = max_overs
        self.wins_bat_first = wins_bat_first
        self.wins_bat_second = wins_bat_second

        # batting / match state
        self.total_runs = 0
        self.wickets = 0
        self.balls = 0  # legal balls bowled in innings
        self.current_batsmen = [0, 1]  # indexes into players: [striker, non-striker]
        self.out_batsmen = []  # list of indices that are out
        self.batsmen_stats: Dict[str, Dict] = {
            p: {"runs": 0, "balls": 0, "fours": 0, "sixes": 0} for p in players
        }

        # bowling
        self.current_bowler: Optional[str] = None
        self.bowler_stats: Dict[str, Dict] = {}
        for b in bowlers:
            self.bowler_stats[b] = {"balls": 0, "runs": 0, "wickets": 0, "maidens": 0}

        # overs tracking
        self.current_over_balls: List[str] = []  # list of symbols for the current over
        self.completed_overs: List[Dict] = []  # each entry: {"over": n, "bowler": str, "balls": [...]}

        # fall of wickets: list of dicts { "wk_no": int, "score": int, "batsman": str, "bowler": str, "reason": str, "over": "x.y" }
        self.fall_of_wickets: List[Dict] = []

        # extras
        self.extras = {"wides": 0, "noballs": 0, "legbyes": 0, "byes": 0}

        # free hit flag (true if next valid ball is free-hit due to NB)
        self.free_hit = False

    # ---------- helpers ----------
    def overs_str(self):
        return f"{self.balls // 6}.{self.balls % 6}"

    def remaining_overs_str(self):
        balls_left = max(0, self.max_overs * 6 - self.balls)
        return f"{balls_left // 6}.{balls_left % 6}"

    def run_rate(self):
        if self.balls == 0:
            return 0.0
        return round(self.total_runs / (self.balls / 6.0), 2)

    def predicted_score(self, rr_offset=0.0):
        # Prediction using current run-rate * max_overs + offset applied by adding to RR
        crr = self.run_rate()
        predicted_rr = max(0.0, crr + rr_offset)
        return int(round(predicted_rr * self.max_overs))

    def initial_win_probability_from_history(self):
        # Uses wins_bat_first vs wins_bat_second to compute prior probability
        total = self.wins_bat_first + self.wins_bat_second
        if total == 0:
            return None
        # if current innings is batting first, show probability for batting-first team
        p_first = (self.wins_bat_first / total) * 100.0
        return round(p_first, 2)

    # ---------- bowler selection ----------
    def set_bowler(self, bowler_name: str):
        if bowler_name not in self.bowler_stats:
            # allow new bowlers too
            self.bowler_stats[bowler_name] = {"balls": 0, "runs": 0, "wickets": 0, "maidens": 0}
            if bowler_name not in self.bowlers:
                self.bowlers.append(bowler_name)
        self.current_bowler = bowler_name

    # ---------- ball processing ----------
    def add_ball(self, outcome_raw: str, extra_runs_on_dead_ball: int = 0, wicket_reason: Optional[str] = None):
        """
        outcome_raw: symbol (0,1,2,3,4,6,W,WD,NB,LBx,Bx, NB+<bat runs> optionally)
        extra_runs_on_dead_ball: additional runs taken (for WD/NB) - front-end handles prompt and passes this
        wicket_reason: string for wicket (caught, bowled, stumping...)
        """
        if self.current_bowler is None:
            raise ValueError("No bowler set")

        outcome = outcome_raw.strip().upper()
        legal = False
        runs_off_bat_against_bowler = 0  # runs that count against bowler
        display_token = outcome  # what to push into current_over_balls

        # WICKET
        if outcome == "W":
            # if free_hit is true, wicket (except run-out) is not allowed — front-end will prevent run-out on free-hit if needed.
            striker_idx = self.current_batsmen[0]
            striker_name = self.players[striker_idx]
            # ball counts
            self.balls += 1
            legal = True
            # batsman faced the ball
            self.batsmen_stats[striker_name]["balls"] += 1
            # bowler wicket count (unless free_hit true)
            if not self.free_hit:
                self.bowler_stats[self.current_bowler]["wickets"] += 1
            else:
                # if free hit, wicket doesn't count (except run-out). We'll assume frontend prevented non-runout wicket on free hit.
                pass
            # record fall of wicket
            over_str = self.overs_str()
            self.fall_of_wickets.append({
                "wk_no": self.wickets + 1,
                "score": self.total_runs,
                "batsman": striker_name,
                "bowler": self.current_bowler,
                "reason": wicket_reason or "out",
                "over": over_str
            })
            # move batsman to out list
            self.out_batsmen.append(striker_idx)
            self.wickets += 1
            # next batsman comes
            next_idx = self.wickets + 1
            if next_idx < len(self.players):
                self.current_batsmen[0] = next_idx
            # display
            display_token = "W"

        # WIDE
        elif outcome.startswith("WD"):
            # wide is not legal delivery
            extra = 1 + max(0, int(extra_runs_on_dead_ball))
            self.total_runs += extra
            self.extras["wides"] += extra
            runs_off_bat_against_bowler += extra
            display_token = "WD" if extra == 1 else f"WD+{extra-1}"
            # legal remains False

        # NO BALL
        elif outcome.startswith("NB"):
            # NB not legal; penal + possibly bat runs (provided by extra_runs_on_dead_ball param)
            base = 1
            bat_runs = max(0, int(extra_runs_on_dead_ball))
            self.total_runs += (base + bat_runs)
            self.extras["noballs"] += base
            runs_off_bat_against_bowler += (base + bat_runs)
            # if bat_runs >0 then batsman gets runs but does NOT get credited ball faced
            if bat_runs > 0:
                striker_name = self.players[self.current_batsmen[0]]
                self.batsmen_stats[striker_name]["runs"] += bat_runs
                if bat_runs == 4:
                    self.batsmen_stats[striker_name]["fours"] += 1
                if bat_runs == 6:
                    self.batsmen_stats[striker_name]["sixes"] += 1
                # rotate strike on odd bat_runs
                if bat_runs % 2 == 1:
                    self.current_batsmen.reverse()
                display_token = f"NB+{bat_runs}" if bat_runs > 0 else "NB"
            else:
                display_token = "NB"
            # mark free-hit for next legal delivery
            self.free_hit = True

        # LEG BYES
        elif outcome.startswith("LB"):
            runs = int(outcome[2:]) if len(outcome) > 2 else int(extra_runs_on_dead_ball or 0)
            self.total_runs += runs
            self.extras["legbyes"] += runs
            # legal ball
            self.balls += 1
            legal = True
            display_token = f"LB{runs}"
            # rotate strike if odd
            if runs % 2 == 1:
                self.current_batsmen.reverse()
            # legbyes do NOT count against bowler (according to your earlier rule)

        # BYES
        elif outcome.startswith("B"):
            runs = int(outcome[1:]) if len(outcome) > 1 else int(extra_runs_on_dead_ball or 0)
            self.total_runs += runs
            self.extras["byes"] += runs
            self.balls += 1
            legal = True
            display_token = f"B{runs}"
            if runs % 2 == 1:
                self.current_batsmen.reverse()
            # not counted against bowler

        # NORMAL RUNS
        else:
            # expect digits 0,1,2,3,4,6
            try:
                runs = int(outcome)
            except:
                raise ValueError("Invalid ball outcome")
            if runs not in (0,1,2,3,4,6):
                raise ValueError("Allowed runs are 0,1,2,3,4,6")
            striker_name = self.players[self.current_batsmen[0]]
            self.batsmen_stats[striker_name]["runs"] += runs
            self.batsmen_stats[striker_name]["balls"] += 1
            if runs == 4:
                self.batsmen_stats[striker_name]["fours"] += 1
            if runs == 6:
                self.batsmen_stats[striker_name]["sixes"] += 1
            self.total_runs += runs
            self.balls += 1
            legal = True
            runs_off_bat_against_bowler += runs
            display_token = str(runs)
            if runs % 2 == 1:
                self.current_batsmen.reverse()

        # update bowler stat contributions
        if runs_off_bat_against_bowler > 0:
            self.bowler_stats[self.current_bowler]["runs"] += runs_off_bat_against_bowler
        if legal:
            self.bowler_stats[self.current_bowler]["balls"] += 1

        # store ball in current_over_balls
        self.current_over_balls.append(display_token)

        # if over complete (6 legal balls) -> store completed over and prompt next bowler
        if legal and (self.balls % 6 == 0):
            over_no = (self.balls // 6)
            self.completed_overs.append({
                "over": over_no,
                "bowler": self.current_bowler,
                "balls": self.current_over_balls.copy()
            })
            # reset current over
            self.current_over_balls = []
            # swap strike at over-end
            self.current_batsmen.reverse()
            # reset free_hit (free hit applies only to next legal delivery, after that it's consumed)
            self.free_hit = False

        # after any legal ball not NB, free_hit should be cleared (NB sets it True)
        if legal:
            # if this legal ball was taken as free hit, free_hit should be set False afterwards
            self.free_hit = False

        # check innings end or chase result handled by app layer
        return display_token

    # ---------- extra views ----------
    def get_current_batting(self):
        # return list of current batsmen info (only those not out and on crease)
        res = []
        for idx in self.current_batsmen:
            if idx < len(self.players) and idx not in self.out_batsmen:
                p = self.players[idx]
                s = self.batsmen_stats[p]
                res.append({"name": p, "runs": s["runs"], "balls": s["balls"], "fours": s["fours"], "sixes": s["sixes"]})
        return res

    def get_out_batsmen(self):
        res = []
        for idx in self.out_batsmen:
            p = self.players[idx]
            s = self.batsmen_stats[p]
            res.append({"name": p, "runs": s["runs"], "balls": s["balls"], "fours": s["fours"], "sixes": s["sixes"]})
        return res

    def innings_over(self):
        if self.balls >= self.max_overs * 6:
            return True
        if self.wickets >= len(self.players) - 1:
            return True
        if self.mode == "chase" and self.target is not None and self.total_runs >= self.target:
            return True
        return False
