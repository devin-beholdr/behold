from argparse import ArgumentParser
import os


def cli():
    # Create a parser object
    parser = ArgumentParser(description="A simple command-line parser")
    # Add command-line arguments
    parser.add_argument("--username", help="(str): The username to search for.", required=True)
    parser.add_argument("--nsfw", help="(true/false): Include NSFW websites in search.", required=False)
    parser.add_argument("--output_filepath", help="(str): The filepath to save the results of the search as csv.",
                        required=False)
    parser.add_argument("--threads", help="(int): Number of threads to run for threading. Defaults to 1.",
                        required=False)
    # Parse the command-line arguments
    args = parser.parse_args()

    return args


def parse_nsfw_arg(nsfw_string: str) -> bool:
    if not nsfw_string:
        return False
    if nsfw_string.lower() == "true":
        return True
    else:
        return False


def parse_threads_arg(threads: str) -> int:
    if not threads:
        return 1
    try:
        return int(threads)
    except ValueError:
        raise ValueError("The \"threads\" arg must be an integer.")
    except TypeError:
        raise ValueError("The \"threads\" arg must be an integer.")


def parse_filepath_arg(filepath: str) -> str:
    if not filepath:
        return ""

    file = open(filepath, 'w')
    file.close()
    if os.path.exists(filepath):
        os.remove(filepath)
    return filepath

