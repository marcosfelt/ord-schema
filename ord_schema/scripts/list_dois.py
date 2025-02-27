# Copyright 2020 Open Reaction Database Project Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Lists DOIs and the Datasets that cover them.

Example usage:
$ ORD_DATA_ROOT="${HOME}/Documents/GitHub/ord-data"
$ python list_dois.py --input="${ORD_DATA_ROOT}/data/*/*.pb"
"""

import collections
import glob
import os
import re
import urllib.parse

from absl import app
from absl import flags
from absl import logging
import requests

from ord_schema import message_helpers
from ord_schema.proto import dataset_pb2

FLAGS = flags.FLAGS
flags.DEFINE_string("input", None, "Input pattern for Dataset protos.")

_PREFIX = "https://github.com/Open-Reaction-Database/ord-data/blob/main/"


def main(argv):
    del argv  # Only used by app.run().
    filenames = glob.glob(FLAGS.input, recursive=True)
    logging.info("Found %d datasets", len(filenames))
    dois = collections.defaultdict(list)
    output_filenames = {}
    for filename in filenames:
        logging.info("Checking %s", filename)
        dataset = message_helpers.load_message(filename, dataset_pb2.Dataset)
        dataset_id = os.path.basename(filename).split(".")[0]
        if dataset.dataset_id != dataset_id:
            raise AssertionError("Dataset IDs do not match: " f"{dataset.dataset_id} != {dataset_id}")
        output_filenames[dataset_id] = message_helpers.id_filename(filename)
        doi_set = set()
        for reaction in dataset.reactions:
            # Some poorly-validated DOI entries start with 'doi:'...
            match = re.fullmatch(r"(?:(?:doi)|(?:DOI))?:?\s*(.+)", reaction.provenance.doi)
            if not match:
                continue  # No DOI.
            doi = urllib.parse.urlsplit(match.group(1)).path
            if doi.startswith("/"):
                doi = doi[1:]
            doi_set.add(doi)
        for doi in doi_set:
            dois[doi].append(dataset_id)
    for doi in sorted(dois):
        url = f"https://doi.org/{doi}"
        reference = requests.get(url, headers={"Accept": "text/x-bibliography; style=nature"})
        citation = f"{reference.content.decode().strip()[2:]} " f"[doi: {doi}]({url})"
        print(f"* {citation}")
        for dataset in sorted(dois[doi]):
            url = urllib.parse.urljoin(_PREFIX, output_filenames[dataset])
            print(f"  * [{dataset}]({url})")


if __name__ == "__main__":
    flags.mark_flag_as_required("input")
    app.run(main)
