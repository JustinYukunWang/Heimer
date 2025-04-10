from prefect import flow

# Source for the code to deploy (e.g., a GitHub repo)
SOURCE_REPO = 'https://github.com/JustinYukunWang/Heimer.git'

if __name__ == "__main__":
    flow.from_source(
        source=SOURCE_REPO,
        entrypoint="backend/fetch_functions/data_fetch.py:weekly_fetch_all",
    ).deploy(
        name="my-first-deployment",
        work_pool_name="my-work-pool",
        cron="0 * * * *",  # Runs every hour
    )
