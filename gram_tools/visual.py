import ast
import os
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

def visualize_fsm(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        bot_code = file.read()

    tree = ast.parse(bot_code)

    handlers = {}
    fsm_transitions = []

    def get_constant_value(node):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Str):
            return node.s
        else:
            return None

    def extract_handler_info(node):
        handler_info = {
            'name': node.name,
            'trigger': None,
            'type': None,
            'states': [],
            'data_stored': set(),
            'data_retrieved': set()
        }
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                func = decorator.func
                if isinstance(func, ast.Attribute):
                    if isinstance(func.value, ast.Name):
                        dp_method = func.attr
                        handler_info['type'] = dp_method
                        args = decorator.args
                        if args:
                            arg = args[0]
                            if isinstance(arg, ast.Call):
                                if isinstance(arg.func, ast.Name):
                                    func_name = arg.func.id
                                    if func_name == 'Command':
                                        if arg.args and isinstance(arg.args[0], ast.Constant):
                                            command = arg.args[0].value
                                            handler_info['trigger'] = f"/{command}"
                            elif isinstance(arg, ast.Compare):
                                left = arg.left
                                if isinstance(left, ast.Attribute) and isinstance(left.value, ast.Name):
                                    left_name = f"{left.value.id}.{left.attr}"
                                else:
                                    left_name = ast.unparse(left)
                                op = arg.ops[0]
                                if isinstance(op, ast.Eq):
                                    operator = '=='
                                elif isinstance(op, ast.NotEq):
                                    operator = '!='
                                else:
                                    operator = type(op).__name__
                                right = arg.comparators[0]
                                if isinstance(right, ast.Constant):
                                    right_value = right.value
                                else:
                                    right_value = ast.unparse(right)
                                handler_info['trigger'] = f"{left_name} {operator} '{right_value}'"
                            elif isinstance(arg, ast.Attribute):
                                if isinstance(arg.value, ast.Name):
                                    state_name = f"{arg.value.id}.{arg.attr}"
                                    handler_info['states'].append(state_name)
            elif isinstance(decorator, ast.Attribute):
                if isinstance(decorator.value, ast.Name):
                    dp_method = decorator.attr
                    handler_info['type'] = dp_method
        return handler_info

    class HandlerVisitor(ast.NodeVisitor):
        def __init__(self):
            super().__init__()

        def visit_FunctionDef(self, node):
            self.process_function(node)
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node):
            self.process_function(node)
            self.generic_visit(node)

        def process_function(self, node):
            handler_info = extract_handler_info(node)
            is_fsm_handler = False
            variable_names = {}
            data_variables = set()

            for sub_node in ast.walk(node):
                if isinstance(sub_node, ast.Await):
                    call = sub_node.value
                    if isinstance(call, ast.Call):
                        func = call.func
                        if isinstance(func, ast.Attribute):
                            if func.attr == 'set_state':
                                is_fsm_handler = True
                                if call.args:
                                    state_arg = call.args[0]
                                    if isinstance(state_arg, ast.Attribute):
                                        if isinstance(state_arg.value, ast.Name):
                                            state_name = f"{state_arg.value.id}.{state_arg.attr}"
                                            fsm_transitions.append({
                                                'from_handler': node.name,
                                                'to_state': state_name
                                            })
                            elif func.attr in ['finish', 'clear']:
                                is_fsm_handler = True
                                cleared_state_node = f"{node.name}_state_cleared"
                                fsm_transitions.append({
                                    'from_handler': node.name,
                                    'to_state': cleared_state_node,
                                    'action': 'clears state'
                                })
                            elif func.attr == 'update_data':
                                if isinstance(func.value, ast.Name) and func.value.id == 'state':
                                    for keyword in call.keywords:
                                        key = keyword.arg
                                        handler_info['data_stored'].add(key)
                elif isinstance(sub_node, ast.Assign):
                    if isinstance(sub_node.value, ast.Await):
                        await_call = sub_node.value.value
                        if isinstance(await_call, ast.Call):
                            func = await_call.func
                            if isinstance(func, ast.Attribute):
                                if func.attr == 'get_data':
                                    if isinstance(func.value, ast.Name) and func.value.id == 'state':
                                        for target in sub_node.targets:
                                            if isinstance(target, ast.Name):
                                                variable_names[target.id] = 'state_data'
                                                data_variables.add(target.id)
                    elif isinstance(sub_node.value, ast.Call):
                        call = sub_node.value
                        func = call.func
                        if isinstance(func, ast.Attribute):
                            if func.attr == 'get' and func.value.id in data_variables:
                                key_arg = call.args[0]
                                if isinstance(key_arg, ast.Constant):
                                    key = key_arg.value
                                    for target in sub_node.targets:
                                        if isinstance(target, ast.Name):
                                            variable_names[target.id] = f"data[{key}]"
                                            handler_info['data_retrieved'].add(key)
                elif isinstance(sub_node, ast.Subscript):
                    if isinstance(sub_node.value, ast.Name) and sub_node.value.id in data_variables:
                        key_node = sub_node.slice
                        key = get_constant_value(key_node)
                        if key is not None:
                            handler_info['data_retrieved'].add(key)

            if is_fsm_handler or handler_info['data_stored'] or handler_info['data_retrieved']:
                handlers[node.name] = handler_info

    visitor = HandlerVisitor()
    visitor.visit(tree)

    state_handlers = {}
    for handler_name, info in handlers.items():
        for state in info.get('states', []):
            if state not in state_handlers:
                state_handlers[state] = []
            state_handlers[state].append(handler_name)

    G = nx.DiGraph()

    for handler_name, handler in handlers.items():
        trigger_label = f"[{handler.get('trigger')}]" if handler.get('trigger') else ''
        data_stored_label = f"Stores: {', '.join(handler['data_stored'])}" if handler['data_stored'] else ''
        data_retrieved_label = f"Retrieves: {', '.join(handler['data_retrieved'])}" if handler['data_retrieved'] else ''
        extra_info = '\n'.join(filter(None, [trigger_label, data_stored_label, data_retrieved_label]))
        node_label = f"{handler_name}\n{extra_info}" if extra_info else handler_name
        G.add_node(handler_name, label=node_label, type=handler['type'])

    for transition in fsm_transitions:
        from_handler = transition['from_handler']
        to_state = transition['to_state']
        action = transition.get('action', '')
        if action == 'clears state':
            G.add_node(to_state, label='State Cleared', type='state_cleared')
            G.add_edge(from_handler, to_state, label=action)
        elif to_state in state_handlers:
            for to_handler in state_handlers[to_state]:
                G.add_edge(from_handler, to_handler, label=f'sets {to_state}')
        else:
            state_handlers[to_state] = []
            G.add_node(to_state, label=to_state, type='state')
            G.add_edge(from_handler, to_state, label=f'sets {to_state}')

    num_nodes = len(G.nodes())

    plt.figure(figsize=(max(20, num_nodes * 0.5), max(15, num_nodes * 0.4)))

    pos = {}
    components = list(nx.weakly_connected_components(G))
    padding = 5.0
    max_width = 0
    bounding_boxes = []

    for i, component in enumerate(components):
        subgraph = G.subgraph(component)
        n_nodes = len(subgraph.nodes())
        if n_nodes == 0:
            continue
        pos_subgraph = nx.kamada_kawai_layout(subgraph)
        x_offset = max_width + padding if i > 0 else 0
        for node in pos_subgraph:
            pos_subgraph[node][0] += x_offset
        pos.update(pos_subgraph)
        x_values = [pos_subgraph[node][0] for node in pos_subgraph]
        if x_values:
            max_width = max(x_values)
        x_vals = [pos[node][0] for node in component]
        y_vals = [pos[node][1] for node in component]
        min_x, max_x = min(x_vals), max(x_vals)
        min_y, max_y = min(y_vals), max(y_vals)
        bbox_padding = max(0.5 - (num_nodes * 0.01), 0.1)
        bounding_boxes.append(((min_x - bbox_padding, min_y - bbox_padding),
                               (max_x + bbox_padding, max_y + bbox_padding)))

    node_labels = nx.get_node_attributes(G, 'label')
    node_colors = []
    for node in G.nodes(data=True):
        attrs = node[1]
        node_type = attrs.get('type', None)
        if node_type == 'message':
            node_colors.append('lightblue')
        elif node_type == 'callback_query':
            node_colors.append('lightgreen')
        elif node_type == 'state':
            node_colors.append('lightyellow')
        elif node_type == 'state_cleared':
            node_colors.append('orange')
        else:
            node_colors.append('lightgrey')

    node_size = max(800 - (num_nodes * 10), 300)
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_size, edgecolors='black')

    nx.draw_networkx_edges(G, pos, arrows=True, arrowstyle='->', arrowsize=20)

    font_size = max(8 - (num_nodes * 0.05), 4)

    def draw_edge_labels_with_boxes(G, pos, edge_labels, font_size):
        for (n1, n2), label in edge_labels.items():
            x, y = (pos[n1][0] + pos[n2][0]) / 2, (pos[n1][1] + pos[n2][1]) / 2
            plt.text(
                x, y, label, fontsize=font_size, ha='center', va='center',
                bbox=dict(boxstyle="round,pad=0.3", edgecolor='black', facecolor='white')
            )

    edge_labels = nx.get_edge_attributes(G, 'label')
    draw_edge_labels_with_boxes(G, pos, edge_labels, font_size)

    nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=font_size)

    ax = plt.gca()
    for bbox in bounding_boxes:
        (min_corner, max_corner) = bbox
        width = max_corner[0] - min_corner[0]
        height = max_corner[1] - min_corner[1]
        rect = Rectangle(min_corner, width, height,
                         linewidth=1, edgecolor='black', facecolor='none', linestyle='--')
        ax.add_patch(rect)

    plt.title(f"{os.path.basename(file_path)} FSM Visualization")
    plt.axis('off')
    plt.show()
