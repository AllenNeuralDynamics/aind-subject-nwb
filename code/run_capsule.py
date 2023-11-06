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
        subject_match = re.search(r'_(\d+)_', file)
        if subject_match:
            subject_id = subject_match.group(1)
        date_match = re.search(r'(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})', file)
        if date_match:
            time = date_match.group(1)

    results = doc_db_client.retrieve_data_asset_records(
        filter_query={
            "$and": [
                {"_name": {"$regex": f"{phys_type}.*{time}"}},
                {"subject.subject_id": f'{subject_id}'}
            ]
        },
        paginate_batch_size=100,
    )
    if not results:
        print("No data records found.")
        raise Exception("No data records found.")
    
    processing = (results[0].processing)
    metadata = (results[0].subject)
    dob = metadata['date_of_birth']

    subject_dob_utc_datetime = datetime.strptime(dob, "%Y-%m-%d").replace(tzinfo=pytz.UTC)
    session_start_date_string = processing['data_processes'][0]['start_date_time']
    date_format = "%Y-%m-%dT%H:%M:%S.%f%z"

    # Use strptime to parse the string into a datetime object
    session_start_date_time = datetime.strptime(session_start_date_string, date_format)
    subject_age = session_start_date_time - subject_dob_utc_datetime

    age = "P" + str(subject_age) + "D"
    subject = pynwb.file.Subject(
        subject_id=metadata["subject_id"],
        species="Mus musculus",
        sex=metadata["sex"][0].upper(),
        date_of_birth=subject_dob_utc_datetime,
        age=age,
        genotype=metadata["genotype"],
        description=None,
        strain=metadata["background_strain"] or metadata["breeding_group"],
    )

    # Store and write NWB file
    nwbfile = NWBFile(
        session_description="Test File",  # required
        identifier=str(uuid4()),  # required
        session_start_time=session_start_date_time,  # required
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
