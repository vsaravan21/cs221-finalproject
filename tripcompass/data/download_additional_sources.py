"""
Helper script to download additional San Francisco datasets.

This script provides instructions and functions to download datasets from
SF Open Data Portal that can enhance the POI catalog.

Usage:
    python -m tripcompass.data.download_additional_sources
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import requests

from tripcompass import config


# URLs for SF Open Data Portal datasets
SF_OPEN_DATA_DATASETS = {
    "film_locations": {
        "url": "https://data.sfgov.org/api/views/yitu-d5am/rows.csv",
        "description": "Film Locations in San Francisco since 1924",
        "filename": "Film_Locations_in_San_Francisco.csv",
    },
    # Add more datasets here as needed
    # Example:
    # "historic_resources": {
    #     "url": "https://data.sfgov.org/api/views/...",
    #     "description": "Historic Resources in San Francisco",
    #     "filename": "Historic_Resources.csv",
    # },
}


def download_dataset(url: str, output_path: Path) -> bool:
    """Download a dataset from a URL and save it to the specified path."""
    try:
        print(f"Downloading from {url}...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(response.content)
        print(f"✅ Saved to {output_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to download: {e}")
        return False


def download_all_datasets() -> Dict[str, bool]:
    """Download all configured datasets."""
    results = {}
    config.ensure_directories()
    
    for dataset_name, dataset_info in SF_OPEN_DATA_DATASETS.items():
        output_path = config.DATA_DIR / dataset_info["filename"]
        if output_path.exists():
            print(f"⏭️  {dataset_name} already exists at {output_path}")
            results[dataset_name] = True
            continue
        
        print(f"\n📥 Downloading {dataset_name}: {dataset_info['description']}")
        success = download_dataset(dataset_info["url"], output_path)
        results[dataset_name] = success
    
    return results


def print_manual_download_instructions() -> None:
    """Print instructions for manually downloading datasets."""
    print("\n" + "=" * 70)
    print("MANUAL DOWNLOAD INSTRUCTIONS")
    print("=" * 70)
    print("\nTo add more datasets, visit the SF Open Data Portal:")
    print("  https://datasf.org/opendata/")
    print("\nRecommended datasets to search for:")
    print("  - Film Locations")
    print("  - Historic Resources")
    print("  - Cultural Districts")
    print("  - Farmers Markets")
    print("  - Public Art")
    print("\nFor each dataset:")
    print("  1. Find the dataset on data.sfgov.org")
    print("  2. Click 'Export' → 'CSV'")
    print("  3. Save to tripcompass/data/ directory")
    print("  4. Update download_additional_sources.py with the dataset URL")
    print("=" * 70)


def main() -> None:
    """Main entry point."""
    print("SF Open Data Dataset Downloader")
    print("=" * 70)
    
    if not SF_OPEN_DATA_DATASETS:
        print("No datasets configured. See print_manual_download_instructions()")
        print_manual_download_instructions()
        return
    
    results = download_all_datasets()
    
    print("\n" + "=" * 70)
    print("DOWNLOAD SUMMARY")
    print("=" * 70)
    for name, success in results.items():
        status = "✅ Success" if success else "❌ Failed"
        print(f"  {name}: {status}")
    
    failed = [name for name, success in results.items() if not success]
    if failed:
        print(f"\n⚠️  {len(failed)} dataset(s) failed to download.")
        print_manual_download_instructions()
    else:
        print("\n✅ All datasets downloaded successfully!")
        print("\nNext step: Run 'python -m tripcompass.data.build_pois' to rebuild the POI catalog.")


if __name__ == "__main__":
    main()

