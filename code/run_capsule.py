""" top level run script """
import json
import pynwb
import os
import re
from datetime import datetime
import pytz
from pynwb import NWBHDF5IO, NWBFile
from uuid import uuid4
from aind_data_access_api.document_db import MetadataDbClient


def run():
    """ basic run function """
    DOC_DB_HOST = "api.allenneuraldynamics.org"
    DOC_DB_DATABASE = "metadata"
    DOC_DB_COLLECTION = "data_assets"
    doc_db_client = MetadataDbClient(
        host=DOC_DB_HOST,
        database=DOC_DB_DATABASE,
        collection=DOC_DB_COLLECTION,)

    for file in os.listdir('/data'):
        if 'ecephys' in file:
            phys_type = 'ecephys'
        elif 'multiplane-ophys' in file:
            phys_type = 'multiplane-ophys'
        subject_match = re.search(r'_(\d{6})', file)
        if subject_match:
            subject_id = subject_match.group(1)
        date_match = re.search(r'_(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})', file)
        if date_match:
            time = date_match.group(1)

    # phys_type = 'ecephys'
    # time = '2023-08-31_12-33-31'
    # subject_id = '668755'

    # phys_type = "multiplane-ophys"
    # time = '2023-07-18_10-56-26'
    # subject_id = '681417'

    results = doc_db_client.retrieve_data_asset_records(
        filter_query={
            "$and": [
                {"_name": {"$regex": f"{phys_type}.*{time}"}},
                {"subject.subject_id": f'{subject_id}'}
            ]
        },
        paginate_batch_size=100,
    )
    processing = (results[0].processing)
    metadata = (results[0].subject)
    dob = metadata['date_of_birth']

    utc_datetime = datetime.strptime(dob, "%Y-%m-%d").replace(tzinfo=pytz.UTC)
    date_string = processing['data_processes'][0]['start_date_time']
    date_format = "%Y-%m-%dT%H:%M:%S.%f%z"

    # Use strptime to parse the string into a datetime object
    date_object = datetime.strptime(date_string, date_format)
    time_difference = date_object - utc_datetime

    # Get the number of days
    days_difference = time_difference.days
    age = "P" + str(days_difference) + "D"
    subject = pynwb.file.Subject(
        subject_id=metadata["subject_id"],
        species="Mus musculus",
        sex=metadata["sex"][0].upper(),
        date_of_birth=utc_datetime,
        age=age,
        genotype=metadata["genotype"],
        description=None,
        strain=metadata["background_strain"] or metadata["breeding_group"],
    )

    # Store and write NWB file
    nwbfile = NWBFile(
        session_description="Test File",  # required
        identifier=str(uuid4()),  # required
        session_start_time=date_object,  # required
        lab="Allen Institute",  # optional
        institution="Allen Institute",  # optional
        subject=subject,
        session_id=subject_id + '_' + time
    )

    # Naming Convention should be decided by AIND Schema.
    # It seems like the subject/processing/etc. Json
    # Files should also be added to the results folder?
    io = NWBHDF5IO(r"/results/test.nwb", mode="w")
    io.write(nwbfile)
    io.close()
    pass


if __name__ == "__main__":
    run()
