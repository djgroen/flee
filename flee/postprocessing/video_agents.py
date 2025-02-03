import pandas as pd
import glob
import os
import re
import argparse
import traceback
from multiprocessing import Pool, cpu_count
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from moviepy.editor import ImageSequenceClip

def process_file(file):
    try:
        df = pd.read_csv(file, index_col=False)
        df.index.name = 'Index'
        df = df[['#time', 'original_location', 'gps_x', 'gps_y', 'current_location']].dropna()
        # df = df.iloc[::2, :]  # Downsample rows by factor of 2
        return df
    except pd.errors.EmptyDataError:
        print(f"Skipping empty file: {file}", flush=True)
        return None
    except Exception as e:
        print(f"Error processing file {file}: {e}", flush=True)
        return None

def clean_location(x):
    if isinstance(x, str):
        return re.sub(r'L:.*?:', '', x)
    print(f"Skipping invalid value: {x}", flush=True)
    return None

def plot_timestep(timestep, agents_data, output_dir):
    try:
        plt.figure(figsize=(12, 8))
        m = Basemap(projection='merc', llcrnrlat=4, urcrnrlat=14, llcrnrlon=2, urcrnrlon=15, resolution='i')
        m.drawcountries()
        m.drawcoastlines()

        original_locations = agents_data[agents_data['#time'] == timestep]
        m.scatter(
            original_locations['gps_x0'].values,
            original_locations['gps_y0'].values,
            latlon=True,
            marker='*',
            color='red',
            label='Original Locations',
            s=90,
            alpha=0.7,
            zorder=3
        )

        current_locations = agents_data[agents_data['#time'] == timestep]
        m.scatter(
            current_locations['gps_y'].values,
            current_locations['gps_x'].values,
            latlon=True,
            marker='o',
            color='green',
            label='Current Locations',
            s=50,
            alpha=0.3,
            zorder=2
        )

        plt.legend(loc='lower left')
        output_path = os.path.join(output_dir, f"agents_timestep_{timestep:03d}.png")
        plt.savefig(output_path)
        plt.close()
        return output_path
    except Exception as e:
        print(f"Error in plot_timestep for timestep {timestep}: {traceback.format_exc()}")
        raise

def process_and_plot(file, locations_df, output_dir):
    try:
        df = process_file(file)
        if df is not None:
            df['current_location_clean'] = df['current_location'].apply(clean_location)
            df = df.merge(
                locations_df[['#name', 'latitude', 'longitude']].rename(
                    columns={'#name': 'original_location', 'latitude': 'gps_y0', 'longitude': 'gps_x0'}
                ),
                on='original_location',
                how='left'
            )
            for timestep in sorted(df['#time'].unique()):
                plot_timestep(timestep, df, output_dir)
                print(f"Generated PNG for timestep {timestep} from file {file}", flush=True)
    except Exception as e:
        print(f"Error in processing file {file}: {traceback.format_exc()}")

def create_video_from_pngs(output_dir, video_filename="agents_movements_animation.mp4"):
    """
    Create a video from PNG files in the output directory.
    """
    try:
        # Specify the pattern for matching PNG files
        file_pattern = os.path.join(output_dir, 'agents_timestep_*.png')
        matching_files = sorted(glob.glob(file_pattern), key=lambda x: int(x.split('_')[-1].split('.')[0]))
        
        if not matching_files:
            print("No PNG files found for video creation.")
            return

        # Create a video clip from the PNGs
        clip = ImageSequenceClip(matching_files, fps=2)  # Adjust fps as needed
        video_path = os.path.join(output_dir, video_filename)
        clip.write_videofile(video_path, codec="libx264")
        print(f"Video created: {video_path}", flush=True)
    except Exception as e:
        print(f"Error during video creation: {traceback.format_exc()}")

def process_files(output_dir):
    try:
        # Use the simulation directory as the working directory
        os.chdir(output_dir)
        
        # Load the locations file
        locations_file = os.path.join(output_dir, "input_csv", "locations.csv")
        if not os.path.exists(locations_file):
            print(f"Error: Required locations.csv not found in '{os.path.join(output_dir, 'input_csv')}'.")
            return
        
        locations_df = pd.read_csv(locations_file)
        
        file_list = sorted(glob.glob('agents.out.*'), key=lambda x: int(x.split('.')[-1]))
        if not file_list:
            print(
                f"No agents.out.* files found in directory '{output_dir}'.\n"
                f"This code is designed to generate PNGs and a video from agents.out.* files.\n"
                f"Please ensure the files are generated in the simulation output directory before running this script."
            )
            return  # Exit the function if no files are found
        
        num_workers = min(cpu_count(), len(file_list))
        print(f"Found {len(file_list)} files and {num_workers} workers to process.")
            
        with Pool(processes=num_workers) as pool:
            try:
                pool.starmap(
                    process_and_plot, 
                    [(file, locations_df, output_dir) for file in file_list]
                )
            except Exception as e:
                print(f"Error occurred during multiprocessing: {e}", flush=True)
            finally:
                pool.close()
                pool.join()

        print("All agents files processed and PNGs generated successfully.")

        # Create video from the generated PNGs
        create_video_from_pngs(output_dir)

    except Exception as e:
        print(f"Error occurred: {traceback.format_exc()}")


if __name__ == "__main__":
    """
    Main function to test the process_files function.
    Accepts a command-line argument for the output directory.
    """
    parser = argparse.ArgumentParser(description="Process Flee simulation output to generate PNGs and video.")
    parser.add_argument(
        "output_dir",
        type=str,
        help="Path to the simulation output directory (e.g., nigeria2024_archer2_128)."
    )
    args = parser.parse_args()

    output_dir = args.output_dir

    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        print(f"Error: The specified directory '{output_dir}' does not exist.")
        exit(1)

    try:
        print(f"Processing files in directory: {output_dir}")
        process_files(output_dir)
        print("Processing completed successfully.")
    except Exception as e:
        print(f"Error in main function: {traceback.format_exc()}")


