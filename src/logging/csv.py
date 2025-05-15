import os

print("NEW CODE !!!!!!!")

class Csv:
    """
    A class to handle CSV file operations.
    """

    def __init__(self, path: str, *headers):
        """
        Initialize the Csv object with a filename.

        :param filename: The name of the CSV file.
        """
        self.path = path
        # self.headers = headers

        name = self.path.split('/')[-1]
        parent_path = self.path[:-(len(name)+1)]
        # print(f"parent_path: {parent_path}")
        filenames = os.listdir(parent_path)

        if not name in filenames:
            with open(self.path, 'w') as file:
                file.write(','.join(headers) + '\n')
        # else: raise Exception(f"Csv file {self.path} already exists.")
        return

    def append(self, *data, prepend_comma=False, end_line=True):
        """
        Append data to the CSV file.
        :param data: List of data to append to the CSV file.
        :param prepend_comma: Whether to prepend a comma before the data.
        :param end_line: Whether to end the line after the data.
        """
        
        print(self.path)

        with open(self.path, 'a') as file:
            start = ',' if prepend_comma else ''
            ending = '\n' if end_line else ''
            data_str = ','.join([str(d) for d in data]) if data else ''
            file.write(start + data_str + ending)
        return

    def read(self):
        """
        Read the CSV file and return its contents.
        :return: List of rows in the CSV file.
        """
        with open(self.path, 'r') as file:
            lines = file.readlines()
        return [line.strip().split(',') for line in lines]