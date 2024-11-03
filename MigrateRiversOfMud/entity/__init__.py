import os
import multiprocessing

from MigrateRiversOfMud.entity.Area import Area


class Orchestrator:
    def __init__(self, directory):
        self.directory = directory
        self.area_files = self._get_area_files()
        self.cpu_count = multiprocessing.cpu_count()
        self.area_count = len(self.area_files)
        print(f"Distributing {self.area_count} files among {self.cpu_count} processors.")

    def _get_area_files(self):
        """
        Retrieves a list of area files in the given directory.
        """
        return [os.path.join(self.directory, file) for file in os.listdir(self.directory) if file.endswith('.are')]

    @staticmethod
    def process_area_file(area_file):
        """
        Processes a single area file by instantiating the Area class.
        """
        Area(area_file)

    def run(self):
        """
        Use a process pool to process area files in parallel.
        """
        with multiprocessing.Pool(self.cpu_count) as pool:
            pool.map(self.process_area_file, self.area_files)



