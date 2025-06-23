import os
import shutil
import json
import time
import concurrent.futures
from datetime import datetime, timedelta
import argparse
from multiprocessing import Manager, Pool
import gzip
import logging
import requests
from requests.auth import HTTPBasicAuth

MAX_PROCESSES = 5
DATA_DICT = {}
DATA_DICT_LOCK = concurrent.futures.ThreadPoolExecutor(max_workers=1)
LAST_CHANGE_TIME = datetime.now()


def json_from_gzip_file(input_filepath):
    try:
        with gzip.open(input_filepath, "rt", encoding="utf-8") as gzip_file:
            json_data = gzip_file.read()
        return json.loads(json_data)
    except Exception as e:
        logging.error(f"Error loading JSON from gzipped file: {e}")
        raise


def send_to_fhir_server(bundle, args):
    try:
        logging.debug("Sending bundle to FHIR...")
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            args.fhirurl,
            json=bundle,
            headers=headers,
            auth=HTTPBasicAuth(args.fhiruser, args.fhirpw),
        )
        response.raise_for_status()  # Raise an exception for non-2xx responses
        logging.debug(f"Response sending bundle: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending bundle to FHIR server: {e}")
        raise


def process_file(data_dict, file_path, args):
    logger = logging.getLogger()
    logger.setLevel(get_numeric_log_level(args.log_level))
    logging.info(f"SENDING TO FHIR - Processing file: {file_path}")

    bundle = {}
    json_loaded_success = False
    cur_try = 0
    n_retries = 5
    while cur_try < n_retries and not json_loaded_success:
        try:
            if args.gzippedfiles:
                bundle = json_from_gzip_file(file_path)
            else:
                with open(file_path, "r") as json_file:
                    bundle = json.load(json_file)
            json_loaded_success = True
        except Exception as e:
            cur_try += 1
            logging.debug(
                f"Error loading JSON from file, attempt {cur_try} of {n_retries}: {e}"
            )
            time.sleep(5)

    send_to_fhir_server(bundle, args)

    if args.removeinputfiles:
        try:
            os.remove(file_path)
        except OSError as e:
            logging.error(f"Error removing input file: {e}")
            raise

    data_dict[file_path] = True
    return True


def process_directory(data_dict, args):
    global LAST_CHANGE_TIME

    multiple_results = []
    all_files = [
        os.path.join(root, file)
        for root, _, files in os.walk(args.inputdir)
        for file in files
    ]

    with Pool(processes=4) as pool:
        for filename in all_files:
            if filename not in data_dict:
                LAST_CHANGE_TIME = datetime.now()
                multiple_results.append(
                    pool.apply_async(process_file, (data_dict, filename, args))
                )

        try:
            results = [res.get(timeout=30) for res in multiple_results]
            logging.debug(results)
        except concurrent.futures.TimeoutError:
            logging.error("Timeout occurred while processing files.")
            raise


def get_numeric_log_level(log_level):
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    return numeric_level


def str_to_bool(s):
    return s.lower() in ["true", "yes", "1"]


def get_fhir_resources(base_url):
    """
    Fetch and return the available FHIR resources from a FHIR server.

    Args:
        base_url (str): Base URL of the FHIR server.

    Returns:
        list: List of FHIR resource types.

    """
    capability_statement_url = f"{base_url}/metadata"
    response = requests.get(capability_statement_url)

    if response.status_code != 200:
        print(
            f"Error: Unable to fetch CapabilityStatement. Status code: {response.status_code}"
        )
        return []

    capability_statement = response.json()
    resources = capability_statement.get("rest", [{}])[0].get("resource", [])

    return [resource.get("type", "") for resource in resources]


def get_resource_count(fhir_url, resource_type):
    """
    Get the count of a specific FHIR resource type.

    Args:
        fhir_url (str): Base URL of the FHIR server.
        resource_type (str): FHIR resource type.

    Returns:
        int: Count of the specified resource type.

    """
    search_url = f"{fhir_url}/{resource_type}?_summary=count"
    response = requests.get(search_url)
    if response.status_code == 200:
        return response.json().get("total", 0)
    else:
        print(
            f"Error fetching count for {resource_type}. Status code: {response.status_code}"
        )
        return 0


def print_fhir_resources_count(fhir_url):
    """
    Print the count of each FHIR resource available on the FHIR server.

    Args:
        fhir_url (str): Base URL of the FHIR server.

    """
    fhir_resources = get_fhir_resources(fhir_url)

    print("Available FHIR Resources:")
    for resource_type in fhir_resources:
        resource_count = get_resource_count(fhir_url, resource_type)
        if resource_count > 0:
            print(f"{resource_type}: {resource_count}")


def main():
    parser = argparse.ArgumentParser(
        description="Continuously process files in a directory."
    )
    parser.add_argument(
        "--log-level",
        default="info",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Set the logging level",
    )
    parser.add_argument(
        "--metadatadir",
        default="generated-testdata/metadata",
        help="Path to the directory to be processed.",
    )
    parser.add_argument(
        "--inputdir",
        default="generated-testdata/fhir-processed",
        help="Path to the directory to be processed.",
    )
    parser.add_argument(
        "--timeout", type=int, default=5, help="Timeout in minutes for no new files."
    )
    parser.add_argument(
        "--gzippedfiles", type=str_to_bool, help="Enable reading of gzipped files"
    )
    parser.add_argument(
        "--removeinputfiles",
        type=str_to_bool,
        help="Enable the continuous removing of input files",
    )
    parser.add_argument(
        "--fhirurl",
        default="http://localhost:8080/fhir",
        help="FHIR base url - commonly ends with /fhir",
    )
    parser.add_argument("--fhiruser", default="", help="FHIR Basic auth user")
    parser.add_argument("--fhirpw", default="", help="FHIR Basic auth password")

    args = parser.parse_args()
    logging.basicConfig(level=get_numeric_log_level(args.log_level))
    manager = Manager()
    data_dict = manager.dict()

    while True:
        try:
            process_directory(data_dict, args)
            if (datetime.now() - LAST_CHANGE_TIME) > timedelta(minutes=args.timeout):
                break
            time.sleep(10)
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            time.sleep(10)  # Add some delay before retrying

    processed_data_info = dict(data_dict)
    if args.removeinputfiles:
        try:
            shutil.rmtree(args.inputdir)
        except Exception as e:
            logging.error(f"Error removing input directory: {e}")

    with open(f"{args.metadatadir}/loaded_data_info.json", "w") as json_file:
        json.dump(processed_data_info, json_file, indent=4)

    # Print FHIR resources and their counts
    try:
        print_fhir_resources_count(args.fhirurl)
    except Exception as e:
        logging.error(f"An error occurred while printing FHIR resources count: {e}")


if __name__ == "__main__":
    main()
