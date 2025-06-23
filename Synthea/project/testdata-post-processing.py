import os
import shutil
import json
import csv
import time
from datetime import datetime, timedelta
import argparse
from multiprocessing import Pool, Manager
import gzip
import logging

MAX_PROCESSES = 5
LAST_CHANGE_TIME = datetime.now()


def gzip_json_to_file(json_data, output_filename):
    json_bytes = json_data.encode("utf-8")
    try:
        with gzip.open(f"{output_filename}.gz", "wb") as f_out:
            f_out.write(json_bytes)
    except Exception as e:
        logging.error(f"Error gzipping JSON to file: {e}")
        raise


def process_entry(resource_overview, entry):
    try:
        resource = entry["resource"]
        res_type = resource["resourceType"]

        if "code" in resource:
            code = resource["code"]["coding"][0]["code"]

            if code not in resource_overview[res_type]:
                resource_overview[res_type][code] = {
                    "count": 1,
                    "code": resource["code"],
                    "type": res_type,
                }
            else:
                resource_overview[res_type][code]["count"] += 1
    except Exception as e:
        logging.error(f"Error processing entry: {e}")
        raise


def remove_non_mii_resources(bundle, relevant_resources):
    try:
        for del_index in reversed(range(len(bundle["entry"]))):
            resource = bundle["entry"][del_index]["resource"]
            if resource["resourceType"] not in relevant_resources:
                logging.debug(
                    f'Removing non MII resource of type: {resource["resourceType"]}'
                )
                del bundle["entry"][del_index]
    except Exception as e:
        logging.error(f"Error removing non-MII resources: {e}")
        raise


def process_bundle(bundle, relevant_resources):
    temp_res_overview = {res_type: {} for res_type in relevant_resources}

    try:
        remove_non_mii_resources(bundle, relevant_resources)

        for entry in bundle["entry"]:
            process_entry(temp_res_overview, entry)
    except Exception as e:
        logging.error(f"Error processing bundle: {e}")
        raise

    return temp_res_overview


def update_overview_dict(data_dict, resource_overview, lock):
    try:
        with lock:
            for res_type, codes in resource_overview.items():
                for code, details in codes.items():
                    if code not in data_dict["resourceOverview"][res_type]:
                        data_dict["resourceOverview"][res_type][code] = details
                    else:
                        data_dict["resourceOverview"][res_type][code][
                            "count"
                        ] += details["count"]
    except Exception as e:
        logging.error(f"Error updating overview dictionary: {e}")
        raise


def write_processed_bundle_to_file(args, filename, bundle):
    try:
        output_path = os.path.join(args.outputdir, filename)

        logging.debug(f"Writing data to: {output_path}")
        if args.gzipfiles:
            gzip_json_to_file(json.dumps(bundle), output_path)
        else:
            with open(output_path, "w") as output_file:
                json.dump(bundle, output_file)
    except Exception as e:
        logging.error(f"Error writing processed bundle to file: {e}")
        raise


def remove_file_and_dirs(base_dir, file_path):
    try:
        os.remove(file_path)
    except Exception as e:
        logging.error(f"Error removing file: {e}")
        raise


def process_file(lock, data_dict, file_path, args):
    try:
        logger = logging.getLogger()
        logger.setLevel(get_numeric_log_level(args.log_level))
        logging.info(f"POSTPROCESSING FILE - Processing file: {file_path}")

        filename = os.path.basename(file_path)
        cur_bundle = {}
        json_loaded_success = False
        cur_try = 0
        n_retries = 5
        while cur_try < n_retries and not json_loaded_success:
            try:
                with open(file_path, "r") as json_file:
                    cur_bundle = json.load(json_file)
                json_loaded_success = True
            except Exception:
                cur_try += 1
                logging.debug(
                    f"Hit running condition opening half written file, try:{cur_try} of {n_retries}"
                )
                json_loaded_success = False
                time.sleep(5)

        resource_overview = process_bundle(
            cur_bundle, data_dict["resourceOverview"].keys()
        )
        update_overview_dict(data_dict, resource_overview, lock)
        write_processed_bundle_to_file(args, filename, cur_bundle)

        if args.removeinputfiles:
            remove_file_and_dirs(args.inputdir, file_path)

        return True
    except Exception as e:
        logging.error(f"Error processing file: {e}")
        raise


def process_directory(lock, data_dict, args):
    global LAST_CHANGE_TIME

    try:
        multiple_results = []
        all_files = [
            os.path.join(root, file)
            for root, _, files in os.walk(args.inputdir)
            for file in files
        ]

        with Pool(processes=4) as pool:
            for filename in all_files:
                if filename not in data_dict["processedFiles"]:
                    LAST_CHANGE_TIME = datetime.now()
                    multiple_results.append(
                        pool.apply_async(
                            process_file, (lock, data_dict, filename, args)
                        )
                    )

            logging.debug([res.get(timeout=30) for res in multiple_results])
    except Exception as e:
        logging.error(f"Error processing directory: {e}")
        raise


def get_numeric_log_level(log_level):
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    return numeric_level


def write_info_as_csv(output_dir, resource_overview):
    try:
        csv_file_path = os.path.join(output_dir, "resources-info.csv")

        with open(csv_file_path, mode="w", newline="") as file:
            writer = csv.writer(file)
            header = ["Resource", "System", "Code", "Count"]
            writer.writerow(header)

            for res_type, codes in resource_overview.items():
                for code, details in sorted(
                    codes.items(), key=lambda x: x[1]["count"], reverse=True
                ):
                    code = details["code"]["coding"][0]["code"]
                    system = details["code"]["coding"][0]["system"]
                    count = details["count"]
                    writer.writerow([res_type, system, code, count])
    except Exception as e:
        logging.error(f"Error writing info as CSV: {e}")
        raise


def str_to_bool(s):
    return s.lower() in ["true", "yes", "1"]


def main():
    try:
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
            default="generated-testdata/fhir",
            help="Path to the directory to be processed.",
        )
        parser.add_argument(
            "--outputdir",
            default="generated-testdata/fhir-processed",
            help="Path to the directory where to save processed data.",
        )
        parser.add_argument(
            "--timeout",
            type=int,
            default=5,
            help="Timeout in minutes for no new files.",
        )
        parser.add_argument(
            "--gzipfiles", type=str_to_bool, help="Enable the gzipping of files"
        )
        parser.add_argument(
            "--removeinputfiles",
            type=str_to_bool,
            help="Enable the continuous removing of input files",
        )
        parser.add_argument(
            "--relevant-resources",
            default="Patient,Encounter,Observation,Condition,DiagnosticReport,Medication,MedicationAdministration,Procedure",
            help="Comma separated list of resource types relevant for testdata",
        )

        args = parser.parse_args()
        logging.basicConfig(level=get_numeric_log_level(args.log_level))

        manager = Manager()
        lock = manager.Lock()
        data_dict = manager.dict()
        data_dict["resourceOverview"] = {
            res_type: {} for res_type in args.relevant_resources.split(",")
        }
        data_dict["processedFiles"] = {}

        while True:
            process_directory(lock, data_dict, args)

            if (datetime.now() - LAST_CHANGE_TIME) > timedelta(minutes=args.timeout):
                break

            time.sleep(10)

        processed_data_info = dict(data_dict)

        if args.removeinputfiles:
            shutil.rmtree(args.inputdir)

        with open(
            os.path.join(args.metadatadir, "processed_data_info.json"), "w"
        ) as json_file:
            json.dump(processed_data_info, json_file, indent=4)

        write_info_as_csv(args.metadatadir, processed_data_info["resourceOverview"])

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise


if __name__ == "__main__":
    main()
