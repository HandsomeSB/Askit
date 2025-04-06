import os
import json

class LocalJsonStore:
    def __init__(self, store_directory=".store"):
        self.store_directory = store_directory
        os.makedirs(self.store_directory, exist_ok=True)

    def _get_file_path(self, filename):
        return os.path.join(self.store_directory, f"{filename}.json")

    def save(self, filename, data):
        """Save data to a JSON file."""
        file_path = self._get_file_path(filename)
        with open(file_path, 'w') as json_file:
            json.dump(data, json_file)

    def load(self, filename):
        """Load data from a JSON file. If the file doesn't exist, create a new empty JSON file."""
        file_path = self._get_file_path(filename)
        if not os.path.exists(file_path):
            with open(file_path, 'w') as json_file:
                json.dump({}, json_file)  # Create a new empty JSON file

        with open(file_path, 'r') as json_file:
            return json.load(json_file)


    def delete(self, filename):
        """Delete a JSON file."""
        file_path = self._get_file_path(filename)
        if os.path.exists(file_path):
            os.remove(file_path)

    def deep_merge(self, original, update):
        """
        Recursively update a dict.
        Subdict's won't be overwritten but also updated.
        Update in place on original.
        """
        for key, value in update.items():
            if key in original and isinstance(original[key], dict) and isinstance(value, dict):
                self.deep_merge(original[key], value)
            else:
                original[key] = value
        return original
