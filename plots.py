import os
import pandas as pd
from pathlib import Path
from datetime import datetime
import re
import subprocess
import json

# Define default fields at the module level (add this near the top of the file)
DEFAULT_FIELDS = ['FileName', 'BandName', 'CentralWavelength', 'WavelengthFWHM']

def parse_directory_structure(base_path):
    """
    Parse directory structure PlotID/YYYYMMDD into a pandas DataFrame
    
    Args:
        base_path (str): Base directory path containing PlotID directories
        
    Returns:
        pd.DataFrame: DataFrame with columns ['plot_id', 'visit_date', 'full_path']
    """
    
    data = []
    base_path = Path(base_path)
    
    # Pattern to match YYYYMMDD format
    date_pattern = re.compile(r'^\d{8}$')
    
    # Walk through the directory structure
    for plot_dir in base_path.iterdir():
        if plot_dir.is_dir():
            plot_id = plot_dir.name
            
            # Look for date subdirectories
            for date_dir in plot_dir.iterdir():
                if date_dir.is_dir() and date_pattern.match(date_dir.name):
                    try:
                        # Parse the date as pandas datetime (not just date)
                        date_str = date_dir.name
                        visit_date = pd.to_datetime(date_str, format='%Y%m%d')
                        
                        data.append({
                            'plot_id': plot_id,
                            'visit_date': visit_date,
                            # 'date_string': date_str,
                            'full_path': str(date_dir),
                            # 'relative_path': f"{plot_id}/{date_str}"
                        })
                        
                    except ValueError:
                        print(f"Warning: Could not parse date {date_dir.name} in {plot_id}")
    
    return pd.DataFrame(data)

# Quick analysis function
def info(df):
    """Print basic info about the plot visits"""
    print("=== Plot Visit Summary ===\n")
    print(f"Total visits: {len(df)}")
    print(f"Unique plots: {df['plot_id'].nunique()}")
    print(f"Date range: {df['visit_date'].min().date()} to {df['visit_date'].max().date()}")
    print(f"Years: {sorted(df['year'].unique())}")
    
    # Display software version info if available
    if 'SwVersion' in df.columns:
        sw_versions = df['SwVersion'].dropna().unique()
        if len(sw_versions) > 0:
            print("\n=== Software Version Info ===")
            version_counts = df['SwVersion'].value_counts()
            for version, count in version_counts.items():
                if pd.notna(version):
                    print(f"  {version}: {count} visits")
    
    # # Top plots by visit count
    # top_plots = df['plot_id'].value_counts().head(5)
    # print(f"\nTop 5 plots by visits:")
    # for plot, count in top_plots.items():
    #     print(f"  {plot}: {count} visits")
    
    # return df.groupby('plot_id').size().describe()

# Main execution
if __name__ == "__main__":
    # Replace with your actual base directory path
    BASE_DIR = "."  # Current directory, change as needed
    
    # Parse the directory structure
    df = parse_directory_structure(BASE_DIR)
    
    if df.empty:
        print("No valid plot directories found!")
        print("Make sure your directory structure follows: PlotID/YYYYMMDD")
    else:
        # Display the DataFrame
        print("Directory Structure DataFrame:")
        print(df.head(10))
        print(f"\nDataFrame shape: {df.shape}")
        print(f"\nColumn types:")
        print(df.dtypes)
        
        # Add some useful derived columns
        # df['year'] = df['visit_date'].dt.year
        # df['month'] = df['visit_date'].dt.month
        # df['day_of_year'] = df['visit_date'].dt.dayofyear
        # df['days_since_first'] = (df['visit_date'] - df['visit_date'].min()).dt.days
        
        # Sort by plot_id and visit_date
        df_sorted = df.sort_values(['plot_id', 'visit_date'])
        
        # Example filtering and analysis
        print("\n=== Example Operations ===")
        
        # Filter by year
        if df['year'].nunique() > 1:
            latest_year = df['year'].max()
            df_latest_year = df[df['year'] == latest_year]
            print(f"\nVisits in {latest_year}: {len(df_latest_year)}")
        
        # # Group by plot and get visit statistics
        # plot_stats = df.groupby('plot_id').agg({
        #     'visit_date': ['count', 'min', 'max'],
        #     'days_since_first': 'max'
        # }).round(2)
        # plot_stats.columns = ['visit_count', 'first_visit', 'last_visit', 'days_span']
        
        # print("\nPlot visit statistics:")
        # print(plot_stats.head())
        
        # # Find plots with multiple visits
        # multi_visit_plots = plot_stats[plot_stats['visit_count'] > 1]
        # print(f"\nPlots with multiple visits: {len(multi_visit_plots)}")
        
        # # Monthly visit distribution
        # monthly_visits = df.groupby(['year', 'month']).size()
        # print(f"\nMonthly visit distribution:")
        # print(monthly_visits.head(10))

