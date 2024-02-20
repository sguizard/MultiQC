"""
MultiQC submodule to parse output from Iso-Seq refine logs
"""

import csv
import json
import logging
import math
from collections import defaultdict

from multiqc.plots import table
from multiqc.utils import config

logger = logging.getLogger(__name__)


class RefineMixin:
    def parse_refine_log(self):
        json_data = dict()
        csv_data = dict()

        for f in self.find_log_files("isoseq/refine-json", filehandles=True):
            json_data[f["s_name"]] = json.load(f["f"])
            self.add_data_source(f)

        for f in self.find_log_files("isoseq/refine-csv", filehandles=True):
            counts = defaultdict(int)
            sums = defaultdict(int)
            squared_sums = defaultdict(int)
            mins = defaultdict(lambda: float("inf"))
            maxs = defaultdict(lambda: float("-inf"))
            strand_counts = defaultdict(int)
            primer_counts = defaultdict(int)

            # Read the CSV file
            reader: csv.DictReader = csv.DictReader(f["f"])
            for row in reader:
                # Process columns of interest
                for column in ["fivelen", "threelen", "polyAlen", "insertlen"]:
                    value = float(row[column])
                    counts[column] += 1
                    sums[column] += value
                    squared_sums[column] += value**2
                    mins[column] = min(mins[column], value)
                    maxs[column] = max(maxs[column], value)

                # Count occurrences of 'strand' and 'primer' values
                strand_counts[row["strand"]] += 1
                primer_counts[row["primer"]] += 1

            d = dict()
            if counts:
                # Compute mean, standard deviation, min, and max and store them in data
                for column in ["fivelen", "threelen", "polyAlen", "insertlen"]:
                    mean = sums[column] / counts[column]
                    variance = (squared_sums[column] / counts[column]) - mean**2
                    std_dev = math.sqrt(variance) if variance > 0 else 0.0

                    d[f"min_{column}"] = mins[column]
                    d[f"mean_{column}"] = mean
                    d[f"std_{column}"] = std_dev
                    d[f"max_{column}"] = maxs[column]
                d["strand_counts"] = dict(strand_counts)
                d["primer_counts"] = dict(primer_counts)
                csv_data[f["s_name"]] = d
                self.add_data_source(f)

        if config.use_filename_as_sample_name:
            logger.error(
                "Iso-Seq refine won't work properly with --fn_as_s_name / config.use_filename_as_sample_name, "
                "as it uses the file name cleaning patterns to get the sample names "
                "from the file names, and it needs to match JSON and CSV files"
            )
        elif json_data.keys() != csv_data.keys():
            logger.error(
                f"Iso-Seq refine: different sets of JSON and CSV files found: "
                f"{json_data.keys()} vs {csv_data.keys()} Make sure that there is "
                f"a JSON and a CSV file for each sample"
            )
        data = dict()
        for s_name in json_data.keys() | csv_data.keys():
            data[s_name] = json_data.get(s_name, {})
            data[s_name].update(csv_data.get(s_name, {}))

        self.write_data_file(data, "multiqc_isoseq_refine_report")
        return data

    def add_general_stats_refine(self, data_by_sample):
        headers = dict()
        headers["num_reads_fl"] = {
            "title": "Full-length",
            "description": "Number of CCS where both primers have been detected",
            "scale": "GnBu",
            "format": "{:,.d}",
        }
        headers["num_reads_flnc"] = {
            "title": "Non-chimeric full-length",
            "description": "Number of non-chimeric CCS where both primers have been detected",
            "scale": "RdYlGn",
            "format": "{:,.d}",
        }
        headers["num_reads_flnc_polya"] = {
            "title": "Poly(A) free non-chimeric full-length",
            "description": "Number of non-chimeric CCS where both primers have been detected and the poly(A) tail has been removed",
            "scale": "GnBu",
            "format": "{:,.d}",
        }
        self.general_stats_addcols(data_by_sample, headers, namespace="refine")

    def add_table_refine(self, data_by_sample):
        headers = dict()
        headers["min_fivelen"] = {
            "title": "Min 5' primer length",
            "description": "The minimum 5' primer length in base pair",
            "scale": "GnBu",
        }
        headers["mean_fivelen"] = {
            "title": "Mean 5' primer length",
            "description": "The mean 5' primer length in base pair",
            "scale": "RdYlGn",
        }
        headers["std_fivelen"] = {
            "title": "Std of 5' primer length",
            "description": "The standard deviation of 5' primer length in base pair",
            "scale": "GnBu",
        }
        headers["max_fivelen"] = {
            "title": "Max 5' primer length",
            "description": "The maximum 5' primer length in base pair",
            "scale": "GnBu",
        }
        headers["min_threelen"] = {
            "title": "Min 3' primer length",
            "description": "The minimum 3' primer length in base pair",
            "scale": "GnBu",
        }
        headers["mean_threelen"] = {
            "title": "Mean 3' primer length",
            "description": "The mean 3' primer length in base pair",
            "scale": "RdYlGn",
        }
        headers["std_threelen"] = {
            "title": "Std of 3' primer length",
            "description": "The standard deviation of 3' primer length in base pair",
            "scale": "GnBu",
        }
        headers["max_threelen"] = {
            "title": "Max 3' primer length",
            "description": "The maximum 3' primer length in base pair",
            "scale": "RdYlGn",
        }
        headers["min_polyAlen"] = {
            "title": "Min polyA tail length",
            "description": "The minimum polyA tail length in base pair",
            "scale": "GnBu",
        }
        headers["mean_polyAlen"] = {
            "title": "Mean polyA tail length",
            "description": "The mean polyA tail length in base pair",
            "scale": "RdYlGn",
        }
        headers["std_polyAlen"] = {
            "title": "Std of polyA tail length",
            "description": "The standard deviation of polyA tail length in base pair",
            "scale": "GnBu",
        }
        headers["max_polyAlen"] = {
            "title": "Max polyA tail length",
            "description": "The maximum polyA tail length in base pair",
            "scale": "RdYlGn",
        }
        headers["min_insertlen"] = {
            "title": "Min insert length",
            "description": "The minimum insert length in base pair",
            "scale": "GnBu",
        }
        headers["mean_insertlen"] = {
            "title": "Mean insert length",
            "description": "The mean insert length in base pair",
            "scale": "RdYlGn",
        }
        headers["std_insertlen"] = {
            "title": "Std of insert length",
            "description": "The standard deviation of insert length in base pair",
            "scale": "GnBu",
        }
        headers["max_insertlen"] = {
            "title": "Max insert length",
            "description": "The maximum insert length in base pair",
            "scale": "RdYlGn",
        }

        config = {
            "id": "isoseq_refine_table",
            "title": "Iso-Seq refine",
        }

        self.add_section(
            name="Iso-Seq refine",
            anchor="insert-refine-stats",
            description="Iso-Seq refine statistics",
            helptext="""
            The .report.csv file contains information about 5' prime and 3' primers length, insert length,
            poly(A) length, and couple of primers detected for each CCS.
            The table presents min, max, mean, standard deviation for each parameter.
            """,
            plot=table.plot(data_by_sample, headers, config),
        )
