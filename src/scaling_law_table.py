"""Phase 4 (MVP): the "probability of success at different scales" table, for basketball.

Taleb's dentist (Fooled by Randomness, Table 3.1) expects +15% a year with 10% volatility, so
he is up in 93% of years but only 54% of days. The same calculation applies to a basketball
team, with possessions in place of time:

    P(win a stretch of n possessions) ~= Phi( mu * sqrt(n) / sigma )

    mu    = average margin per possession = net rating / 200
            (net rating is per 100 of the team's own possessions; it has the ball for ~half)
    sigma = how much the margin bounces around per possession (measured, sql/05_sigma.sql)
    n     = possessions in the stretch, both teams combined

This script measures sigma, then compares the model with what actually happened for the
best-record teams of recent seasons. Run from the project folder:  python -m src.scales
"""
import duckdb
import numpy as np
import pandas as pd
from scipy.stats import norm

from src import config


def measure_sigma(con):
    """Per-possession noise, from the variance of real window margins (sql/05_sigma.sql)."""
    by_size = con.execute((config.SQL_DIR / "05_sigma.sql").read_text()).df()
    sigma = by_size.loc[by_size["size"] == config.SIGMA_WINDOW_SIZE, "sigma"].item()

    # For comparison: the naive estimate, treating every possession as independent
    naive = con.execute("SELECT sqrt(avg(pts * pts)) FROM possessions_ordered").fetchall()[0][0]
    return sigma, naive, by_size


def load_featured(con):
    """Win % at every level for the best-record teams plus the extra team-seasons."""
    extra = pd.DataFrame(config.EXTRA_TEAM_SEASONS, columns=["team", "season"])
    con.register("extra_teams", extra)
    query = (config.SQL_DIR / "06_scale_table.sql").read_text()
    return con.execute(query, {"best_seasons": config.BEST_RECORD_SEASONS}).df()


def scale_rows(team):
    """(label, segments to average, possessions n) for each scale, from full game down."""
    per_game = 2 * team["poss_per_game"]           # both teams' possessions in a game
    rows = [("Full game", ["game"], per_game),
            ("Half", ["half_1", "half_2"], per_game / 2),
            ("Quarter", ["quarter"], per_game / 4)]
    rows += [(f"{s} possessions", [f"poss_{s}"], s) for s in config.SCALE_WINDOW_SIZES]
    return rows


def build_tables(featured, sigma):
    """Two tables, rows = scales and columns = teams: what happened, and what the model says."""
    actual, model, teams = {}, {}, []
    for (season, team), g in featured.groupby(["season", "team"], sort=False):
        info = g.iloc[0]
        label = f"{team} {season - 1}-{str(season)[2:]} ({info.wins}-{info.losses})"
        mu = info.net_rating / 200
        win = g.set_index("segment")["win_pct"]
        actual[label], model[label] = {}, {}
        for scale, segments, n in scale_rows(info):
            actual[label][scale] = win[segments].mean()
            model[label][scale] = norm.cdf(mu * np.sqrt(n) / sigma)
        teams.append({"team": label, "net_rating": info.net_rating, "mu": mu,
                      "mu_over_sigma": mu / sigma})
    return pd.DataFrame(actual), pd.DataFrame(model), pd.DataFrame(teams)


def pct(table):
    return table.map(lambda x: f"{100 * x:.1f}%")


def to_markdown(df, index_name):
    """Minimal Markdown table writer (avoids an extra dependency)."""
    header = [index_name] + list(df.columns)
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(str(v) for v in row) + " |"
              for row in df.itertuples()]
    return "\n".join(lines)


def run_scales():
    config.RESULTS_DIR.mkdir(exist_ok=True)
    con = duckdb.connect(str(config.DB_PATH), read_only=True)
    sigma, naive_sigma, sigma_by_size = measure_sigma(con)
    featured = load_featured(con)
    con.close()

    actual, model, teams = build_tables(featured, sigma)
    actual.to_csv(config.RESULTS_DIR / "scales_actual.csv")
    model.to_csv(config.RESULTS_DIR / "scales_model.csv")
    sigma_by_size.to_csv(config.RESULTS_DIR / "sigma_by_window_size.csv", index=False)

    report = "\n\n".join([
        "# Probability of winning at different scales",
        "## What actually happened (share of stretches won; ties count as half)",
        to_markdown(pct(actual), "Scale"),
        f"## What the model predicts: Phi(mu * sqrt(n) / sigma), sigma = {sigma:.2f}",
        to_markdown(pct(model), "Scale"),
        "## Inputs",
        to_markdown(teams.set_index("team").round(3), "Team"),
        (f"sigma measured from {config.SIGMA_WINDOW_SIZE}-possession windows: {sigma:.3f} "
         f"(naive single-possession estimate: {naive_sigma:.3f})"),
        "## Variance per possession by window size",
        to_markdown(sigma_by_size.set_index("size").round(3), "Window size"),
    ])
    (config.RESULTS_DIR / "scales_table.md").write_text(report + "\n")

    print(f"  sigma = {sigma:.3f} (naive {naive_sigma:.3f})")
    print("\n  ACTUAL\n" + pct(actual).to_string())
    print("\n  MODEL\n" + pct(model).to_string())
    print(f"\n  saved {config.RESULTS_DIR / 'scales_table.md'}")


if __name__ == "__main__":
    run_scales()