import csv


class DetectionModel:

    def detect_delimiter(self, row: str) -> str:
        detected_delimiter = ""
        try:
            dialect = csv.Sniffer().sniff(row)
            detected_delimiter = dialect.delimiter
        except Exception as e:
            # TODO: use logging
            print(e)

        return detected_delimiter
