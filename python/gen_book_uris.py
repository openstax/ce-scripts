#!/usr/bin/env python
"""CNX Book URI Generator: Generate URLS for cnx.org book for testing
Usage:
  gen_book_urls.py <archive_host> <cnx_id>
  gen_book_urls.py (-h | --help)

Examples:
  Run as an executable:
  ./gen_book_urls.py archive-staging.cnx.org e42bd376-624b-4c0f-972f-e0c57998e765

  Run using the python command:
  python gen_book_urls archive.cnx.org 7fccc9cf-9b71-44f6-800b-f9457fd64335
"""
import os

from docopt import docopt
from rex_redirects import generate_cnx_uris

HERE = os.path.abspath(os.path.dirname(__file__))

OUTPUT_DIR = os.path.join(HERE, "output")


def cli():
    arguments = docopt(__doc__)

    # Assign arguments to variables
    archive_host = arguments["<archive_host>"]
    cnx_id = arguments["<cnx_id>"]

    with open(os.path.join(OUTPUT_DIR, f"{cnx_id}.txt"), "w") as outfile:
        for uri in generate_cnx_uris(archive_host, cnx_id):
            outfile.write(f"{uri}\n")

    print("uris generated successfully")


if __name__ == "__main__":
    cli()
