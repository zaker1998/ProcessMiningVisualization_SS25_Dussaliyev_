from streamlit.runtime.uploaded_file_manager import UploadedFile
import pandas as pd
import pickle
import base64
import pm4py
from pm4py.objects.log.obj import EventLog
import tempfile
import os
import xml.etree.ElementTree as ET
from src.exceptions.io_exceptions import UnsupportedFileTypeException, InvalidTypeException
import logging


class ImportOperations:

    def read_csv(
        self, filePath: str | UploadedFile, delimiter: str = ","
    ) -> pd.DataFrame:
        """Reads a csv file and returns a pandas DataFrame

        Parameters
        ----------
        filePath : str | UploadedFile
            Path to the csv file or the uploaded file object
        delimiter : str, optional
            The delimiter used in the csv file, by default ","

        Returns
        -------
        pd.DataFrame
            The csv file as a pandas DataFrame
        """
        df = pd.read_csv(filePath, delimiter=delimiter)
        return df

    def read_img(self, file_path: str) -> str:
        """Reads an image file and returns it as a base64 string. This is used to display the image in the HTML

        Parameters
        ----------
        file_path : str
            Path to the image file

        Returns
        -------
        str
            The image file as a base64 string
        """
        with open(file_path, "rb") as file:
            png = file.read()
        # https://pmbaumgartner.github.io/streamlitopedia/sizing-and-images.html
        # https://discuss.streamlit.io/t/how-to-show-local-gif-image/3408/2
        # Convert the image to a base64 string to be able to display it in the HTML
        png_base64 = base64.b64encode(png).decode("utf-8")
        return png_base64

    def read_model(self, path: str | UploadedFile) -> object:
        """Reads a model from a pickle file and returns the model object

        Parameters
        ----------
        path : str | UploadedFile
            Path to the pickle file or the uploaded file object

        Returns
        -------
        object
            The model object
        """
        if isinstance(path, UploadedFile):
            model = pickle.load(path)
        else:
            with open(path, "rb") as file:
                model = pickle.load(file)
        return model

    def read_file(self, file_path: str | UploadedFile) -> str:
        """Reads a file and returns the content as a string. This is used to display the content of the file in the UI

        Parameters
        ----------
        file_path : str | UploadedFile
            Path to the file or the uploaded file object

        Returns
        -------
        str
            The content of the file as a string
        """
        if isinstance(file_path, UploadedFile):
            return file_path.read().decode("utf-8")

        with open(file_path, "r") as file:
            return file.read()

    def read_file_binary(self, file_path: str) -> bytes:
        """Reads a file and returns the content as bytes. This is used to download the file

        Parameters
        ----------
        file_path : str
            Path to the file

        Returns
        -------
        bytes
            The content of the file as bytes
        """
        with open(file_path, "rb") as file:
            return file.read()

    def read_line(self, file_path: str | UploadedFile) -> str:
        """Reads the first line of a file and returns it as a string. This is used to detect the delimiter of a csv file

        Parameters
        ----------
        file_path : str | UploadedFile
            Path to the file or the uploaded file object

        Returns
        -------
        str
            The first line of the file as a string
        """
        if isinstance(file_path, UploadedFile):
            line = file_path.readline().decode("utf-8")
            # reset the file pointer to the beginning of the file
            file_path.seek(0)
            return line

        with open(file_path, "r") as file:
            return file.readline()

    def read_xes(self, file_path: str | UploadedFile) -> EventLog:
        """Reads an XES file and returns a PM4Py EventLog object

        Parameters
        ----------
        file_path : str | UploadedFile
            Path to the XES file or the uploaded file object

        Returns
        -------
        EventLog
            The XES file as a PM4Py EventLog object
            
        Raises
        ------
        UnsupportedFileTypeException
            If the file is not a valid XES file
        """
        try:
            if isinstance(file_path, UploadedFile):
                # Create a temporary file to store the uploaded content
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xes') as temp_file:
                    temp_file.write(file_path.getvalue())
                    temp_path = temp_file.name
                
                # Read the XES file using PM4Py's xes importer directly
                from pm4py.objects.log.importer.xes import importer as xes_importer
                event_log = xes_importer.apply(temp_path)
                
                # Clean up the temporary file
                os.unlink(temp_path)
                return event_log
            else:
                # Read directly from the file path using xes importer
                from pm4py.objects.log.importer.xes import importer as xes_importer
                return xes_importer.apply(file_path)
        except Exception as e:
            logging.error(f"Error reading XES file: {str(e)}")
            raise UnsupportedFileTypeException(f"XES file format error: {str(e)}")

    def xes_to_dataframe(self, event_log: EventLog) -> pd.DataFrame:
        """Converts a PM4Py EventLog object to a pandas DataFrame

        Parameters
        ----------
        event_log : EventLog
            The PM4Py EventLog object

        Returns
        -------
        pd.DataFrame
            The event log as a pandas DataFrame
        """
        if not isinstance(event_log, EventLog):
            raise InvalidTypeException("PM4Py EventLog", type(event_log))
        return pm4py.convert_to_dataframe(event_log)
    
    def validate_xes(self, file_path: str | UploadedFile) -> bool:
        """Validates if a file is a valid XES file

        Parameters
        ----------
        file_path : str | UploadedFile
            Path to the XES file or the uploaded file object

        Returns
        -------
        bool
            True if the file is a valid XES file, False otherwise
        """
        try:
            event_log = self.read_xes(file_path)
            return isinstance(event_log, EventLog) and len(event_log) > 0
        except Exception:
            return False
    
    def _validate_xes_structure(self, file_path: str) -> bool:
        """Validates the structure of an XES file

        Parameters
        ----------
        file_path : str
            Path to the XES file

        Returns
        -------
        bool
            True if the file has a valid XES structure, False otherwise
        """
        try:
            # Parse the XML
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Check if root tag is 'log'
            if root.tag != 'log':
                return False
                
            # Check if there are traces and events
            ns = {'xes': 'http://www.xes-standard.org/'}
            traces = root.findall('.//trace', ns)
            if not traces:
                # Also try without namespace
                traces = root.findall('.//trace')
                if not traces:
                    return False
            
            # At least one trace should have events
            has_events = False
            for trace in traces[:10]:  # Check first 10 traces
                events = trace.findall('.//event', ns) or trace.findall('.//event')
                if events:
                    has_events = True
                    break
                
            return has_events
        except Exception:
            return False
    
    def get_xes_attributes(self, file_path: str | UploadedFile) -> dict:
        """Gets the attributes of an XES file

        Parameters
        ----------
        file_path : str | UploadedFile
            Path to the XES file or the uploaded file object

        Returns
        -------
        dict
            Dictionary containing log attributes, trace attributes, and event attributes
        """
        event_log = self.read_xes(file_path)
        
        # Initialize attribute containers
        log_attributes = {}
        trace_attributes = set()
        event_attributes = set()
        
        # Extract log attributes
        for attr_key, attr_value in event_log.attributes.items():
            log_attributes[attr_key] = attr_value
        
        # Extract trace and event attributes
        for trace in event_log:
            for attr_key in trace.attributes.keys():
                trace_attributes.add(attr_key)
            
            for event in trace:
                for attr_key in event.keys():
                    event_attributes.add(attr_key)
        
        return {
            'log_attributes': log_attributes,
            'trace_attributes': list(trace_attributes),
            'event_attributes': list(event_attributes)
        }