from prefect import flow


@flow
def hello_world():
    print(f"Hello kunkun from Prefect! 🤗")

if __name__ == "__main__":
    hello_world()