""" Export NWB file with subject information """

import json
import re
import argparse
import warnings
from pathlib import Path
import pytz
import datetime as dt
from datetime import datetime
import logging

from pynwb import NWBHDF5IO, NWBFile
from pynwb.file import Subject
from hdmf_zarr import NWBZarrIO
from uuid import uuid4

# AIND
try:
    from aind_log_utils import log

    HAVE_AIND_LOG_UTILS = True
except ImportError:
    HAVE_AIND_LOG_UTILS = False


DOC_DB_HOST = "api.allenneuraldynamics.org"
DOC_DB_DATABASE = "metadata"
DOC_DB_COLLECTION = "data_assets"

data_folder = Path("../data")
results_folder = Path("../results")

# Create an argument parser
parser = argparse.ArgumentParser(description="Convert subject info to NWB")

# this allows us to pass positional argument (in Code Ocean)
# or optional argument (from API/CLI)
backend_group = parser.add_mutually_exclusive_group()
backend_help = "NWB backend. It can be either 'hdf5' or 'zarr'."
backend_group.add_argument(
    "--backend", choices=["hdf5", "zarr"], default="zarr", help=backend_help
)
backend_group.add_argument("static_backend", nargs="?", help=backend_help)


data_asset_group = parser.add_mutually_exclusive_group()
data_asset_help = (
    "Path to the data asset of the session. When provided, "
    "the metadata are fetched from the AIND metadata database. "
    "If None, and the attached data asset is used to fetch relevant "
    "metadata."
)
data_asset_group.add_argument("--asset-name", type=str, help=data_asset_help)
data_asset_group.add_argument(
    "static_asset_name", nargs="?", help=data_asset_help
)


