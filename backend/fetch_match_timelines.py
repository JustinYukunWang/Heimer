"""
Script to fetch timeline data for multiple match IDs.
This script extracts player gold, items, and KDA at 1, 5, 10, 15, and 20 minute timestamps.
"""
import argparse
import os
import logging
from backend.fetch_functions.history_check import process_match_list

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def read_match_ids_from_file(file_path):
    """
    Read match IDs from a file, one per line.

    Args:
        file_path: Path to the file containing match IDs

    Returns:
        List of match IDs
    """
    try:
        with open(file_path, 'r') as f:
            match_ids = [line.strip() for line in f if line.strip()]
        logger.info(f"Read {len(match_ids)} match IDs from {file_path}")
        return match_ids
    except Exception as e:
        logger.error(f"Error reading match IDs from {file_path}: {e}")
        return []

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch timeline data for League of Legends matches")

    # Add arguments
    parser.add_argument(
        "--match-ids",
        nargs="+",
        help="One or more match IDs to process"
    )
    parser.add_argument(
        "--file",
        help="File containing match IDs, one per line"
    )
    # Region parameter is no longer used but kept for backward compatibility
    parser.add_argument(
        "--region",
        default="NA",
        help="Region for the matches (not used, kept for backward compatibility)"
    )
    parser.add_argument(
        "--output-dir",
        default="data/match_timelines",
        help="Directory to save the output files (default: data/match_timelines)"
    )

    args = parser.parse_args()

    # Get match IDs from arguments or file
    match_ids = []
    if args.match_ids:
        match_ids.extend(args.match_ids)

    if args.file:
        file_match_ids = read_match_ids_from_file(args.file)
        match_ids.extend(file_match_ids)

    if not match_ids:
        logger.error("No match IDs provided. Use --match-ids or --file")
        parser.print_help()
        exit(1)

    # Remove duplicates
    match_ids = list(set(match_ids))
    logger.info(f"Processing {len(match_ids)} unique match IDs")

    # Process match IDs
    successful = process_match_list(match_ids, output_path=args.output_dir)

    # Print summary
    logger.info(f"Successfully processed {successful}/{len(match_ids)} matches")
    logger.info(f"Output saved to {os.path.abspath(args.output_dir)}")
