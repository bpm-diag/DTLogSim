import json
import sys

bpmnPath="../json/bpmn.json"

def parse_again():
    try:
        with open(bpmnPath, "r") as file:
            bpmn_dict = json.load(file)
    except FileNotFoundError:
        sys.exit()
    except json.JSONDecodeError:
        sys.exit()
    except Exception as e:
        sys.exit()


    # Initialize 'previous' and 'next' for each node
    for process in bpmn_dict['process_elements'].values():
        for node in process['node_details'].values():
            node['previous'] = []
            node['next'] = []
            if 'subprocess_details' in node:
                for sub_node in node['subprocess_details'].values():
                    sub_node['previous'] = []
                    sub_node['next'] = []

    # Populate 'previous' and 'next' based on sequence flows
    for flow_id, flow in bpmn_dict['sequence_flows'].items():
        source_id = flow['sourceRef']
        target_id = flow['targetRef']

        # Find the process that contains the source node
        for process in bpmn_dict['process_elements'].values():
            if source_id in process['node_details']:
                process['node_details'][source_id]['next'].append(target_id)
            else:
                # Check if the source node is in a subprocess
                for node in process['node_details'].values():
                    if 'subprocess_details' in node and source_id in node['subprocess_details']:
                        node['subprocess_details'][source_id]['next'].append(target_id)

        """# Find the process that contains the target node
        for process in bpmn_dict['process_elements'].values():
            if target_id in process['node_details']:
                process['node_details'][target_id]['previous'].append(source_id)
            else:
                # Check if the target node is in a subprocess
                for node in process['node_details'].values():
                    if 'subprocess_details' in node and target_id in node['subprocess_details']:
                        node['subprocess_details'][target_id]['previous'].append(source_id)"""
                        
    # After populating 'next', check for parallelGateways with only one 'next' element
    for process in bpmn_dict['process_elements'].values():
        for node in process['node_details'].values():
            if node['type'] == 'parallelGateway' and len(node['next']) == 1:
                node['type'] = 'parallelGateway_close'
            if node['type'] == 'inclusiveGateway' and len(node['next']) == 1:
                node['type'] = 'inclusiveGateway_close'
            if 'subprocess_details' in node:
                for sub_node in node['subprocess_details'].values():
                    if sub_node['type'] == 'parallelGateway' and len(sub_node['next']) == 1:
                        sub_node['type'] = 'parallelGateway_close'
                    if sub_node['type'] == 'inclusiveGateway' and len(sub_node['next']) == 1:
                        sub_node['type'] = 'inclusiveGateway_close'


    # Populate 'previous' based on message flows
    for flow_id, flow in bpmn_dict['collaboration']['messageFlows'].items():
        target_id = flow['targetRef']

        # Find the process that contains the target node
        for process in bpmn_dict['process_elements'].values():
            if target_id in process['node_details']:
                process['node_details'][target_id]['previous'].append(flow['sourceRef'])
            else:
                # Check if the target node is in a subprocess
                for node in process['node_details'].values():
                    if 'subprocess_details' in node and target_id in node['subprocess_details']:
                        node['subprocess_details'][target_id]['previous'].append(flow['sourceRef'])


    with open(bpmnPath, "w") as outfile:
        json.dump(bpmn_dict, outfile, indent=4)