def run():
    # Parse the command-line arguments
    args = parser.parse_args()
    backend = args.static_backend or args.backend
    asset_name = args.asset_name or args.static_asset_name

    if not results_folder.is_dir():
        results_folder.mkdir(parents=True)

    if asset_name is not None and asset_name == "":
        asset_name = None
    # hot-fix for parameter in pipeline
    if backend == "null":
        backend = args.backend

    if backend == "hdf5":
        io_class = NWBHDF5IO
    elif backend == "zarr":
        io_class = NWBZarrIO
    else:
        raise ValueError(f"Unknown backend: {backend}")

    nwb_input_file = None
    if asset_name is not None:
        from aind_data_access_api.document_db import MetadataDbClient

        doc_db_client = MetadataDbClient(
            host=DOC_DB_HOST,
            database=DOC_DB_DATABASE,
            collection=DOC_DB_COLLECTION,
        )
        if "ecephys" in asset_name or "behavior":
            modality = "ecephys"
        elif "multiplane-ophys" in asset_name:
            modality = "multiplane-ophys"
        subject_match = re.search(r"_(\d+)_", asset_name)
        if subject_match:
            subject_id = subject_match.group(1)
        date_match = re.search(
            r"(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})", asset_name
        )
        if date_match:
            time_str = date_match.group(1)
        else:
            raise Exception("Could not find a date match")

        results = doc_db_client.retrieve_data_asset_records(
            filter_query={
                "$and": [
                    {"_name": {"$regex": f"{modality}.*{time_str}"}},
                    {"subject.subject_id": f"{subject_id}"},
                ]
            },
            paginate_batch_size=100,
        )
        if not results:
            raise Exception("No data records found.")

        data_description = results[0].data_description
        subject_metadata = results[0].subject
        subject_id = subject_metadata["subject_id"]
        session_name = data_description["name"]
    else:
        input_folders = [
            f
            for f in data_folder.iterdir()
            if f.is_dir() and f.suffix != ".nwb"
        ]
        if len(input_folders) == 1:
            input_folder = input_folders[0]
        else:
            input_folder = data_folder
        nwb_files = [f for f in input_folder.iterdir() if f.suffix == ".nwb"]
        if len(nwb_files) == 1:
            nwb_input_file = nwb_files[0]
            asset_name = None
            subject_id = "undefined"
            session_name = "undefined"
        else:
            # In we expect a single data folder as input
            data_assets = [p for p in data_folder.iterdir() if p.is_dir()]
            if len(data_assets) != 1:
                raise ValueError(
                    f"Expected exactly one data asset attached, "
                    f"got {len(data_assets)}"
                )
            data_asset = data_assets[0]
            data_description_file = data_asset / "data_description.json"
            subject_metadata_file = data_asset / "subject.json"
            session_name = "undefined"
            if data_description_file.is_file():
                with open(data_description_file) as f:
                    data_description = json.load(f)
                asset_name = data_description["name"]
                session_name = asset_name
            else:
                data_description = None
                asset_name = None

            subject_id = "undefined"
            if subject_metadata_file.is_file():
                with open(subject_metadata_file) as f:
                    subject_metadata = json.load(f)
                subject_id = subject_metadata["subject_id"]
            else:
                subject_metadata = None

    if HAVE_AIND_LOG_UTILS:
        log.setup_logging(
            "NWB Packaging Subject",
            mouse_id=subject_id,
            session_name=session_name,
        )
    else:
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    if nwb_input_file is not None:
        logging.info(f"Found input NWB file: {nwb_files[0]}")
        # copy NWB input file to results
        nwb_output_file = results_folder / nwb_input_file.name
        asset_name = nwb_input_file.stem
        if nwb_input_file.is_dir():
            backend = "zarr"
            # Zarr format is a directory
            io_class = NWBZarrIO
        else:
            backend = "hdf5"
            # HDF5 format is a file
            io_class = NWBHDF5IO

        with io_class(str(nwb_input_file), mode="r") as io:
            nwbfile_read = io.read()
            subject_read = nwbfile_read.subject
            # Create minimal NWB file with session and subject info
            subject = Subject(
                subject_id=subject_read.subject_id,
                species=subject_read.species,
                sex=subject_read.sex,
                date_of_birth=subject_read.date_of_birth,
                age=subject_read.age,
                genotype=subject_read.genotype,
                description=subject_read.description,
                strain=subject_read.strain,
            )

            nwbfile = NWBFile(
                session_description="NWB file generated by AIND pipeline",
                identifier=str(uuid4()),
                session_start_time=nwbfile_read.session_start_time,
                institution=nwbfile_read.institution,
                subject=subject,
                session_id=nwbfile_read.session_id,
            )
        logging.info(f"\tBackend: {backend}")
        logging.info(f"\tAsset name: {asset_name}")
    else:
        logging.info(f"Creating NWB file")
        logging.info(f"\tBackend: {backend}")
        logging.info(f"\tAsset name: {asset_name}")
        # create NWB file
        if data_description is not None:
            timezone_info = pytz.timezone("US/Pacific")
            date_format_no_tz = "%Y-%m-%dT%H:%M:%S"
            date_format_tz = "%Y-%m-%dT%H:%M:%S%z"
            date_format_frac_tz = "%Y-%m-%dT%H:%M:%S.%f%z"
            supported_date_formats = [
                date_format_no_tz,
                date_format_tz,
                date_format_frac_tz,
            ]

            if "creation_date" in data_description:
                session_start_date_string = f"{data_description['creation_date']}T{data_description['creation_time'].split('.')[0]}"
            else:
                session_start_date_string = data_description["creation_time"]
            session_id = data_description["name"]
            if isinstance(data_description["institution"], str):
                institution = data_description["institution"]
            elif isinstance(data_description["institution"], dict):
                institution = data_description["institution"].get("name", None)

            # Use strptime to parse the string into a datetime object
            session_start_date_time = None
            for date_format in supported_date_formats:
                try:
                    session_start_date_time = datetime.strptime(
                        session_start_date_string, date_format
                    )
                    break
                except:
                    pass
            if session_start_date_time is None:
                warnings.warn(
                    f"Could not parse date string: {session_start_date_string}. Using current time."
                )
                timezone_info = (
                    datetime.now(dt.timezone.utc).astimezone().tzinfo
                )
                session_start_date_time = datetime.now().replace(
                    tzinfo=timezone_info
                )
        else:
            # create session_start_time
            logging.info(f"Missing data description file: {data_description_file}")
            logging.info(f"\tCreating mock info.")
            timezone_info = datetime.now(dt.timezone.utc).astimezone().tzinfo
            session_start_date_time = datetime.now().replace(
                tzinfo=timezone_info
            )
            institution = None
            session_id = data_asset.name
            asset_name = session_id

        if subject_metadata is not None:
            dob = subject_metadata["date_of_birth"]
            subject_dob = datetime.strptime(dob, "%Y-%m-%d").replace(
                tzinfo=pytz.timezone("US/Pacific")
            )
            if session_start_date_time.tzinfo is None:
                pacific = pytz.timezone('US/Pacific')
                session_start_date_time = pacific.localize(session_start_date_time)
            subject_age = session_start_date_time - subject_dob

            age = "P" + str(subject_age.days) + "D"
            if isinstance(subject_metadata["species"], dict):
                species = subject_metadata["species"]["name"]
            else:
                species = subject_metadata["species"]
            subject = Subject(
                subject_id=subject_metadata["subject_id"],
                species=species,
                sex=subject_metadata["sex"][0].upper(),
                date_of_birth=subject_dob,
                age=age,
                genotype=subject_metadata["genotype"],
                description=None,
                strain=subject_metadata.get("background_strain")
                or subject_metadata.get("breeding_group"),
            )
        else:
            # create mock subject
            logging.info(f"Missing subject metadata file: {subject_metadata_file}")
            logging.info("\tCreating mock subject.")
            from pynwb.testing.mock.file import mock_Subject

            subject = mock_Subject()

        # Store and write NWB file
        nwbfile = NWBFile(
            session_description="NWB file generated by AIND pipeline",
            identifier=str(uuid4()),
            session_start_time=session_start_date_time,
            institution=institution,
            subject=subject,
            session_id=session_id,
        )

    # Naming Convention should be decided by AIND Schema.
    # It seems like the subject/processing/etc. Json
    # Files should also be added to the results folder?
    nwb_output_file = results_folder / f"{asset_name}.nwb"
    with io_class(str(nwb_output_file), mode="w") as io:
        io.write(nwbfile)

    logging.info(f"Saved {nwb_output_file}")


if __name__ == "__main__":
    run()
