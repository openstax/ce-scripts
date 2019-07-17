import csv
import os
from datetime import datetime

import requests


def to_csv(fieldnames, collection, filename, datestamp=True):
    if datestamp:
        filename = f"{filename}-{datetime.now().strftime('%Y%m%d')}.csv"
    else:
        filename = f"{filename}.csv"

    print(f"Saving csv file to {filename}")

    with open(filename, 'w') as outfile:
        w = csv.DictWriter(outfile, fieldnames, dialect='excel')

        if not os.path.exists(filename):
            w.writeheader()

        for row in collection:
            w.writerow(row)


def make_destination_folder(folder):
    if not os.path.isdir(folder):
        os.makedirs(folder)


def get_json_reponse(url, **kwargs):
    params = kwargs

    r = requests.get(url, params=params)
    r.raise_for_status()
    return r.json()
