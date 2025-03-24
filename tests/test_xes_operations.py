import unittest
import os
import pandas as pd
import tempfile
import shutil
from pm4py.objects.log.obj import EventLog, Trace, Event
from io_operations.import_operations import ImportOperations
from io_operations.export_operations import ExportOperations

class TestXESOperations(unittest.TestCase):
    
    def setUp(self):
        """Set up the test environment before each test method runs"""
        self.importer = ImportOperations()
        self.exporter = ExportOperations()
        
        # Create a test directory for output files
        self.test_output_dir = os.path.join(tempfile.gettempdir(), 'test_xes_output')
        os.makedirs(self.test_output_dir, exist_ok=True)
        
        # Create a simple test DataFrame
        self.test_df = pd.DataFrame({
            'case:concept:name': ['case1', 'case1', 'case2', 'case2'],
            'concept:name': ['activity1', 'activity2', 'activity1', 'activity3'],
            'time:timestamp': [
                '2023-01-01 10:00:00', 
                '2023-01-01 11:00:00', 
                '2023-01-02 10:00:00', 
                '2023-01-02 11:00:00'
            ]
        })
        
        # Create a simple event log
        self.test_event_log = EventLog()
        
        # First trace
        trace1 = Trace()
        trace1.attributes['concept:name'] = 'case1'
        
        event1 = Event()
        event1['concept:name'] = 'activity1'
        event1['time:timestamp'] = '2023-01-01 10:00:00'
        
        event2 = Event()
        event2['concept:name'] = 'activity2'
        event2['time:timestamp'] = '2023-01-01 11:00:00'
        
        trace1.append(event1)
        trace1.append(event2)
        
        # Second trace
        trace2 = Trace()
        trace2.attributes['concept:name'] = 'case2'
        
        event3 = Event()
        event3['concept:name'] = 'activity1'
        event3['time:timestamp'] = '2023-01-02 10:00:00'
        
        event4 = Event()
        event4['concept:name'] = 'activity3'
        event4['time:timestamp'] = '2023-01-02 11:00:00'
        
        trace2.append(event3)
        trace2.append(event4)
        
        self.test_event_log.append(trace1)
        self.test_event_log.append(trace2)
        
    def tearDown(self):
        """Clean up after each test method runs"""
        # Remove the test output directory
        shutil.rmtree(self.test_output_dir, ignore_errors=True)
    
    def test_export_dataframe_to_xes(self):
        """Test exporting a DataFrame to XES and then reading it back"""
        output_file = os.path.join(self.test_output_dir, 'test_df_export.xes')
        
        # Export DataFrame to XES
        self.exporter.export_to_xes(self.test_df, output_file)
        
        # Check that file exists
        self.assertTrue(os.path.exists(output_file))
        
        # Import the XES file
        event_log = self.importer.read_xes(output_file)
        
        # Verify it's an EventLog
        self.assertIsInstance(event_log, EventLog)
        
        # Verify trace count
        self.assertEqual(len(event_log), 2)
        
        # Convert back to DataFrame and check some values
        df_reimport = self.importer.xes_to_dataframe(event_log)
        self.assertEqual(len(df_reimport), 4)
    
    def test_export_event_log_to_xes(self):
        """Test exporting an EventLog to XES and then reading it back"""
        output_file = os.path.join(self.test_output_dir, 'test_event_log_export.xes')
        
        # Export EventLog to XES
        self.exporter.export_to_xes(self.test_event_log, output_file)
        
        # Check that file exists
        self.assertTrue(os.path.exists(output_file))
        
        # Import the XES file
        event_log = self.importer.read_xes(output_file)
        
        # Verify it's an EventLog
        self.assertIsInstance(event_log, EventLog)
        
        # Verify trace count
        self.assertEqual(len(event_log), 2)
        
        # Verify the first trace's first event's activity name
        self.assertEqual(event_log[0][0]['concept:name'], 'activity1')
    
    def test_export_with_custom_columns(self):
        """Test exporting a DataFrame with custom column mappings"""
        # Create DataFrame with non-standard column names
        custom_df = pd.DataFrame({
            'case_id': ['case1', 'case1', 'case2', 'case2'],
            'activity': ['activity1', 'activity2', 'activity1', 'activity3'],
            'timestamp': [
                '2023-01-01 10:00:00', 
                '2023-01-01 11:00:00', 
                '2023-01-02 10:00:00', 
                '2023-01-02 11:00:00'
            ]
        })
        
        output_file = os.path.join(self.test_output_dir, 'test_custom_cols.xes')
        
        # Export with custom column mappings
        self.exporter.export_dataframe_to_xes(
            custom_df,
            output_file,
            case_id_col='case_id',
            activity_col='activity',
            timestamp_col='timestamp'
        )
        
        # Check that file exists
        self.assertTrue(os.path.exists(output_file))
        
        # Import the XES file
        event_log = self.importer.read_xes(output_file)
        
        # Convert back to DataFrame and verify
        df_reimport = self.importer.xes_to_dataframe(event_log)
        
        # Should now have standard column names
        self.assertTrue('case:concept:name' in df_reimport.columns)
        self.assertTrue('concept:name' in df_reimport.columns)
        self.assertTrue('time:timestamp' in df_reimport.columns)
    
    def test_export_with_attributes(self):
        """Test exporting with custom log and trace attributes"""
        output_file = os.path.join(self.test_output_dir, 'test_attributes.xes')
        
        # Custom attributes
        log_attrs = {
            'creator': 'Test Suite',
            'version': '1.0'
        }
        
        trace_attrs = {
            'department': 'Testing'
        }
        
        # Export with custom attributes
        self.exporter.export_logs_with_attributes(
            self.test_df,
            output_file,
            log_attributes=log_attrs,
            trace_attributes=trace_attrs
        )
        
        # Check that file exists
        self.assertTrue(os.path.exists(output_file))
        
        # Import the XES file
        event_log = self.importer.read_xes(output_file)
        
        # Verify log attributes
        self.assertEqual(event_log.attributes['creator'], 'Test Suite')
        self.assertEqual(event_log.attributes['version'], '1.0')
        
        # Verify trace attributes
        self.assertEqual(event_log[0].attributes['department'], 'Testing')
    
    def test_validate_xes(self):
        """Test the XES validation functionality"""
        # First create a valid XES file
        output_file = os.path.join(self.test_output_dir, 'test_valid.xes')
        self.exporter.export_to_xes(self.test_df, output_file)
        
        # Test validation on valid file
        self.assertTrue(self.importer.validate_xes(output_file))
        
        # Create an invalid file (just a text file)
        invalid_file = os.path.join(self.test_output_dir, 'invalid.xes')
        with open(invalid_file, 'w') as f:
            f.write("<not>valid</xes>")
            
        # Test validation on invalid file
        self.assertFalse(self.importer.validate_xes(invalid_file))
    
    def test_get_xes_attributes(self):
        """Test getting attributes from an XES file"""
        # First create an XES file with attributes
        output_file = os.path.join(self.test_output_dir, 'test_get_attrs.xes')
        
        # Create event log with custom attributes
        event_log = EventLog()
        event_log.attributes['creator'] = 'Test'
        
        trace = Trace()
        trace.attributes['concept:name'] = 'case1'
        trace.attributes['department'] = 'Testing'
        
        event = Event()
        event['concept:name'] = 'activity1'
        event['cost'] = 100
        
        trace.append(event)
        event_log.append(trace)
        
        # Export the event log
        self.exporter.export_to_xes(event_log, output_file)
        
        # Get attributes
        attributes = self.importer.get_xes_attributes(output_file)
        
        # Verify the structure and contents
        self.assertIn('log_attributes', attributes)
        self.assertIn('trace_attributes', attributes)
        self.assertIn('event_attributes', attributes)
        
        self.assertEqual(attributes['log_attributes']['creator'], 'Test')
        self.assertIn('department', attributes['trace_attributes'])
        self.assertIn('cost', attributes['event_attributes'])
    
    def test_export_to_xes_bytes(self):
        """Test exporting to XES as bytes"""
        # Export to bytes
        xes_bytes = self.exporter.export_to_xes_bytes(self.test_df)
        
        # Check we got bytes back
        self.assertIsInstance(xes_bytes, bytes)
        
        # Write bytes to a file
        temp_file = os.path.join(self.test_output_dir, 'test_bytes.xes')
        with open(temp_file, 'wb') as f:
            f.write(xes_bytes)
            
        # Read the file to ensure it's valid XES
        self.assertTrue(self.importer.validate_xes(temp_file))

if __name__ == '__main__':
    unittest.main() 