import csv


class DetectionModel:

    def detect_delimiter(self, row: str) -> str:
        """Detect the delimiter of a CSV row.

        Parameters
        ----------
        row : str
            A row of a CSV file

        Returns
        -------
        str
            The detected delimiter. If no delimiter is detected, an empty string is returned.
        """
        detected_delimiter = ""
        try:
            dialect = csv.Sniffer().sniff(row)
            detected_delimiter = dialect.delimiter
        except Exception as e:
            # TODO: use logging
            print(e)

        return detected_delimiter
