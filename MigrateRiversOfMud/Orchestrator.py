import os
import multiprocessing
import time

from MigrateRiversOfMud.entity.Area import Area
from MigrateRiversOfMud.entity.Helps import Helps
from MigrateRiversOfMud.entity.Socials import Socials
from MigrateRiversOfMud.http.SOMClient import delete, api_endpoints


class Orchestrator:
    def __init__(
        self,
        directory,
        dry_run=False,
        delete_first=False,
        socials_file=None,
        helps_file=None,
        migrate_type="all"
    ):
        self.directory = directory
        self.socials_file = socials_file
        self.helps_file = helps_file
        self.migrate_type = self._normalize_migrate_type(migrate_type)
        self.dry_run = dry_run
        self.delete_first = delete_first
        self.area_files = self._get_area_files()
        self.area_count = len(self.area_files)
        if self.socials_file is None:
            default_socials = os.path.join(self.directory, "social.are")
            if os.path.exists(default_socials):
                self.socials_file = default_socials
        if self.helps_file is None:
            default_helps = os.path.join(self.directory, "help.are")
            if os.path.exists(default_helps):
                self.helps_file = default_helps
        if self.dry_run:
            print(f"DRY RUN MODE: Migration type '{self.migrate_type}'.")
        else:
            print(f"Running migration type '{self.migrate_type}'.")

        if self.migrate_type in ("all", "areas"):
            if self.dry_run:
                print(f"DRY RUN MODE: Would process {self.area_count} area files.")
            else:
                print(f"Distributing {self.area_count} area files among {multiprocessing.cpu_count()} processors.")

    @staticmethod
    def _normalize_migrate_type(migrate_type):
        mapping = {
            "all": "all",
            "area": "areas",
            "areas": "areas",
            "social": "socials",
            "socials": "socials",
            "help": "helps",
            "helps": "helps",
        }
        normalized = mapping.get((migrate_type or "all").strip().lower())
        if normalized is None:
            valid = ", ".join(sorted(mapping.keys()))
            raise ValueError(f"Invalid migrate_type '{migrate_type}'. Valid values: {valid}")
        return normalized

    def _get_area_files(self):
        """
        Retrieves a list of area files in the given directory.
        """
        area_files = []
        for file in os.listdir(self.directory):
            if not file.endswith('.are'):
                continue
            if file.lower() in ("social.are", "help.are", "group.are", "rom.are"):
                continue
            area_files.append(os.path.join(self.directory, file))
        return area_files

    def process_area_file(self, area_file):
        """
        Processes a single area file by instantiating the Area class.
        In dry-run mode, only logs the payload without posting to API.
        """
        Area(area_file, insert=not self.dry_run)

    def process_socials_file(self):
        """
        Processes social.are by instantiating the Socials class.
        """
        if self.socials_file and os.path.exists(self.socials_file):
            Socials(self.socials_file, insert=not self.dry_run)

    def process_helps_file(self):
        """
        Processes help.are by instantiating the Helps class.
        """
        if self.helps_file and os.path.exists(self.helps_file):
            Helps(self.helps_file, insert=not self.dry_run)

    def _delete_all_collections(self):
        """
        Deletes all data from each collection by sending DELETE requests to each endpoint.
        """
        collections = []
        if self.migrate_type in ("all", "areas"):
            collections.extend(['areas', 'rooms', 'mobiles', 'items', 'shops', 'resets', 'specials'])
        if self.migrate_type in ("all", "socials"):
            collections.append('socials')
        if self.migrate_type in ("all", "helps"):
            collections.append('helps')

        if not collections:
            return

        print("Deleting all existing data from collections...")
        for collection in collections:
            endpoint_key = collection.rstrip('s')  # Convert plural to singular for endpoint lookup
            if endpoint_key in api_endpoints:
                url = api_endpoints[endpoint_key] + collection
                print(f"  Deleting {collection}...")
                response = delete(url)
                if response:
                    print(f"  ✓ Successfully deleted {collection}")
                else:
                    print(f"  ✗ Failed to delete {collection}")
        print("Deletion complete.\n")

    def run(self):
        """
        Use a process pool to process area files in parallel.
        In dry-run mode, processes files sequentially to allow proper logging.
        """
        start_time = time.time()

        if self.delete_first and not self.dry_run:
            self._delete_all_collections()

        if self.migrate_type in ("all", "areas"):
            if self.dry_run:
                print("DRY RUN: Processing area files sequentially for logging...")
                for area_file in self.area_files:
                    print(f"Processing {area_file}...")
                    if area_file.endswith("rom.are") or area_file.endswith("group.are") or area_file.endswith("help.are"):
                        continue
                    self.process_area_file(area_file)
            else:
                with multiprocessing.Pool(multiprocessing.cpu_count()) as pool:
                    pool.map(self.process_area_file, self.area_files)

        if self.migrate_type in ("all", "socials") and self.socials_file:
            self.process_socials_file()
        if self.migrate_type in ("all", "helps") and self.helps_file:
            self.process_helps_file()

        end_time = time.time()
        mode = "DRY RUN" if self.dry_run else "Orchestrator run"
        print(f"{mode} completed in {end_time - start_time:.2f} seconds.")