# Utility functions with short names
def filter_date(df, start=None, end=None):
    """Filter plots by date range
    
    Args:
        df (pd.DataFrame): DataFrame containing plot data with a 'visit_date' column
        start (str or datetime, optional): Start date. Accepts any format pandas.to_datetime() understands 
            (e.g., '2023-01-01', 'Jan 1 2023', '20230101')
        end (str or datetime, optional): End date in same format as start
            
    Returns:
        pd.DataFrame: Filtered DataFrame with dates in the specified range
    """
    if start is None and end is None:
        return df
    
    mask = pd.Series(True, index=df.index)
    if start is not None:
        mask &= (df['visit_date'] >= pd.to_datetime(start))
    if end is not None:
        mask &= (df['visit_date'] <= pd.to_datetime(end))
    
    return df.loc[mask]

def filter_year(df, year):
    """Filter by specific year(s)"""
    if isinstance(year, (list, tuple)):
        return df[df['year'].isin(year)]
    return df[df['year'] == year]

def filter_plot(df, plot_id):
    """Get all visits for specific plot(s)"""
    if isinstance(plot_id, (list, tuple)):
        return df[df['plot_id'].isin(plot_id)].sort_values('visit_date')
    return df[df['plot_id'] == plot_id].sort_values('visit_date')

def recent(df, days=30):
    """Get visits from last N days"""
    latest_date = df['visit_date'].max()
    threshold = latest_date - pd.Timedelta(days=days)
    return df[df['visit_date'] > threshold]


def monthly(df):
    """Get monthly visit counts"""
    return df.groupby(['year', 'month']).size().reset_index(name='visits')

def yearly(df):
    """Get yearly visit counts"""
    return df.groupby('year').size().reset_index(name='visits')

def extract_metadata(df, directory_path=None, fields=['SwVersion']):
    """
    Extract metadata from TIF files for existing plot DataFrame
    
    Args:
        df (pd.DataFrame): DataFrame with 'full_path' column
        directory_path (str, optional): If provided, overrides the full_path in the DataFrame
        fields (list): List of metadata fields to extract from TIF files
        
    Returns:
        pd.DataFrame: DataFrame with additional metadata columns
    """
    print(f"Extracting metadata fields {', '.join(fields)} from TIF files...")
    
    # Create a copy to avoid modifying the original
    result_df = df.copy()
    
    # Apply the extract_tif_metadata function to each directory
    metadata_list = []
    for idx, row in df.iterrows():
        path = directory_path if directory_path else row['full_path']
        metadata = extract_tif_metadata(path, fields=fields)
        metadata_list.append(metadata)
        
    # Convert list of dicts to DataFrame and join with main DataFrame
    metadata_df = pd.DataFrame(metadata_list)
    result_df = pd.concat([result_df, metadata_df], axis=1)
    
    # Report on metadata extraction
    for field in fields:
        metadata_found = result_df[field].notna().sum()
        print(f"Found {field} metadata for {metadata_found} of {len(result_df)} plot visits")
    
    return result_df

