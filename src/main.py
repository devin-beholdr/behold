import json
import os
import re

import pydantic
import requests
import argparse

from typing import List, Match
from Behold.src.models.site import Site

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


def generate_site_objects() -> List[Site]:
    """
        Convert the json list of site information into a list of Site objects.
    """
    config: json = load_config()
    sites_json: json = read_json_file(config["sites_json_filepath"])
    sites_nsfw_dict = generate_site_nsfw_lookup_dict()
    sites: List[Site] = []
    for site, data in sites_json.items():
        temp_url = data.get("urlMain", None)
        temp_nsfw = sites_nsfw_dict.get(parse_url_domain(temp_url), None)
        try:
            temp_site = Site(
                name=site,
                user_url=data.get("url", None),
                main_url=temp_url,
                error_url=data.get("errorUrl", None),
                error_type=data.get("errorType", None),
                users_found=[],
                nsfw=temp_nsfw,
                error_message=data.get("errorMsg", None)
            )
        except pydantic.ValidationError as e:
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

def determine_compatiable_encoding(byte_data: bytes, string_data: str) -> str:
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

    # if "instagram" != parse_url_domain(site.main_url):
    #     return False
    if response.status_code == 404:
        return False
    # If a Site error message is set, check it's existence in response
    if site.error_message:
        if site.error_message.encode(response.encoding) in response.content:
            return True
    if response.status_code == 200:
        return True
    return False


def cli():
    # Create a parser object
    parser = argparse.ArgumentParser(description="A simple command-line parser")

    # Add command-line arguments
    parser.add_argument("--username", help="String: The username to search for.", required=True)
    parser.add_argument("--nsfw", help="true/false: Include NSFW websites in search.", required=False)
    parser.add_argument("--output_filepath", help="string: The filepath to save the results of the search as csv.",
                        required=False)

    # Parse the command-line arguments
    args = parser.parse_args()

    # Access the values of the arguments
    username: str = args.username
    nsfw: bool = args.nsfw
    output_filepath: str = args.output_filepath

    # Perform some operation (in this example, we'll just print the input and output paths)
    # TODO: Setup parsing these commands into calling functions.
    print(f"username file: {username}")
    print(f"nsfw file: {nsfw}")
    print(f"output_filepath file: {output_filepath}")

def main():
    cli()


if __name__ == "__main__":
    main()

# env_setup()
# sites: List[Site] = generate_site_objects()
# for site in sites:
#     username = "dogle"
#     user_found: bool = check_website_for_user(site, username)
#     site.users_found.append(username)
#     print(site.user_url.format(username) + " : {}".format(user_found))