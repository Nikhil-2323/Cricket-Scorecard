// static/script.js
// Handles button clicks, prompts for extras/wicket reason, calls /ball endpoint via fetch
document.addEventListener("DOMContentLoaded", () => {
  const ballButtons = document.querySelectorAll(".ball-buttons button");
  const currentOverEl = document.getElementById("current-over");
  const completedOversEl = document.getElementById("completed-overs");
  const curBowlerEl = document.getElementById("curBowler");
  const predRR = document.getElementById("pred_rr");
  const predRR2 = document.getElementById("pred_rr2");
  const predRR4 = document.getElementById("pred_rr4");
  const currentBattingEl = document.getElementById("current-batting");
  const outBatsmenEl = document.getElementById("out-batsmen");
  const bowlingStatsEl = document.getElementById("bowling-stats");
  const fallOfWicketsEl = document.getElementById("fall-of-wickets");
  const extrasEl = document.getElementById("extras");

  // Use delegated click for ball-buttons
  ballButtons.forEach(btn => {
    btn.addEventListener("click", async (ev) => {
      const outcome = btn.dataset.outcome;
      let extra_runs = 0;
      let wicket_reason = "";

      if (outcome === "WD" || outcome === "NB") {
        // ask if batsman took extra runs on this ball
        const got = prompt("Extra runs taken on this ball (besides the penalty run)? Enter 0 if none.");
        extra_runs = parseInt(got || "0");
        if (isNaN(extra_runs) || extra_runs < 0) extra_runs = 0;
      }

      if (outcome === "W") {
        // ask for wicket reason
        wicket_reason = prompt("Reason for wicket (caught, bowled, lbw, stumping, run out, etc.)", "caught");
        if (!wicket_reason) wicket_reason = "out";
      }

      // Send to server
      const form = new FormData();
      form.append('outcome', outcome);
      form.append('extra_runs', extra_runs);
      form.append('wicket_reason', wicket_reason);

      const res = await fetch('/ball', { method: 'POST', body: form });
      const json = await res.json();
      if (json.error) {
        alert(json.error);
        return;
      }
      // update UI snapshot
      updateSnapshot(json);
      if (json.need_bowler) {
        // show prompt to select next bowler
        const bowlersResp = await fetch('/bowlers');
        const bowlers = await bowlersResp.json();
        const b = prompt("Select next bowler from list:\n" + bowlers.join(", "));
        if (b) {
          // set via form submit
          const sform = document.getElementById('setBowlerForm');
          const sel = document.getElementById('bowlerSelect');
          // if select exists, try to set value; else create a quick post
          if (sel) {
            let found = false;
            for (let opt of sel.options) { if (opt.value === b) found = true; }
            if (!found) {
              // append new option
              const opt = document.createElement('option');
              opt.value = b; opt.text = b; sel.add(opt);
            }
            sel.value = b;
            sform.submit();
          } else {
            // fallback: POST to /set_bowler via fetch
            const f = new FormData();
            f.append('bowler', b);
            await fetch('/set_bowler', { method: 'POST', body: f });
            location.reload();
          }
        }
      }
    });
  });

  // initial fetch to populate UI if page loaded with active match
  async function init() {
    // If page has no scorecard, nothing to do
    try {
      // we can fetch a small snapshot by calling /ball with no-op? Not provided.
      // But the server rendered initial state; we can just parse DOM placeholders or reload.
    } catch (e) {
      console.error(e);
    }
  }

  function clearEl(el) { if (el) el.innerHTML = ""; }

  function updateSnapshot(json) {
    // update current over
    if (currentOverEl) {
      currentOverEl.innerHTML = "";
      json.current_over_balls.forEach(tok => {
        const span = document.createElement('span');
        span.className = "ball-token";
        if (tok === '4') span.classList.add('four');
        if (tok === '6') span.classList.add('six');
        if (tok === 'W') span.classList.add('wicket');
        if (tok.startsWith('WD')) span.classList.add('wide');
        if (tok.startsWith('NB')) span.classList.add('noball');
        span.textContent = tok;
        currentOverEl.appendChild(span);
      });
    }

    // completed overs
    if (completedOversEl) {
      completedOversEl.innerHTML = "";
      json.completed_overs.forEach(over => {
        const div = document.createElement('div');
        div.className = 'comp-over';
        div.textContent = `Over ${over.over} [${over.bowler}]: ${over.balls.join(" ")}`;
        completedOversEl.appendChild(div);
      });
    }

    // update bowler text
    if (curBowlerEl) curBowlerEl.textContent = json.current_bowler || "-";

    // predictions
    if (predRR) predRR.textContent = json.predicted_score_rr;
    if (predRR2) predRR2.textContent = json.predicted_score_rr_plus2;
    if (predRR4) predRR4.textContent = json.predicted_score_rr_plus4;

    // batting on crease
    if (currentBattingEl) {
      currentBattingEl.innerHTML = "";
      (json.current_batting || []).forEach(b => {
        const d = document.createElement('div');
        d.className = 'bat-row';
        d.innerHTML = `<strong>${b.name}</strong> ${b.runs}(${b.balls}) <span class="small">4s:${b.fours} 6s:${b.sixes}</span>`;
        currentBattingEl.appendChild(d);
      });
    }

    // out batsmen
    if (outBatsmenEl) {
      outBatsmenEl.innerHTML = "";
      (json.out_batsmen || []).forEach(b => {
        const d = document.createElement('div');
        d.className = 'out-row';
        d.innerHTML = `<strong>${b.name}</strong> ${b.runs}(${b.balls}) <span class="small">4s:${b.fours} 6s:${b.sixes}</span>`;
        outBatsmenEl.appendChild(d);
      });
    }

    // bowling stats
    if (bowlingStatsEl) {
      bowlingStatsEl.innerHTML = "";
      for (let b in json.bowler_stats) {
        const s = json.bowler_stats[b];
        const overs = `${Math.floor(s.balls/6)}.${s.balls%6}`;
        const div = document.createElement('div');
        div.textContent = `${b} - ${overs} overs, ${s.runs} runs, ${s.wickets} wkts`;
        bowlingStatsEl.appendChild(div);
      }
    }

    // fall of wickets
    if (fallOfWicketsEl) {
      fallOfWicketsEl.innerHTML = "";
      (json.fall_of_wickets || []).forEach(f => {
        const str = `${f.wk_no}-${f.score} (${f.batsman}, ${f.bowler}, ${f.reason}, ${f.over} ov)`;
        const d = document.createElement('div');
        d.textContent = str;
        fallOfWicketsEl.appendChild(d);
      });
    }

    // extras
    if (extrasEl) {
      extrasEl.innerHTML = `Wides: ${json.bowler_stats ? json.bowler_stats : ""}`;
      // The server didn't include extras map in payload; skip for now or extend the endpoint
    }

    // if innings over, reload to show final
    if (json.innings_over) {
      alert("Innings over");
      location.reload();
    }
  }

  init();
});
