from core.graphs.visualization.base_graph import BaseGraph


class InductiveGraph(BaseGraph):
    """A class to represent a InductiveGraph."""

    def __init__(
        self,
        process_tree,
        frequency: dict[str, int] = None,
        node_sizes: dict[str, tuple[float, float]] = None,
    ) -> None:
        """Initialize the InductiveGraph object.

        Parameters
        ----------
        process_tree : tuple
            a tuple representing the process tree. The process tree is a nested tuple where the first element is the operator and the rest of the elements are the children of the operator.
            children can be either a string representing an event or another nested tuple representing a sub-process tree.
        frequency : dict[str, int], optional
            a dictionary containing the frequency of each event, by default None
        node_sizes : dict[str, tuple[float, float]], optional
            a dictionary containing the size of each node, by default None
        """
        super().__init__(rankdir="LR")
        self.exclusive_gates_count = 0
        self.parallel_gates_count = 0
        self.silent_activities_count = 0
        self.event_frequency = frequency
        self.node_sizes = node_sizes
        self.event_count = {}  # Track count of each event for unique IDs
        self.process_tree = process_tree  # Store for reference

        self.build_graph(process_tree)

    def build_graph(self, process_tree) -> None:
        """Build the graph from the process tree.

        Parameters
        ----------
        process_tree : tuple
            a tuple representing the process tree. The process tree is a nested tuple where the first element is the operator and the rest of the elements are the children of the operator.
            children can be either a string representing an event or another nested tuple representing a sub-process tree.
        """
        self.add_start_node()
        self.add_end_node()

        start_node, end_node = self.add_section(process_tree)

        # Handle case where entire tree is tau (hidden)
        if start_node is None or end_node is None:
            # Connect start directly to end
            self.add_edge("Start", "End", weight=None, style="dashed")
        else:
            self.add_starting_edges([start_node])
            self.add_ending_edges([end_node])

    def add_event(
        self,
        title: str,
        **event_data,
    ) -> str:
        """Add an event to the graph.

        Parameters
        ----------
        title : str
            name of the event
        **event_data
            additional data for the event
            
        Returns
        -------
        str
            the unique node ID for this event
        """
        # Generate unique ID for this event instance
        title_str = str(title)
        self.event_count[title_str] = self.event_count.get(title_str, 0) + 1
        count = self.event_count[title_str]
        
        # Always use unique ID with prefix to avoid conflicts with Start/End nodes
        node_id = f"event_{title_str}_{count}"
        
        width, height = (1.5, 0.5)
        frequency = 0
        if self.node_sizes:
            width, height = self.node_sizes.get(title_str, (1.5, 0.5))
        if self.event_frequency:
            frequency = self.event_frequency.get(title_str, 0)
        if frequency > 0:
            event_data["frequency"] = frequency

        label = f"{title_str}\n{frequency}"
        super().add_node(
            id=node_id,
            label=label,
            data=event_data,
            width=str(width),
            height=str(height),
            shape="box",
            style="rounded, filled",
            fillcolor="#FFFFFF",
        )
        return node_id

    def add_section(self, process_tree) -> tuple:
        """Adds a section from the process tree to the graph.
        This can be a sequence, a loop, a parallel section, or a xor section.
        The function recursively adds the children of the section to the graph.

        Parameters
        ----------
        process_tree : tuple
            a tuple representing the process tree. The process tree is a nested tuple where the first element is the operator and the rest of the elements are the children of the operator.
            children can be either a string representing an event or another nested tuple representing a sub-process tree.

        Returns
        -------
        tuple
            a tuple containing the start and end node of the section.
        """
        start_node, end_node = None, None

        if isinstance(process_tree, str) or isinstance(process_tree, int):
            if process_tree == "tau":
                silent_activity_id = self.add_silent_activity()
                start_node, end_node = silent_activity_id, silent_activity_id
            else:
                node_id = self.add_event(process_tree)
                start_node, end_node = node_id, node_id

        elif process_tree[0] == "seq":
            start_node, end_node = self.add_sequence(process_tree[1:])

        elif process_tree[0] == "xor":
            start_node, end_node = self.add_section_with_gate(process_tree[1:], "xor")

        elif process_tree[0] == "par":
            start_node, end_node = self.add_section_with_gate(process_tree[1:], "par")

        elif process_tree[0] == "loop":
            start_node, end_node = self.add_loop(process_tree[1:])

        return start_node, end_node

    def add_sequence(self, process_tree) -> tuple:
        """Adds a sequence section from the process tree to the graph.

        Parameters
        ----------
        process_tree : tuple
            a tuple representing the process tree. The process tree is a nested tuple where the first element is the operator and the rest of the elements are the children of the operator.
            children can be either a string representing an event or another nested tuple representing a sub-process tree.

        Returns
        -------
        tuple
            a tuple containing the start and end node of the sequence section
        """
        start_node, end_node = None, None
        for section in process_tree:
            start, end = self.add_section(section)
            
            # Skip hidden tau nodes in sequence
            if start is None and end is None:
                continue

            if start_node is None:
                start_node = start

            if end_node is not None:
                self.add_edge(end_node, start, weight=None)

            end_node = end

        return start_node, end_node

    def add_section_with_gate(self, process_tree, gate_type: str) -> tuple:
        """Adds a section with a gate from the process tree to the graph. This can be a parallel section or an xor section.

        Parameters
        ----------
        process_tree : tuple
            a tuple representing the process tree. The process tree is a nested tuple where the first element is the operator and the rest of the elements are the children of the operator.
            children can be either a string representing an event or another nested tuple representing a sub-process tree.
        gate_type : str
            the type of the gate, can be either "xor" or "par"

        Returns
        -------
        tuple
            a tuple containing the start and end node of the section
        """
        start_node, end_node = self.add_gate(gate_type)

        for section in process_tree:
            start, end = self.add_section(section)
            self.add_edge(start_node, start, weight=None)
            self.add_edge(end, end_node, weight=None)

        return start_node, end_node

    def add_loop(self, process_tree) -> tuple:
        """Adds a loop section from the process tree to the graph.

        Parameters
        ----------
        process_tree : tuple
            a tuple representing the process tree. The process tree is a nested tuple where the first element is the operator and the rest of the elements are the children of the operator.
            children can be either a string representing an event or another nested tuple representing a sub-process tree.

        Returns
        -------
        tuple
            a tuple containing the start and end node of the loop section
        """
        # get start and end of the loop section,
        # by finding the start and end of the first section
        start_node, end_node = self.add_section(process_tree[0])

        for section in process_tree[1:]:
            start, end = self.add_section(section)
            
            # add edges to the loop section
            # the start of the redo section is the end of the loop section
            # the end of the redo section is the start of the loop section
            self.add_edge(end_node, start, weight=None)
            self.add_edge(end, start_node, weight=None)

        return start_node, end_node

    def add_gate(self, type: str) -> tuple[str, str]:
        """Add a gate to the graph. The gate can be either an xor gate or a parallel gate.

        Parameters
        ----------
        type : str
            the type of the gate, can be either "xor" or "par"

        Returns
        -------
        tuple[str, str]
            a tuple containing the start and end node of the gate

        Raises
        ------
        ValueError
            if the gate type is not supported
        """
        node_attributes = {
            "shape": "diamond",
            "style": "filled",
            "fillcolor": "#FFFFFF",
        }

        if type.lower() == "xor":
            return self.add_exclusive_gate(**node_attributes)

        elif type.lower() == "par":
            return self.add_parallel_gate(**node_attributes)
        else:
            raise ValueError(f"Gate type {type} is not supported")

    def add_exclusive_gate(self, **node_attributes) -> tuple[str, str]:
        """Add an exclusive gate to the graph.

        Parameters
        ----------
        **node_attributes
            additional attributes for the node

        Returns
        -------
        tuple[str, str]
            a tuple containing the start and end node of the exclusive gate
        """
        start_id = f"exclusive_gate_start_{self.exclusive_gates_count}"
        end_id = f"exclusive_gate_end_{self.exclusive_gates_count}"

        self.add_node(id=start_id, label="X", **node_attributes)
        node_attributes["style"] = node_attributes.get("style", "") + ", bold"
        node_attributes["fontname"] = "bold"
        self.add_node(id=end_id, label="X", **node_attributes)
        self.exclusive_gates_count += 1

        return start_id, end_id

    def add_parallel_gate(self, **node_attributes) -> tuple[str, str]:
        """Add a parallel gate to the graph.

        Parameters
        ----------
        **node_attributes
            additional attributes for the node

        Returns
        -------
        tuple[str, str]
            a tuple containing the start and end node of the parallel gate
        """
        start_id = f"parallel_gate_start_{self.parallel_gates_count}"
        end_id = f"parallel_gate_end_{self.parallel_gates_count}"

        self.add_node(id=start_id, label="+", **node_attributes)
        node_attributes["style"] = node_attributes.get("style", "") + ", bold"
        node_attributes["fontname"] = "bold"
        self.add_node(id=end_id, label="+", **node_attributes)
        self.parallel_gates_count += 1

        return start_id, end_id

    def add_silent_activity(self) -> str:
        """Add a silent activity (tau) to the graph.

        Returns
        -------
        str
            the id of the silent activity node
        """
        node_id = f"silent_activity_{self.silent_activities_count}"
        # Render tau as a small gray circle with "τ" label for visibility
        self.add_node(
            id=node_id, 
            label="τ", 
            shape="circle",
            width="0.3",
            height="0.3",
            style="filled",
            fillcolor="#E0E0E0",
            fontsize="10",
            fontcolor="#666666"
        )
        self.silent_activities_count += 1
        return node_id

    def node_to_string(self, id: str) -> tuple[str, str]:
        """Return the node name/id and description for the given node id.
        For special nodes like gates and silent activities, the description contains additional information about the node.

        Parameters
        ----------
        id : str
            id of the node

        Returns
        -------
        tuple[str, str]
            node name/id and description. The description contains the node name and frequency.
            If the node is a special node like a gate or a silent activity, it also contains additional information about the node.
        """
        if "gate" in id or "silent" in id:
            return self.special_node_to_string(id)

        node = self.get_node(id)
        description = f"**Event:** {node.get_id()}"
        if frequency := node.get_data_from_key("frequency"):
            description = f"""{description}\n**Frequency:** {frequency}"""
        return node.get_id(), description

    def special_node_to_string(self, id: str) -> tuple[str, str]:
        """Return the node name/id and description for the given special node id.

        Parameters
        ----------
        id : str
            id of the node

        Returns
        -------
        tuple[str, str]
            node name/id and description. The description contains the node name and additional information about the node.
        """
        title, description = "", ""

        if "exclusive" in id:
            if "start" in id:
                title = "Exclusive Start Gate"
            elif "end" in id:
                title = "Exclusive End Gate"

            description = f"""**Exclusive Gateway**
            
            The Exclusive Gateway is used to represent a decision point in the process flow."""
        elif "parallel" in id:
            if "start" in id:
                title = "Parallel Start Gate"
            elif "end" in id:
                title = "Parallel End Gate"
            description = f"""**Parallel Gateway**
            
            The Parallel Gateway is used to represent a synchronization point in the process flow."""
        elif "silent" in id:
            title = "Silent Activity"
            description = f"""**Silent Activity**
            
            A silent activity is an activity that does not have any effect on the process flow. It is used to represent a transition in the process flow without any actual work being done."""

        return title, description
