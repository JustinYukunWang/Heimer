"""
Script to fetch match IDs for players in a CSV file.
"""
import argparse
import os
import logging
from backend.fetch_functions.fetch_match_ids import process_player_csv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch match IDs for players in a CSV file")
    
    parser.add_argument(
        "--input", 
        required=True,
        help="Path to the input CSV file containing player information"
    )
    parser.add_argument(
        "--output", 
        help="Path to the output CSV file to store match IDs (default: match_ids.csv in the same directory as input)"
    )
    parser.add_argument(
        "--count", 
        type=int,
        default=20,
        help="Number of matches to fetch per player (default: 20, max: 100)"
    )
    parser.add_argument(
        "--queue", 
        type=int,
        help="Queue type (e.g., 420 for ranked solo/duo)"
    )
    
    args = parser.parse_args()
    
    # Set default output file if not provided
    if not args.output:
        input_dir = os.path.dirname(args.input)
        input_name = os.path.basename(args.input).split('.')[0]
        args.output = os.path.join(input_dir, f"{input_name}_match_ids.csv")
    
    logger.info(f"Processing players from {args.input}")
    logger.info(f"Output will be saved to {args.output}")
    
    # Process the CSV file
    num_matches = process_player_csv(args.input, args.output, args.count, args.queue)
    
    logger.info(f"Successfully fetched {num_matches} unique match IDs")
    logger.info(f"Output saved to {args.output}")
