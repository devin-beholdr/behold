import csv
import json
import os
import queue
import re
import threading
from queue import Queue

import pydantic
import requests

from typing import List, Match
from argparse import Namespace, ArgumentParser

from src.models.site import Site

def env_setup() -> None:
    os.environ['CONFIG_FILEPATH'] = "config/config.json"


def load_config() -> json:
    try:
        config_file_path: str = os.getenv("CONFIG_FILEPATH")
        config = read_json_file(filepath=config_file_path)
        return config
    except FileNotFoundError:
        raise FileNotFoundError("Unable to find config file.")
    except json.JSONDecodeError:
        raise ValueError("Unable to parse config file.")


def read_json_file(filepath: str) -> json:
    try:
        with open(filepath, "r") as config_file:
            file_json = json.load(config_file)
        return file_json
    except FileNotFoundError:
        raise FileNotFoundError("Unable to find filepath: {}".format(filepath))
    except json.JSONDecodeError:
        raise ValueError("Unable to parse contents of {}".format(filepath))


def generate_site_nsfw_lookup_dict() -> dict:
    config: json = load_config()
    sites_nsfw_json: json = read_json_file(config["sites_nsfw_json_filepath"])
    sites_nsfw_dict = {}
    for data in sites_nsfw_json['data']:

        temp_site: str = data.get('site')
        temp_site_nsfw: bool = data.get('nsfw')
        if temp_site is None or temp_site_nsfw is None:
            continue

        temp_site_domain = parse_url_domain(temp_site)
        if temp_site_domain:
            if temp_site_domain not in sites_nsfw_dict:
                sites_nsfw_dict[temp_site_domain] = temp_site_nsfw

    return sites_nsfw_dict

def parse_url_domain(url: str) -> str:
    match: Match = re.search(r"https?://(?:www\.)?([a-zA-Z0-9.-]+)\.", url)
    result: str = None
    if match:
        temp_site_domain: str = ''.join(match.groups())
        result = temp_site_domain
    return result


def generate_site_objects(nsfw: bool) -> List[Site]:
    """
        Convert the json list of site information into a list of Site objects.
    """
    config: json = load_config()
    sites_json: json = read_json_file(config["sites_json_filepath"])
    sites_nsfw_dict = generate_site_nsfw_lookup_dict()
    sites: List[Site] = []
    for site, data in sites_json.items():
        temp_url = data.get("main_url", None)
        temp_nsfw = sites_nsfw_dict.get(parse_url_domain(temp_url), None)
        try:
            temp_site = Site(
                name=site,
                user_url=data.get("user_url", None),
                main_url=temp_url,
                error_url=data.get("error_url", None),
                error_type=data.get("error_type", None),
                users_found=False,
                nsfw=temp_nsfw,
                error_message=data.get("error_message", None)
            )
        except pydantic.ValidationError as e:
            continue
        if temp_site.nsfw and nsfw is False:
            continue
        sites.append(temp_site)

    return sites


def decode_bytes_with_common_encodings(data: bytes, encodings=None) -> str:
    if encodings is None:
        encodings: json = load_config()["common_encodings"]
    for encoding in encodings:
        try:
            decoded_data = data.decode(encoding)
            return decoded_data
        except UnicodeDecodeError:
            continue

    # If none of the encodings work, you can handle the error or return a default value
    raise ValueError("Unable to decode data with any of the specified encodings")


def determine_encoding_used_for_content(data: bytes) -> str:
    encodings: json = load_config()["common_encodings"]
    for encoding in encodings:
        try:
            decoded_data = data.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            continue

def determine_compatible_encoding(byte_data: bytes, string_data: str) -> str:
    encodings: json = load_config()["common_encodings"]
    for encoding in encodings:
        try:
            decoded_data = byte_data.decode(encoding)
            string_data.encode(encoding=encoding)
            return encoding
        except UnicodeDecodeError:
            continue
        except UnicodeEncodeError:
            continue

def encode_string_to_bytes(string_to_encode: str, encoding: str) -> bytes:
    try:
        return string_to_encode.encode(encoding=encoding)
    except UnicodeEncodeError:
        raise UnicodeEncodeError


def check_website_for_user(site: Site, username: str) -> bool:
    request_url: str = site.user_url.format(username)
    headers = headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)"
    }
    try:
        response = requests.get(request_url, timeout=1, headers=headers)
    except requests.exceptions.ReadTimeout:
        return False
    except requests.exceptions.ConnectTimeout:
        return False
    except requests.exceptions.ConnectionError:
        return False
    except requests.exceptions.RequestException:
        return False

    if response.status_code == 404:
        return False
    # If a Site error message is set, check its existence in response
    if site.error_message:
        if site.error_message.encode(response.encoding) in response.content:
            return False
    if response.status_code == 200:
        return True
    return False


def cli():
    # Create a parser object
    parser = ArgumentParser(description="A simple command-line parser")

    # Add command-line arguments
    parser.add_argument("--username", help="String: The username to search for.", required=True)
    parser.add_argument("--nsfw", help="true/false: Include NSFW websites in search.", required=False)
    parser.add_argument("--output_filepath", help="string: The filepath to save the results of the search as csv.",
                        required=False)
    parser.add_argument("--threads", help="int: Number of threads to run for threading. Defaults to 1.",
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


def main():
    args: Namespace = cli()
    username: str = args.username
    nsfw: bool = parse_nsfw_arg(args.nsfw)
    threads_arg: int = parse_threads_arg(args.threads)
    output_filepath: str = parse_filepath_arg(args.output_filepath)

    sites: List[Site] = generate_site_objects(nsfw)

    results_queue: Queue = queue.Queue()
    results: List = []
    # Search Websites
    if threads_arg > 1:
        threads = []
        site_groups: List[List[Site]] = split_sites_into_groups(sites=sites,threads=threads_arg)
        for site_group in site_groups:
            thread = threading.Thread(target=execute_search, args=(site_group, username, results_queue))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()
    else:
        sites = execute_search(sites=sites, username=username, results_queue=results_queue)
    # Collect results
    while not results_queue.empty():
        result = results_queue.get()
        results.append(result)
    # Store results
    if output_filepath:
        generate_search_results_csv(sites, filepath=output_filepath)


def generate_search_results_csv(sites: List[Site], filepath: str) -> None:
    site_dict_list: List[dict] = []
    for site in sites:
        site_dict_list.append(site.model_dump())

    fieldnames = site_dict_list[0].keys()

    with open(filepath, mode="w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for item in site_dict_list:
            writer.writerow(item)


def split_sites_into_groups(threads: int, sites: List[Site]) -> List[List[Site]]:
    sub_list_length = len(sites) // threads
    split_lists = []

    for i in range(0, len(sites), sub_list_length):
        sub_list = sites[i:i + sub_list_length]
        split_lists.append(sub_list)

    return split_lists

def execute_search(sites: List[Site], username: str, results_queue: Queue) -> List[Site]:
    result_string = "[{}] | {}"
    for site in sites:
        found: bool = check_website_for_user(site=site, username=username)
        user_url: str = site.user_url.format(username)
        temp_result_string: str = ""
        if found:
            temp_result_string = result_string.format("+", user_url)
            site.users_found = True
        else:
            temp_result_string = result_string.format("-", user_url)
        print(temp_result_string)
        results_queue.put(temp_result_string)
    return sites

if __name__ == "__main__":
    env_setup()
    main()
