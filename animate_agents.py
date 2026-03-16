#!/usr/bin/env python3
"""
Animate individual agents over time on the topology layout for verification.
Useful for spotting movement problems, bottlenecks, and evacuation flow.

Usage:
  python animate_agents.py --topology ring --results data/experiments/ring/results_a2.0_b2.0_s0.csv
  python animate_agents.py --topology star --results data/experiments/star/results_a1.0_b1.0_s0.csv -o star_anim.mp4

Layouts: ring (concentric rings), star (hub + spokes), linear (chain with side branches).
"""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.collections import LineCollection

def load_topology(topology: str, repo_root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load locations and routes for the given topology."""
    topo_dir = repo_root / "topologies" / topology / "input_csv"
    if not topo_dir.exists():
        raise FileNotFoundError(f"Topology dir not found: {topo_dir}")
    locations = pd.read_csv(topo_dir / "locations.csv")
    routes = pd.read_csv(topo_dir / "routes.csv")
    return locations, routes

def build_coord_map(locations: pd.DataFrame) -> dict[str, tuple[float, float]]:
    """Map location name -> (x, y)."""
    return {row["name"]: (float(row["gps_x"]), float(row["gps_y"])) for _, row in locations.iterrows()}

def get_location_info(locations: pd.DataFrame, topo_dir: Path) -> dict[str, dict]:
    """Map location name -> {x, y, type, conflict}."""
    conflict_map = {}
    conflicts_file = topo_dir / "conflicts.csv"
    if conflicts_file.exists():
        try:
            cf = pd.read_csv(conflicts_file)
            if "location" in cf.columns and "conflict_value" in cf.columns:
                for _, r in cf.iterrows():
                    conflict_map[str(r["location"])] = float(r["conflict_value"])
        except Exception:
            pass
    info = {}
    for _, row in locations.iterrows():
        name = row["name"]
        loc_type = str(row.get("location_type", "town")).lower()
        if "conflict" in loc_type or "Facility" in name or "Hub" in name:
            node_type = "conflict"
        elif "camp" in loc_type or "SafeZone" in name:
            node_type = "safe"
        else:
            node_type = "town"
        info[name] = {
            "x": float(row["gps_x"]),
            "y": float(row["gps_y"]),
            "type": node_type,
            "conflict": conflict_map.get(name, 0.0),
        }
    return info

def main():
    parser = argparse.ArgumentParser(description="Animate agents on topology layout")
    parser.add_argument("--topology", choices=["ring", "star", "linear"], default="ring",
                        help="Layout: ring (concentric), star (hub+spokes), linear (chain)")
    parser.add_argument("--results", type=Path, required=True, help="Path to results_*.csv")
    parser.add_argument("-o", "--output", type=Path, default=None,
                        help="Output path (default: data/experiments/figures/{topology}_agents.mp4)")
    parser.add_argument("--format", choices=["mp4", "gif"], default="mp4", help="Output format")
    parser.add_argument("--fps", type=int, default=4, help="Frames per second")
    parser.add_argument("--jitter", type=float, default=1.5,
                        help="Jitter radius for overlapping agents at same node")
    parser.add_argument("--max-agents", type=int, default=None,
                        help="Subsample agents for faster render (default: all)")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent
    results_path = args.results if args.results.is_absolute() else repo_root / args.results
    if not results_path.exists():
        print(f"Results not found: {results_path}")
        return 1

    df = pd.read_csv(results_path)
    if "location" not in df.columns or "timestep" not in df.columns:
        print("Results must have 'location' and 'timestep' columns.")
        return 1

    locations, routes = load_topology(args.topology, repo_root)
    topo_dir = repo_root / "topologies" / args.topology / "input_csv"
    coord_map = build_coord_map(locations)
    loc_info = get_location_info(locations, topo_dir)

    # Build edge segments for drawing
    segments = []
    for _, row in routes.iterrows():
        n1, n2 = row["name1"], row["name2"]
        if n1 in coord_map and n2 in coord_map:
            segments.append([coord_map[n1], coord_map[n2]])
    if not segments:
        print("No route segments found; topology may use different column names.")
        segments = [[(0, 0), (0, 0)]]

    timesteps = sorted(df["timestep"].unique())
    if not timesteps:
        print("No timesteps in results.")
        return 1

    agents = df["agent_id"].unique()
    if args.max_agents and len(agents) > args.max_agents:
        rng = np.random.default_rng(42)
        agents = rng.choice(agents, args.max_agents, replace=False)

    out_path = args.output
    if out_path is None:
        out_dir = repo_root / "data" / "experiments" / "figures"
        out_dir.mkdir(parents=True, exist_ok=True)
        ext = "mp4" if args.format == "mp4" else "gif"
        out_path = out_dir / f"{args.topology}_agents.{ext}"
    out_path = out_path if out_path.is_absolute() else repo_root / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(42)
    jitter = args.jitter

    fig, ax = plt.subplots(figsize=(12, 10))
    lc = LineCollection(segments, colors="lightgray", linewidths=0.8, zorder=0)
    ax.add_collection(lc)

    # Plot nodes by type: conflict=star, safe=square, town=circle
    node_texts = {}  # location_name -> text object for population count
    for name, info in loc_info.items():
        x, y = info["x"], info["y"]
        t = info["type"]
        if t == "conflict":
            ax.scatter(x, y, s=800, c="#D35400", marker="*", alpha=0.9, zorder=1,
                       edgecolors="#873600", linewidths=2)
            node_texts[name] = ax.text(x, y + 18, f"{name}\n(0)", ha="center", fontsize=9,
                                       fontweight="bold", bbox=dict(boxstyle="round,pad=0.2",
                                       facecolor="#F5B7B1", edgecolor="#873600", alpha=0.9), zorder=10)
        elif t == "safe":
            ax.scatter(x, y, s=600, c="#56B4E9", marker="s", alpha=0.8, zorder=1,
                       edgecolors="#0072B2", linewidths=2)
            display = name.replace("SafeZone", "Safe ")
            node_texts[name] = ax.text(x, y + 22, f"{display}\n(0)", ha="center", fontsize=10,
                                       fontweight="bold", bbox=dict(boxstyle="round,pad=0.3",
                                       facecolor="#CCE5FF", edgecolor="#0072B2", alpha=0.9), zorder=10)
        else:
            ax.scatter(x, y, s=120, c="#95a5a6", marker="o", alpha=0.6, zorder=1,
                       edgecolors="#7f8c8d", linewidths=1)
            node_texts[name] = ax.text(x, y + 12, "(0)", ha="center", fontsize=8, alpha=0.8, zorder=10)

    scat = ax.scatter([], [], c=[], cmap="viridis", s=20, alpha=0.8, vmin=0, vmax=1, zorder=2)
    title = ax.text(0.5, 0.98, "", transform=ax.transAxes, ha="center", fontsize=16, fontweight="bold")
    subtitle = ax.text(0.5, 0.94, "", transform=ax.transAxes, ha="center", fontsize=12)

    def init():
        scat.set_offsets(np.empty((0, 2)))
        scat.set_array(np.array([]))
        for txt in node_texts.values():
            txt.set_visible(True)
        return [scat]

    def update(frame):
        t = timesteps[frame]
        sub = df[(df["timestep"] == t) & (df["agent_id"].isin(agents))]
        loc_counts = sub["location"].value_counts() if not sub.empty else pd.Series(dtype=int)
        for name, txt in node_texts.items():
            cnt = int(loc_counts.get(name, 0))
            info = loc_info[name]
            if info["type"] == "conflict":
                txt.set_text(f"{name}\n({cnt})")
            elif info["type"] == "safe":
                display = name.replace("SafeZone", "Safe ")
                txt.set_text(f"{display}\n({cnt})")
            else:
                txt.set_text(f"({cnt})")
        if sub.empty:
            scat.set_offsets(np.empty((0, 2)))
            scat.set_array(np.array([]))
            title.set_text(f"{args.topology} topology — t={t}")
            subtitle.set_text("No agents")
        else:
            coords = []
            p_s2_vals = []
            for _, row in sub.iterrows():
                loc = row["location"]
                if pd.isna(loc) or str(loc) == "None":
                    continue
                if loc not in coord_map:
                    continue
                x, y = coord_map[loc]
                if jitter > 0:
                    x += rng.uniform(-jitter, jitter)
                    y += rng.uniform(-jitter, jitter)
                coords.append([x, y])
                p_s2_vals.append(row.get("p_s2", 0.5))
            if coords:
                scat.set_offsets(np.array(coords))
                scat.set_array(np.array(p_s2_vals))
            else:
                scat.set_offsets(np.empty((0, 2)))
                scat.set_array(np.array([]))
            mean_p_s2 = sub["p_s2"].mean()
            s2_pct = mean_p_s2 * 100
            evacuated = (sub["location"].astype(str).str.contains("SafeZone", na=False)).sum()
            title.set_text(f"{args.topology} topology — t={t} | n={len(sub)}")
            subtitle.set_text(f"Mean P_S2: {s2_pct:.1f}% | At Safe Zones: {evacuated}")
        return [scat]

    xs = [c[0] for c in coord_map.values()]
    ys = [c[1] for c in coord_map.values()]
    ax.set_xlim(min(xs) - 25, max(xs) + 25)
    ax.set_ylim(min(ys) - 25, max(ys) + 25)
    ax.set_aspect("equal")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    cbar = plt.colorbar(scat, ax=ax, label="P_S2")

    anim = FuncAnimation(fig, update, frames=len(timesteps), init_func=init, blit=False)

    if args.format == "gif":
        writer = PillowWriter(fps=args.fps)
        anim.save(str(out_path), writer=writer)
    else:
        try:
            writer = "ffmpeg"
            anim.save(str(out_path), writer=writer, fps=args.fps)
        except Exception:
            writer = PillowWriter(fps=args.fps)
            out_path = out_path.with_suffix(".gif")
            anim.save(str(out_path), writer=writer)
            print("ffmpeg not found; saved as GIF instead.")

    plt.close(fig)
    print(f"Saved: {out_path} ({args.topology} layout)")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
