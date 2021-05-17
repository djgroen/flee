import os
from pprint import pprint
import pandas as pd


def avg_distance(file_path, camp_name):
    df = pd.read_csv(file_path)
    # filter rwos for agent location == camp_name
    df = df[(df["agent location"] == camp_name) &
            (df["distance_moved_this_timestep"] > 0)
            ]
    df.to_csv(
        os.path.join(os.path.dirname(file_path),
                     "df_{}.csv".format(os.path.basename(
                         file_path).replace(".", "_"))
                     ),
        sep=",",
        mode="w",
        index=False,
        encoding='utf-8'
    )

    return df["distance_travelled"].mean()
