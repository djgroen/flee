import pandas as pd
import numpy as np
from pathlib import Path
import os
import sys

# Add current directory to path
sys.path.insert(0, '.')

def reanalyze():
    root_dir = Path("systematic_results")
    results = []
    
    for d in root_dir.iterdir():
        if not d.is_dir() or d.name == "animations": continue
        
        # Parse run parameters from name
        try:
            parts = d.name.split('_')
            # Format: Topology_N##_Dense/Sparse
            # But sometimes: Topology_N##_Run1_... if I used that format (I didn't)
            # My format: {topo_name}_N{N}_{'Dense' if dense else 'Sparse'}
            
            # parts[-1] is "Dense" or "Sparse"
            # parts[-2] is "N##"
            # parts[:-2] is Name (can contain underscores?)
            
            dense_str = parts[-1]
            n_str = parts[-2]
            topo_name = "_".join(parts[:-2])
            
            dense = (dense_str == "Dense")
            N = int(n_str.replace("N", ""))
            
            # Load locations to find safe zones
            loc_df = pd.read_csv(d / "locations.csv", dtype={'name': str})
            # Safe zones are those with type 'camp' OR capacity > 10000
            safe_zones = loc_df[ (loc_df['location_type'] == 'camp') | (loc_df['capacity'] > 10000) ]['name'].tolist()
            
            # Parse log
            log_path = d / "agents.out.0"
            if not log_path.exists():
                print(f"Missing log for {d.name}")
                continue
                
            arrivals = {}
            with open(log_path, 'r') as f:
                header = f.readline().replace('#','').strip().split(',')
                try:
                    # Robust column finding
                    cols = [c.strip() for c in header]
                    t_idx = [i for i, c in enumerate(cols) if 'time' in c][0]
                    id_idx = [i for i, c in enumerate(cols) if 'agentid' in c][0]
                    loc_idx = [i for i, c in enumerate(cols) if 'location' in c and 'original' not in c][0]
                    
                    for line in f:
                        parts = line.split(',')
                        if len(parts) < len(cols): continue
                        
                        try:
                            t = int(parts[t_idx])
                            aid = parts[id_idx].strip()
                            loc = parts[loc_idx].strip()
                            
                            if loc in safe_zones and aid not in arrivals:
                                arrivals[aid] = t
                        except ValueError:
                            continue
                            
                except Exception as e:
                    print(f"Error parsing log {d.name}: {e}")
                    continue
            
            avg_time = np.mean(list(arrivals.values())) if arrivals else 0
            count = len(arrivals)
            
            results.append({
                "Name": d.name,
                "AvgTime": avg_time,
                "Arrivals": count,
                "Topology": topo_name,
                "N": N,
                "Dense": dense
            })
            print(f"Processed {d.name}: {count} arrivals, AvgTime {avg_time:.1f}")
            
        except Exception as e:
            print(f"Skipping {d.name}: {e}")
            
    df = pd.DataFrame(results)
    df.to_csv("systematic_results/summary_fixed.csv", index=False)
    print("Done.")

if __name__ == "__main__":
    reanalyze()


