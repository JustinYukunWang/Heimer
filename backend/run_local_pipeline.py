"""
Script to run the League of Legends data pipeline locally.
Supports one-time execution or scheduled daily updates.
"""
import argparse
import time
import datetime
import logging
from backend.fetch_functions.simple_local_pipeline import run_pipeline

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_once(ranks=None):
    """Run the pipeline once with the specified ranks."""
    print("Starting League of Legends data pipeline...")
    results = run_pipeline(ranks)

    print("\nPipeline execution completed!")
    for rank, result in results.items():
        print(f"- {rank}: {result}")

    return results

def run_daily(ranks=None, run_time="02:00"):
    """
    Run the pipeline daily at the specified time.

    Args:
        ranks: List of ranks to fetch
        run_time: Time to run in 24-hour format (HH:MM)
    """
    logger.info(f"Scheduled to run daily at {run_time}")

    try:
        hour, minute = map(int, run_time.split(":"))
    except ValueError:
        logger.error(f"Invalid time format: {run_time}. Using default 02:00.")
        hour, minute = 2, 0

    while True:
        now = datetime.datetime.now()
        # Calculate time until next run
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_run <= now:
            # If the time has already passed today, schedule for tomorrow
            next_run = next_run + datetime.timedelta(days=1)

        # Calculate seconds until next run
        wait_seconds = (next_run - now).total_seconds()

        logger.info(f"Next run scheduled at {next_run.strftime('%Y-%m-%d %H:%M:%S')} "
                   f"({wait_seconds/3600:.1f} hours from now)")

        # Sleep until the scheduled time
        time.sleep(wait_seconds)

        # Run the pipeline
        logger.info("Running scheduled pipeline update")
        results = run_pipeline(ranks)

        # Log results
        for rank, result in results.items():
            logger.info(f"{rank}: {result}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the League of Legends data pipeline")
    parser.add_argument(
        "--ranks",
        nargs="+",
        choices=["DIAMOND", "MASTER", "GRANDMASTER", "CHALLENGER"],
        help="Ranks to fetch (default: all ranks)"
    )
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Run the pipeline on a daily schedule"
    )
    parser.add_argument(
        "--time",
        default="02:00",
        help="Time to run the scheduled pipeline (24-hour format, HH:MM)"
    )

    args = parser.parse_args()

    if args.schedule:
        print(f"Setting up daily schedule at {args.time}...")
        print("Press Ctrl+C to stop the scheduler")
        try:
            run_daily(args.ranks, args.time)
        except KeyboardInterrupt:
            print("\nScheduler stopped")
    else:
        run_once(args.ranks)
