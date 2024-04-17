from graphs.visualization.base_graph import BaseGraph


class InductiveGraph(BaseGraph):
    def __init__(
        self,
        process_tree,
        frequency: dict[str, int] = None,
        node_sizes: dict[str, tuple[float, float]] = None,
    ) -> None:
        super().__init__(rankdir="LR")
        self.exclusive_gates_count = 0
        self.parallel_gates_count = 0
        self.silent_activities_count = 0
        self.event_frequency = frequency
        self.node_sizes = node_sizes

        self.build_graph(process_tree)

    def build_graph(self, process_tree) -> None:
        self.add_start_node()
        self.add_end_node()

        start_node, end_node = self.add_section(process_tree)

        self.add_starting_edges([start_node])
        self.add_ending_edges([end_node])

    def add_event(
        self,
        title: str,
        **event_data,
    ) -> None:

        width, height = self.node_sizes.get(title, (1.5, 0.5))
        frequency = self.event_frequency.get(title, 0)
        if frequency > 0:
            event_data["frequency"] = frequency

        label = f"{title}\n{frequency}"
        super().add_node(
            id=title,
            label=label,
            data=event_data,
            width=str(width),
            height=str(height),
            shape="box",
            style="rounded, filled",
            fillcolor="#FFFFFF",
        )

    def add_section(self, process_tree) -> tuple:
        start_node, end_node = None, None

        if isinstance(process_tree, str) or isinstance(process_tree, int):
            if process_tree == "tau":
                silent_activity_id = self.add_silent_activity()
                start_node, end_node = silent_activity_id, silent_activity_id
            else:
                self.add_event(process_tree)
                start_node, end_node = process_tree, process_tree

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
        start_node, end_node = None, None
        for section in process_tree:
            start, end = self.add_section(section)

            if start_node is None:
                start_node = start

            if end_node is not None:
                self.add_edge(end_node, start, weight=None)

            end_node = end

        return start_node, end_node

    def add_section_with_gate(self, process_tree, gate_type: str) -> tuple:
        start_node, end_node = self.add_gate(gate_type)

        for section in process_tree:
            start, end = self.add_section(section)

            self.add_edge(start_node, start, weight=None)
            self.add_edge(end, end_node, weight=None)

        return start_node, end_node

    def add_loop(self, process_tree) -> tuple:
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

    def add_gate(self, type: str):
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

    def add_exclusive_gate(self, **node_attributes):
        start_id = f"exclusive_gate_start_{self.exclusive_gates_count}"
        end_id = f"exclusive_gate_end_{self.exclusive_gates_count}"

        self.add_node(id=start_id, label="X", **node_attributes)
        self.add_node(id=end_id, label="X", **node_attributes)
        self.exclusive_gates_count += 1

        return start_id, end_id

    def add_parallel_gate(self, **node_attributes):
        start_id = f"parallel_gate_start_{self.parallel_gates_count}"
        end_id = f"parallel_gate_end_{self.parallel_gates_count}"

        self.add_node(id=start_id, label="+", **node_attributes)
        self.add_node(id=end_id, label="+", **node_attributes)
        self.parallel_gates_count += 1

        return start_id, end_id

    def add_silent_activity(self):
        node_id = f"silent_activity_{self.silent_activities_count}"
        self.add_node(id=node_id, label=" ", shape="point", fillcolor="#FFFFFF")
        self.silent_activities_count += 1
        return node_id

    def node_to_string(self, id: str) -> tuple[str, str]:
        if "gate" in id or "silent" in id:
            return self.special_node_to_string(id)

        node = self.get_node(id)
        description = f"**Event:** {node.get_id()}"
        if frequency := node.get_data_from_key("frequency"):
            description = f"""{description}\n**Frequency:** {frequency}"""
        return node.get_id(), description

    def special_node_to_string(self, id: str) -> tuple[str, str]:
        title, description = "", ""

        if "exclusive" in id:
            if "start" in id:
                title = "Exclusive Start Gate"
            elif "end" in id:
                title = "Exclusive End Gate"

            description = "**Exclusive Gateway**"
        elif "parallel" in id:
            if "start" in id:
                title = "Parallel Start Gate"
            elif "end" in id:
                title = "Parallel End Gate"
            description = "**Parallel Gateway**"
        elif "silent" in id:
            title = "Silent Activity"
            description = "**Silent Activity**"

        return title, description
