from streamlit.runtime.uploaded_file_manager import UploadedFile
import pandas as pd
import pickle
import base64
import pm4py
import tempfile
import os
import xml.etree.ElementTree as ET
from exceptions.io_exceptions import UnsupportedFileTypeException, InvalidTypeException
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

    def read_xes(self, file_path: str | UploadedFile) -> pd.DataFrame:
        """Reads an XES file and returns a pandas DataFrame

        Parameters
        ----------
        file_path : str | UploadedFile
            Path to the XES file or the uploaded file object

        Returns
        -------
        pd.DataFrame
            The XES file as a pandas DataFrame
            
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
                
                # Read the XES file and convert to DataFrame
                event_log = pm4py.read_xes(temp_path)  # type: ignore[arg-type]
                df = pm4py.convert_to_dataframe(event_log)  # type: ignore[arg-type]
                
                # Clean up the temporary file
                os.unlink(temp_path)
                return df
            else:
                # Read directly from the file path and convert to DataFrame
                event_log = pm4py.read_xes(file_path)  # type: ignore[arg-type]
                return pm4py.convert_to_dataframe(event_log)  # type: ignore[arg-type]
        except Exception as e:
            logging.error(f"Error reading XES file: {str(e)}")
            raise UnsupportedFileTypeException(f"XES file format error: {str(e)}")

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
            df = self.read_xes(file_path)
            return isinstance(df, pd.DataFrame) and len(df) > 0
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
        df = self.read_xes(file_path)
        
        # Initialize attribute containers
        log_attributes = {}
        trace_attributes = set()
        event_attributes = set()
        
        # Extract event attributes from DataFrame columns
        # XES attributes are stored as columns in the DataFrame
        if not df.empty:
            event_attributes = set(df.columns.tolist())
            
            # Common trace-level attributes (attributes that are constant per case)
            # These are typically prefixed with 'case:' in XES standard
            for col in df.columns:
                if col.startswith('case:'):
                    trace_attributes.add(col)
        
        return {
            'log_attributes': log_attributes,
            'trace_attributes': list(trace_attributes),
            'event_attributes': list(event_attributes)
        }