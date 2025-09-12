import unittest
from mining_algorithms.process_tree import ProcessTreeNode, Operator


class TestProcessTreeNode(unittest.TestCase):
    """Test cases for ProcessTreeNode functionality."""

    def setUp(self):
        """Set up common test nodes."""
        # Simple activity nodes
        self.activity_a = ProcessTreeNode(Operator.ACTIVITY, "A")
        self.activity_b = ProcessTreeNode(Operator.ACTIVITY, "B")
        self.activity_c = ProcessTreeNode(Operator.ACTIVITY, "C")
        
        # Tau node
        self.tau_node = ProcessTreeNode(Operator.TAU)
        
        # Composite nodes
        self.seq_node = ProcessTreeNode(
            Operator.SEQUENCE, 
            children=[self.activity_a, self.activity_b]
        )
        
        self.par_node = ProcessTreeNode(
            Operator.PARALLEL,
            children=[self.activity_a, self.activity_b, self.activity_c]
        )
        
        self.xor_node = ProcessTreeNode(
            Operator.XOR,
            children=[self.activity_a, self.tau_node]
        )

    def test_activity_node_creation(self):
        """Test creation of activity nodes."""
        node = ProcessTreeNode(Operator.ACTIVITY, "TestActivity")
        
        self.assertEqual(node.operator, Operator.ACTIVITY)
        self.assertEqual(node.label, "TestActivity")
        self.assertEqual(len(node.children), 0)

    def test_tau_node_creation(self):
        """Test creation of tau nodes."""
        node = ProcessTreeNode(Operator.TAU)
        
        self.assertEqual(node.operator, Operator.TAU)
        self.assertIsNone(node.label)
        self.assertEqual(len(node.children), 0)

    def test_composite_node_creation(self):
        """Test creation of composite nodes with children."""
        children = [self.activity_a, self.activity_b]
        node = ProcessTreeNode(Operator.SEQUENCE, children=children)
        
        self.assertEqual(node.operator, Operator.SEQUENCE)
        self.assertEqual(len(node.children), 2)
        self.assertIn(self.activity_a, node.children)
        self.assertIn(self.activity_b, node.children)

    def test_empty_children_default(self):
        """Test that children default to empty list."""
        node = ProcessTreeNode(Operator.XOR)
        
        self.assertEqual(len(node.children), 0)
        self.assertIsInstance(node.children, list)

    def test_activity_node_repr(self):
        """Test string representation of activity nodes."""
        node = ProcessTreeNode(Operator.ACTIVITY, "TestActivity")
        
        self.assertEqual(repr(node), "Activity(TestActivity)")

    def test_tau_node_repr(self):
        """Test string representation of tau nodes."""
        self.assertEqual(repr(self.tau_node), "Tau")

    def test_composite_node_repr(self):
        """Test string representation of composite nodes."""
        expected = "SEQUENCE(Activity(A), Activity(B))"
        self.assertEqual(repr(self.seq_node), expected)

    def test_nested_node_repr(self):
        """Test string representation of nested composite nodes."""
        nested_node = ProcessTreeNode(
            Operator.XOR,
            children=[self.seq_node, self.activity_c]
        )
        
        expected = "XOR(SEQUENCE(Activity(A), Activity(B)), Activity(C))"
        self.assertEqual(repr(nested_node), expected)

    def test_activity_to_tuple(self):
        """Test tuple conversion of activity nodes."""
        self.assertEqual(self.activity_a.to_tuple(), "A")
        self.assertEqual(self.activity_b.to_tuple(), "B")

    def test_tau_to_tuple(self):
        """Test tuple conversion of tau nodes."""
        self.assertEqual(self.tau_node.to_tuple(), "tau")

    def test_sequence_to_tuple(self):
        """Test tuple conversion of sequence nodes."""
        expected = ("seq", "A", "B")
        self.assertEqual(self.seq_node.to_tuple(), expected)

    def test_parallel_to_tuple(self):
        """Test tuple conversion of parallel nodes."""
        expected = ("par", "A", "B", "C")
        self.assertEqual(self.par_node.to_tuple(), expected)

    def test_xor_to_tuple(self):
        """Test tuple conversion of XOR nodes."""
        expected = ("xor", "A", "tau")
        self.assertEqual(self.xor_node.to_tuple(), expected)

    def test_complex_nested_to_tuple(self):
        """Test tuple conversion of complex nested structures."""
        # Create: XOR(SEQ(A, B), PAR(C, TAU))
        seq_part = ProcessTreeNode(
            Operator.SEQUENCE,
            children=[self.activity_a, self.activity_b]
        )
        
        par_part = ProcessTreeNode(
            Operator.PARALLEL,
            children=[self.activity_c, self.tau_node]
        )
        
        complex_node = ProcessTreeNode(
            Operator.XOR,
            children=[seq_part, par_part]
        )
        
        expected = ("xor", ("seq", "A", "B"), ("par", "C", "tau"))
        self.assertEqual(complex_node.to_tuple(), expected)

    def test_loop_node_operations(self):
        """Test loop node creation and operations."""
        loop_node = ProcessTreeNode(
            Operator.LOOP,
            children=[self.activity_a, self.tau_node]
        )
        
        self.assertEqual(loop_node.operator, Operator.LOOP)
        self.assertEqual(len(loop_node.children), 2)
        
        expected_tuple = ("loop", "A", "tau")
        self.assertEqual(loop_node.to_tuple(), expected_tuple)
        
        expected_repr = "LOOP(Activity(A), Tau)"
        self.assertEqual(repr(loop_node), expected_repr)

    def test_deep_nesting_to_tuple(self):
        """Test tuple conversion with deep nesting."""
        # Create: SEQ(A, XOR(B, SEQ(C, LOOP(D, TAU))))
        activity_d = ProcessTreeNode(Operator.ACTIVITY, "D")
        
        loop_inner = ProcessTreeNode(
            Operator.LOOP,
            children=[activity_d, self.tau_node]
        )
        
        seq_inner = ProcessTreeNode(
            Operator.SEQUENCE,
            children=[self.activity_c, loop_inner]
        )
        
        xor_middle = ProcessTreeNode(
            Operator.XOR,
            children=[self.activity_b, seq_inner]
        )
        
        seq_outer = ProcessTreeNode(
            Operator.SEQUENCE,
            children=[self.activity_a, xor_middle]
        )
        
        expected = ("seq", "A", ("xor", "B", ("seq", "C", ("loop", "D", "tau"))))
        self.assertEqual(seq_outer.to_tuple(), expected)

    def test_single_child_nodes(self):
        """Test nodes with single children."""
        single_child_node = ProcessTreeNode(
            Operator.XOR,
            children=[self.activity_a]
        )
        
        expected_tuple = ("xor", "A")
        self.assertEqual(single_child_node.to_tuple(), expected_tuple)
        
        expected_repr = "XOR(Activity(A))"
        self.assertEqual(repr(single_child_node), expected_repr)

    def test_empty_operator_nodes(self):
        """Test nodes with no children for composite operators."""
        empty_seq = ProcessTreeNode(Operator.SEQUENCE, children=[])
        
        expected_tuple = ("seq",)
        self.assertEqual(empty_seq.to_tuple(), expected_tuple)
        
        expected_repr = "SEQUENCE()"
        self.assertEqual(repr(empty_seq), expected_repr)

    def test_all_operators_enum_values(self):
        """Test that all operator enum values work correctly."""
        operators = [
            (Operator.SEQUENCE, "seq"),
            (Operator.XOR, "xor"), 
            (Operator.PARALLEL, "par"),
            (Operator.LOOP, "loop"),
            (Operator.TAU, "tau"),
            (Operator.ACTIVITY, "activity")
        ]
        
        for op_enum, op_value in operators:
            self.assertEqual(op_enum.value, op_value)

    def test_modifying_children_after_creation(self):
        """Test modifying children list after node creation."""
        node = ProcessTreeNode(Operator.PARALLEL)
        
        # Initially empty
        self.assertEqual(len(node.children), 0)
        
        # Add children
        node.children.append(self.activity_a)
        node.children.append(self.activity_b)
        
        self.assertEqual(len(node.children), 2)
        
        expected_tuple = ("par", "A", "B")
        self.assertEqual(node.to_tuple(), expected_tuple)

    def test_node_equality_by_structure(self):
        """Test that nodes with same structure produce same tuples."""
        # Create two identical sequence nodes
        seq1 = ProcessTreeNode(
            Operator.SEQUENCE,
            children=[
                ProcessTreeNode(Operator.ACTIVITY, "X"),
                ProcessTreeNode(Operator.ACTIVITY, "Y")
            ]
        )
        
        seq2 = ProcessTreeNode(
            Operator.SEQUENCE,
            children=[
                ProcessTreeNode(Operator.ACTIVITY, "X"),
                ProcessTreeNode(Operator.ACTIVITY, "Y")
            ]
        )
        
        # They should produce the same tuple
        self.assertEqual(seq1.to_tuple(), seq2.to_tuple())
        self.assertEqual(seq1.to_tuple(), ("seq", "X", "Y"))


if __name__ == '__main__':
    unittest.main() 