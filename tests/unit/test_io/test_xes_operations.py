import unittest
import os
import pandas as pd
import tempfile
import shutil
from io_ops.import_ import ImportOperations


class TestXESOperations(unittest.TestCase):
    
    def setUp(self):
        """Set up the test environment before each test method runs"""
        self.importer = ImportOperations()
        
        # Create a test directory for output files
        self.test_output_dir = os.path.join(tempfile.gettempdir(), 'test_xes_output')
        os.makedirs(self.test_output_dir, exist_ok=True)
        
        # Create a simple test DataFrame with proper datetime format
        self.test_df = pd.DataFrame({
            'case:concept:name': ['case1', 'case1', 'case2', 'case2'],
            'concept:name': ['activity1', 'activity2', 'activity1', 'activity3'],
            'time:timestamp': pd.to_datetime([
                '2023-01-01 10:00:00', 
                '2023-01-01 11:00:00', 
                '2023-01-02 10:00:00', 
                '2023-01-02 11:00:00'
            ])
        })
        
        # Create a sample XES file for testing
        self.sample_xes_content = '''<?xml version="1.0" encoding="UTF-8" ?>
<log>
    <trace>
        <string key="concept:name" value="case1"/>
        <event>
            <string key="concept:name" value="activity1"/>
            <date key="time:timestamp" value="2023-01-01T10:00:00"/>
        </event>
        <event>
            <string key="concept:name" value="activity2"/>
            <date key="time:timestamp" value="2023-01-01T11:00:00"/>
        </event>
    </trace>
    <trace>
        <string key="concept:name" value="case2"/>
        <event>
            <string key="concept:name" value="activity1"/>
            <date key="time:timestamp" value="2023-01-02T10:00:00"/>
        </event>
        <event>
            <string key="concept:name" value="activity3"/>
            <date key="time:timestamp" value="2023-01-02T11:00:00"/>
        </event>
    </trace>
</log>'''
        
        # Write sample XES file
        self.sample_xes_path = os.path.join(self.test_output_dir, 'sample.xes')
        with open(self.sample_xes_path, 'w', encoding='utf-8') as f:
            f.write(self.sample_xes_content)
        
    def tearDown(self):
        """Clean up after each test method runs"""
        # Remove the test output directory
        shutil.rmtree(self.test_output_dir, ignore_errors=True)
    
    def test_read_xes_returns_dataframe(self):
        """Test that reading XES file returns a DataFrame"""
        df = self.importer.read_xes(self.sample_xes_path)
        
        # Verify it's a DataFrame
        self.assertIsInstance(df, pd.DataFrame)
        
        # Verify row count (4 events)
        self.assertEqual(len(df), 4)
    
    def test_read_xes_has_correct_columns(self):
        """Test that the DataFrame has expected columns"""
        df = self.importer.read_xes(self.sample_xes_path)
        
        # Check for expected columns
        self.assertIn('concept:name', df.columns)
        self.assertIn('case:concept:name', df.columns)
        self.assertIn('time:timestamp', df.columns)
    
    def test_read_xes_case_ids(self):
        """Test that case IDs are correctly extracted"""
        df = self.importer.read_xes(self.sample_xes_path)
        
        # Check case IDs
        case_ids = df['case:concept:name'].unique().tolist()
        self.assertIn('case1', case_ids)
        self.assertIn('case2', case_ids)
        self.assertEqual(len(case_ids), 2)
    
    def test_read_xes_activities(self):
        """Test that activities are correctly extracted"""
        df = self.importer.read_xes(self.sample_xes_path)
        
        # Check activities
        activities = df['concept:name'].unique().tolist()
        self.assertIn('activity1', activities)
        self.assertIn('activity2', activities)
        self.assertIn('activity3', activities)
    
    def test_read_xes_with_namespace(self):
        """Test reading XES file with namespace"""
        xes_with_ns = '''<?xml version="1.0" encoding="UTF-8" ?>
<log xmlns="http://www.xes-standard.org/">
    <trace>
        <string key="concept:name" value="case1"/>
        <event>
            <string key="concept:name" value="activity1"/>
        </event>
    </trace>
</log>'''
        
        xes_path = os.path.join(self.test_output_dir, 'with_namespace.xes')
        with open(xes_path, 'w', encoding='utf-8') as f:
            f.write(xes_with_ns)
        
        df = self.importer.read_xes(xes_path)
        
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 1)
    
    def test_read_xes_with_various_types(self):
        """Test reading XES file with different attribute types"""
        xes_content = '''<?xml version="1.0" encoding="UTF-8" ?>
<log>
    <trace>
        <string key="concept:name" value="case1"/>
        <event>
            <string key="concept:name" value="activity1"/>
            <int key="cost" value="100"/>
            <float key="duration" value="1.5"/>
            <boolean key="completed" value="true"/>
        </event>
    </trace>
</log>'''
        
        xes_path = os.path.join(self.test_output_dir, 'various_types.xes')
        with open(xes_path, 'w', encoding='utf-8') as f:
            f.write(xes_content)
        
        df = self.importer.read_xes(xes_path)
        
        self.assertEqual(len(df), 1)
        self.assertIn('cost', df.columns)
        self.assertIn('duration', df.columns)
        self.assertIn('completed', df.columns)
        
        # Check types
        self.assertEqual(df['cost'].iloc[0], 100)
        self.assertEqual(df['duration'].iloc[0], 1.5)
        self.assertEqual(df['completed'].iloc[0], True)
    
    def test_validate_xes_valid_file(self):
        """Test validation on a valid XES file"""
        self.assertTrue(self.importer.validate_xes(self.sample_xes_path))
    
    def test_validate_xes_invalid_file(self):
        """Test validation on an invalid file"""
        invalid_file = os.path.join(self.test_output_dir, 'invalid.xes')
        with open(invalid_file, 'w') as f:
            f.write("<not>valid xes</not>")
            
        self.assertFalse(self.importer.validate_xes(invalid_file))
    
    def test_validate_xes_structure(self):
        """Test the internal XES structure validation"""
        self.assertTrue(self.importer._validate_xes_structure(self.sample_xes_path))
        
        # Create file without traces
        no_traces = '''<?xml version="1.0" encoding="UTF-8" ?>
<log>
</log>'''
        no_traces_path = os.path.join(self.test_output_dir, 'no_traces.xes')
        with open(no_traces_path, 'w', encoding='utf-8') as f:
            f.write(no_traces)
        
        self.assertFalse(self.importer._validate_xes_structure(no_traces_path))
    
    def test_get_xes_attributes(self):
        """Test getting attributes from an XES file"""
        attributes = self.importer.get_xes_attributes(self.sample_xes_path)
        
        # Verify the structure
        self.assertIn('log_attributes', attributes)
        self.assertIn('trace_attributes', attributes)
        self.assertIn('event_attributes', attributes)
        
        # Check event attributes
        self.assertIn('concept:name', attributes['event_attributes'])
        self.assertIn('time:timestamp', attributes['event_attributes'])
    
    def test_read_xes_empty_trace(self):
        """Test reading XES file with empty traces"""
        xes_content = '''<?xml version="1.0" encoding="UTF-8" ?>
<log>
    <trace>
        <string key="concept:name" value="empty_case"/>
    </trace>
    <trace>
        <string key="concept:name" value="case1"/>
        <event>
            <string key="concept:name" value="activity1"/>
        </event>
    </trace>
</log>'''
        
        xes_path = os.path.join(self.test_output_dir, 'empty_trace.xes')
        with open(xes_path, 'w', encoding='utf-8') as f:
            f.write(xes_content)
        
        df = self.importer.read_xes(xes_path)
        
        # Should only have 1 event (from the non-empty trace)
        self.assertEqual(len(df), 1)


if __name__ == '__main__':
    unittest.main()
