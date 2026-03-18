import os
import multiprocessing
import time

from MigrateRiversOfMud.entity.Area import Area
from MigrateRiversOfMud.http import delete, api_endpoints


class Orchestrator:
    def __init__(self, directory, dry_run=False, delete_first=False):
        self.directory = directory
        self.dry_run = dry_run
        self.delete_first = delete_first
        self.area_files = self._get_area_files()
        self.area_count = len(self.area_files)
        if self.dry_run:
            print(f"DRY RUN MODE: Would process {self.area_count} files.")
        else:
            print(f"Distributing {self.area_count} files among {multiprocessing.cpu_count()} processors.")

    def _get_area_files(self):
        """
        Retrieves a list of area files in the given directory.
        """
        return [os.path.join(self.directory, file) for file in os.listdir(self.directory) if file.endswith('.are')]

    def process_area_file(self, area_file):
        """
        Processes a single area file by instantiating the Area class.
        In dry-run mode, only logs the payload without posting to API.
        """
        Area(area_file, insert=not self.dry_run)

    def _delete_all_collections(self):
        """
        Deletes all data from each collection by sending DELETE requests to each endpoint.
        """
        collections = ['areas', 'rooms', 'mobiles', 'items', 'shops', 'resets', 'specials']
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

        if self.dry_run:
            print("DRY RUN: Processing files sequentially for logging...")
            for area_file in self.area_files:
                self.process_area_file(area_file)
        else:
            with multiprocessing.Pool(multiprocessing.cpu_count()) as pool:
                pool.map(self.process_area_file, self.area_files)
        end_time = time.time()
        mode = "DRY RUN" if self.dry_run else "Orchestrator run"
        print(f"{mode} completed in {end_time - start_time:.2f} seconds.")