# Simple wrapper function for easy usage
def extract_tif_metadata(directory_path, fields=['Software', 'SwVersion']):
    """
    Extract metadata from the first TIF file found in a directory or its subdirectories
    
    Args:
        directory_path (str or Path): Directory to search for TIF files
        fields (list): List of metadata fields to extract
        
    Returns:
        dict: Dictionary containing the requested metadata fields
    """
    directory_path = Path(directory_path)
    
    # Search for TIF files (non-recursively first for speed)
    tif_files = list(directory_path.glob('*.tif'))
    # Filter out files ending with _cog.tif
    tif_files = [f for f in tif_files if not f.name.endswith('_cog.tif')]
    
    # If no TIFs found directly, search one level down
    if not tif_files:
        # Common subdirectories where imagery might be stored
        for subdir in ['imagery', 'rgb', 'multispec', 'level0_raw']:
            potential_path = directory_path / subdir
            if potential_path.exists():
                subdir_files = list(potential_path.glob('*.tif'))
                # Filter out files ending with _cog.tif
                subdir_files = [f for f in subdir_files if not f.name.endswith('_cog.tif')]
                tif_files.extend(subdir_files)
        
        # If still not found, search one more level down but limit search
        if not tif_files:
            # Limit recursive search to first 3 non-COG TIFs to avoid performance issues
            all_tifs = list(directory_path.glob('**/*.tif'))
            tif_files = [f for f in all_tifs if not f.name.endswith('_cog.tif')][:3]
    
    # If no TIFs found, return empty metadata
    if not tif_files:
        return {field: None for field in fields}
    
    # Take just the first TIF for speed
    first_tif = str(tif_files[0])
    
    # Run exiftool on the first TIF
    try:
        result = subprocess.run(['exiftool', '-j', first_tif], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and result.stdout.strip():
            metadata = json.loads(result.stdout)[0]  # Get the first (and only) item
            
            # Extract requested fields
            extracted_data = {}
            for field in fields:
                extracted_data[field] = metadata.get(field, None)
            
            # Add filename for reference
            extracted_data['metadata_source'] = Path(first_tif).name
            return extracted_data
        else:
            return {field: None for field in fields}
            
    except (subprocess.SubprocessError, json.JSONDecodeError, IndexError, FileNotFoundError) as e:
        # Handle various potential errors gracefully
        print(f"Warning: Could not extract metadata from {first_tif}: {e}")
        return {field: None for field in fields}

def parse_plots(base_path, include_metadata=False):
    """
    Simple wrapper function that returns a processed DataFrame ready for analysis
    
    Args:
        base_path (str): Path to directory containing PlotID folders
        include_metadata (bool): Whether to extract metadata from TIF files
        
    Returns:
        pd.DataFrame: Processed DataFrame with all derived columns
    """
    # Parse the directory structure
    df = parse_directory_structure(base_path)
    
    if df.empty:
        print("No valid plot directories found!")
        print("Make sure your directory structure follows: PlotID/YYYYMMDD")
        return pd.DataFrame()
    
    # Add derived columns
    df['year'] = df['visit_date'].dt.year
    df['month'] = df['visit_date'].dt.month
    df['day_of_year'] = df['visit_date'].dt.dayofyear
    df['days_since_first'] = (df['visit_date'] - df['visit_date'].min()).dt.days
    
    # Extract metadata if requested
    if include_metadata:
        print("Extracting metadata from TIF files (this may take a while)...")
        # Apply the extract_tif_metadata function to each directory
        metadata_list = []
        for idx, row in df.iterrows():
            metadata = extract_tif_metadata(row['full_path'])
            metadata_list.append(metadata)
            
        # Convert list of dicts to DataFrame and join with main DataFrame
        metadata_df = pd.DataFrame(metadata_list)
        df = pd.concat([df, metadata_df], axis=1)
        
        # Report on metadata extraction
        metadata_found = df['SwVersion'].notna().sum()
        print(f"Found SwVersion metadata for {metadata_found} of {len(df)} plot visits")
    
    # Sort by plot_id and visit_date
    df = df.sort_values(['plot_id', 'visit_date']).reset_index(drop=True)
    
    print(f"Successfully parsed {len(df)} visits from {df['plot_id'].nunique()} plots")
    print(f"Date range: {df['visit_date'].min()} to {df['visit_date'].max()}")
    
    return df


# Then update these function definitions
def extract_multispec_bands(directory_path, fields=None, max_band_number=11):
    """
    Extract metadata from multispectral band TIF files (_1.tif through _N.tif) in a directory
    
    Args:
        directory_path (str or Path): Directory to search for multispectral TIF files
        fields (list, optional): List of metadata fields to extract from TIF files
        max_band_number (int): Maximum band number to look for (default: 11)
        
    Returns:
        dict: Dictionary containing metadata for each band keyed by RigCameraIndex
    """
    # Use default fields if none provided
    if fields is None:
        fields = DEFAULT_FIELDS

    directory_path = Path(directory_path)
    
    # Define common paths for multispectral images
    multispec_paths = [
        directory_path / "imagery" / "multispec" / "level0_raw",
        directory_path / "imagery" / "multispec",
        directory_path / "multispec" / "level0_raw",
        directory_path / "multispec",
        directory_path
    ]
    
    # Find the first valid path that exists
    valid_path = None
    for path in multispec_paths:
        if path.exists():
            valid_path = path
            break
    
    # If no valid path found, return empty result
    if valid_path is None:
        return {}
    
    # Add debug information
    print(f"Searching for TIF files in: {valid_path}")
    
    # Look specifically for files with _1.tif through _N.tif pattern
    band_files = []
    
    # First, try to find files with the specific naming pattern
    for i in range(1, max_band_number + 1):
        # Look for any file ending with _N.tif
        pattern_files = list(valid_path.glob(f"*_{i}.tif"))
        if pattern_files:
            band_files.extend(pattern_files)
    
    # If no band files found with the pattern, search recursively for any TIFs
    if not band_files:
        print("No files with _N.tif pattern found, looking for any TIF files...")
        # Try a recursive search up to 2 levels deep
        all_tifs = []
        for root, dirs, files in os.walk(str(valid_path)):
            depth = len(Path(root).relative_to(valid_path).parts)
            if depth <= 2:  # Only search up to 2 levels deep
                for file in files:
                    if file.lower().endswith('.tif') and not file.lower().endswith('_cog.tif'):
                        all_tifs.append(os.path.join(root, file))
                        if len(all_tifs) >= 11:  # Limit to 11 files
                            break
            if len(all_tifs) >= 11:
                break
        
        band_files = [Path(f) for f in all_tifs]
    
    # If still no files found, return empty result
    if not band_files:
        print("No TIF files found")
        return {}
    
    print(f"Found {len(band_files)} TIF files")
    
    # Try to extract metadata using exiftool
    try:
        # Convert paths to strings for subprocess
        file_paths = [str(f) for f in band_files]
        
        # Try to run exiftool directly on one file first to check if exiftool is working
        first_file = file_paths[0]
        test_result = subprocess.run(['exiftool', '-j', first_file], 
                                   capture_output=True, text=True, timeout=10)
        
        if test_result.returncode != 0:
            print(f"Error: exiftool command failed with return code {test_result.returncode}")
            print(f"Error message: {test_result.stderr}")
            
            # Try to check if exiftool is installed
            try:
                version_check = subprocess.run(['exiftool', '-ver'], 
                                             capture_output=True, text=True, timeout=5)
                if version_check.returncode == 0:
                    print(f"exiftool is installed, version: {version_check.stdout.strip()}")
                else:
                    print("exiftool version check failed")
            except Exception as e:
                print(f"Error checking exiftool version: {e}")
                print("exiftool might not be installed or not in the PATH")
            
            return {}
        
        # If the test worked, proceed with all files
        result = subprocess.run(['exiftool', '-j'] + file_paths,
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0 or not result.stdout.strip():
            print(f"Error extracting metadata from files in {valid_path}: {result.stderr}")
            return {}
        
        # Parse the JSON output
        try:
            metadata_list = json.loads(result.stdout)
            print(f"Successfully extracted metadata for {len(metadata_list)} files")
            
            # Organize by RigCameraIndex (band number)
            bands_metadata = {}
            for metadata in metadata_list:
                rig_index = metadata.get('RigCameraIndex')
                if rig_index is not None:
                    # Extract requested fields
                    band_data = {
                        'filename': Path(metadata.get('SourceFile', '')).name
                    }
                    for field in fields:
                        band_data[field] = metadata.get(field)
                    
                    # Store by RigCameraIndex
                    bands_metadata[rig_index] = band_data
            
            print(f"Found {len(bands_metadata)} bands with RigCameraIndex")
            return bands_metadata
            
        except json.JSONDecodeError:
            print(f"Error decoding JSON output: {result.stdout[:100]}...")
            return {}
        
    except Exception as e:
        print(f"Error running exiftool: {e}")
        return {}

# New function to extract and organize multispectral band metadata across plots
def extract_multispec_analysis(plot_df, fields=None, max_band_number=11):
    """
    Extract and organize multispectral band metadata for all plots in the DataFrame
    
    Args:
        plot_df (pd.DataFrame): DataFrame with plot_id, visit_date, and full_path columns
        fields (list, optional): List of metadata fields to extract from TIF files
        max_band_number (int): Maximum band number to look for (default: 11)
        
    Returns:
        pd.DataFrame: DataFrame with one row per plot visit and columns for each band's metadata
    """
    # Use default fields if none provided
    if fields is None:
        fields = DEFAULT_FIELDS
        
    print(f"Extracting multispectral band metadata for {len(plot_df)} plot visits...")
    print(f"Fields to extract: {', '.join(fields)}")
    print(f"Looking for bands 1 through {max_band_number}")
    
    # Create a list to store data for each plot
    data = []
    total_processed = 0
    
    # Process each plot directory
    for idx, row in plot_df.iterrows():
        plot_id = row['plot_id']
        visit_date = row['visit_date']
        directory = row['full_path']
        
        # Update progress less frequently to reduce console output
        if idx % 5 == 0 or idx == len(plot_df) - 1:
            print(f"Processing {plot_id}/{visit_date.strftime('%Y%m%d')} ({idx+1}/{len(plot_df)})")
        
        # Extract band metadata from this plot directory
        bands_metadata = extract_multispec_bands(directory, fields, max_band_number)
        
        # Create base record with plot info
        record = {
            'plot_id': plot_id,
            'visit_date': visit_date,
            'full_path': directory
        }
        
        # For each rig camera index (band), add its metadata to the record with prefixed column names
        if bands_metadata:
            total_processed += 1
            # First get just general software info from any band
            first_band = next(iter(bands_metadata.values()), {})
            record['Software'] = first_band.get('Software')
            record['SwVersion'] = first_band.get('SwVersion')
            
            # Add each band's metadata with the band index in the column name
            for rig_index, band_data in bands_metadata.items():
                prefix = f"Band{rig_index}_"
                for field in fields:
                    if field != 'RigCameraIndex':  # Already captured in the prefix
                        record[f"{prefix}{field}"] = band_data.get(field)
        
        data.append(record)
        
        # Every 10 plots, report progress
        if idx > 0 and idx % 10 == 0:
            print(f"Progress: {idx}/{len(plot_df)} plots processed ({idx/len(plot_df)*100:.1f}%)")
    
    # Convert to DataFrame
    result_df = pd.DataFrame(data)
    
    print(f"Successfully processed metadata for {total_processed} of {len(result_df)} plot visits")
    return result_df

# New function to compare band assignments across firmware versions
def compare_band_assignments(df):
    """
    Compare band assignments across firmware versions
    
    Args:
        df (pd.DataFrame): DataFrame with extracted multispec band metadata
        
    Returns:
        pd.DataFrame: Summary of band assignments by firmware version
    """
    if 'Software' not in df.columns:
        print("Error: Software column not found in DataFrame")
        return pd.DataFrame()
    
    # Get all unique firmware versions
    versions = df['Software'].dropna().unique()
    
    # Find all band columns
    band_cols = [col for col in df.columns if col.startswith('Band') and col.endswith('_BandName')]
    
    # Create a summary DataFrame
    summary_data = []
    
    # For each version, summarize band assignments
    for version in versions:
        version_df = df[df['Software'] == version]
        
        for band_col in band_cols:
            # Extract band index from column name (e.g., 'Band0_BandName' -> '0')
            band_idx = band_col.split('_')[0].replace('Band', '')
            
            # Count occurrences of each band name
            value_counts = version_df[band_col].value_counts()
            
            # For each band name used for this RigCameraIndex
            for band_name, count in value_counts.items():
                if pd.notna(band_name):
                    wavelength_col = f"Band{band_idx}_CentralWavelength"
                    fwhm_col = f"Band{band_idx}_WavelengthFWHM"
                    
                    # Get the most common wavelength for this band assignment
                    wavelength = version_df[version_df[band_col] == band_name][wavelength_col].mode().iloc[0] if not version_df[version_df[band_col] == band_name][wavelength_col].empty else None
                    
                    # Get the most common FWHM for this band assignment
                    fwhm = version_df[version_df[band_col] == band_name][fwhm_col].mode().iloc[0] if not version_df[version_df[band_col] == band_name][fwhm_col].empty else None
                    
                    summary_data.append({
                        'Software': version,
                        'RigCameraIndex': band_idx,
                        'BandName': band_name,
                        'Count': count,
                        'CentralWavelength': wavelength,
                        'WavelengthFWHM': fwhm
                    })
    
    # Convert to DataFrame and sort
    summary_df = pd.DataFrame(summary_data)
    if not summary_df.empty:
        summary_df = summary_df.sort_values(['Software', 'RigCameraIndex']).reset_index(drop=True)
    
    return summary_df

# Function to create a more compact band assignment table
def create_band_table(df):
    """
    Create a compact table showing band assignments by firmware version
    
    Args:
        df (pd.DataFrame): DataFrame with extracted multispec band metadata
        
    Returns:
        pd.DataFrame: Pivot table of band assignments by firmware version and RigCameraIndex
    """
    # First get the summary data
    summary_df = compare_band_assignments(df)
    
    if summary_df.empty:
        return pd.DataFrame()
    
    # Create a pivot table: Versions as rows, RigCameraIndex as columns
    pivot_df = summary_df.pivot_table(
        index='Software', 
        columns='RigCameraIndex', 
        values='BandName',
        aggfunc=lambda x: x.iloc[0] if len(x) > 0 else None
    )
    
    # Add wavelength information
    wavelength_df = summary_df.pivot_table(
        index='Software', 
        columns='RigCameraIndex', 
        values='CentralWavelength',
        aggfunc=lambda x: x.iloc[0] if len(x) > 0 else None
    )
    
    # Rename columns to add wavelength info
    for col in wavelength_df.columns:
        if col in pivot_df.columns:
            pivot_df[col] = pivot_df[col].astype(str) + " (" + wavelength_df[col].astype(str) + " nm)"
    
    return pivot_df
