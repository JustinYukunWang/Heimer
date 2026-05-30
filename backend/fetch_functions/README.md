# League of Legends Data Pipeline

A simple, locally ready data pipeline for fetching League of Legends player data.

## Features

- Fetches player data from different ranks (Diamond I, Master, Grandmaster, Challenger)
- Processes and saves data to CSV files
- Includes error handling and logging
- Easy to run locally

## Getting Started

### Prerequisites

- Python 3.8+
- Required Python packages (see requirements.txt)

### Installation

1. Make sure you have Python and pip installed
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Make sure you have a valid Riot API key in your `.env` file:
   ```
   API_KEY=your-riot-api-key
   ```

### Running the Pipeline

#### One-time Execution

To run the pipeline once for all ranks:

```bash
python -m backend.run_local_pipeline
```

You can specify which ranks to fetch:

```bash
python -m backend.run_local_pipeline --ranks DIAMOND MASTER
```

#### Daily Scheduled Updates

To run the pipeline daily at a specific time (default is 2:00 AM):

```bash
python -m backend.run_local_pipeline --schedule
```

You can specify a different time (24-hour format):

```bash
python -m backend.run_local_pipeline --schedule --time 04:30
```

You can also specify which ranks to fetch with the scheduled updates:

```bash
python -m backend.run_local_pipeline --schedule --ranks DIAMOND MASTER
```

The scheduler will run continuously until you stop it with Ctrl+C.

## Pipeline Structure

- `simple_local_pipeline.py`: Contains the main pipeline functions
- `run_local_pipeline.py`: Script to run the pipeline locally

## Customization

You can customize the pipeline by:

1. Modifying the ranks to fetch in `run_local_pipeline.py`
2. Adding new data processing functions in `simple_local_pipeline.py`
3. Changing the save location in `simple_local_pipeline.py`

## Troubleshooting

- If you encounter rate limiting issues, the pipeline will automatically retry
- Check the console output for detailed logs
- Ensure your API key is valid and has the necessary permissions
