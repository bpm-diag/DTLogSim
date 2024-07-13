from flask import Flask, render_template, request, send_from_directory, redirect, url_for
import os
import subprocess
import zipfile
import time
import xml.etree.ElementTree as ET
import json


app = Flask(__name__, template_folder='../templates', static_folder='../static')
JSON_FOLDER='../json'
DOWNLOAD_FOLDER='../download'
UPLOAD_FOLDER = '../uploads'
PREUPLOAD_FOLDER = '../preupload'
LOGS_FOLDER = '../logs' # Directory for logs within the container
tagName = "diagbp"


# Create upload and logs folders if they don't exist, FORSE DA RIMUOVERE POI CON DOCKER
os.makedirs(UPLOAD_FOLDER, exist_ok=True) 
os.makedirs(LOGS_FOLDER, exist_ok=True)
os.makedirs(PREUPLOAD_FOLDER, exist_ok=True)
os.makedirs(JSON_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def wait_for_and_remove_flag():
    # Wait for 'flag.txt' to appear in 'uploads' folder, created by main.py after simulation is over
    flag_path = os.path.join(UPLOAD_FOLDER, "flag.txt")
    while not os.path.exists(flag_path):
        time.sleep(1) 
    try:
        os.remove(flag_path) 
        print("Flag file removed successfully.")
    except OSError as e:
        print(f"Error removing flag file: {e}")


@app.route('/', methods=['GET', 'POST'])
def index():
    for filename in os.listdir(PREUPLOAD_FOLDER): # remove old log files
        file_path = os.path.join(PREUPLOAD_FOLDER, filename)
        os.remove(file_path)
    for filename in os.listdir(UPLOAD_FOLDER): # remove old log files
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        os.remove(file_path)
    for filename in os.listdir(DOWNLOAD_FOLDER): # remove old log files
        file_path = os.path.join(DOWNLOAD_FOLDER, filename)
        os.remove(file_path)
    for filename in os.listdir(LOGS_FOLDER): # remove old log files
        file_path = os.path.join(LOGS_FOLDER, filename)
        os.remove(file_path)
    for filename in os.listdir(JSON_FOLDER): # remove old log files
        file_path = os.path.join(JSON_FOLDER, filename)
        os.remove(file_path)
    
    try:
        flag_path = os.path.join(UPLOAD_FOLDER, "flag.txt")
        if os.path.exists(flag_path):
            os.remove(flag_path) 
            print("Flag file removed successfully.")
    except OSError as e:
        print(f"Error removing flag file: {e}")

    if request.method == 'POST':
        bpmn_file = request.files['bpmn_file']
        extra = request.files['extra']

        if bpmn_file:
            bpmn_path = os.path.join(PREUPLOAD_FOLDER, bpmn_file.filename)
            bpmn_file.save(bpmn_path)
            bpmn_file.seek(0)  

            #check diagbp tag
            tree = ET.parse(bpmn_path)
            root = tree.getroot()
            diagbpTag = root.find('.//' + tagName)
            if diagbpTag is not None or extra: #se è presente o il tag nel file o l'extra.json file
                if extra:
                    extra_path = os.path.join(JSON_FOLDER, "extra.json")
                    extra.save(extra_path)
                # Save uploaded BPMN
                bpmn_path = os.path.join(UPLOAD_FOLDER, bpmn_file.filename)
                bpmn_file.save(bpmn_path)
                os.remove(os.path.join(PREUPLOAD_FOLDER, bpmn_file.filename)) 
                return redirect(url_for('results'))
            else:
                bpmn_path = os.path.join(UPLOAD_FOLDER, bpmn_file.filename) #save in upload so that simulator reads it and creates bpmn.json for parameters.html
                bpmn_file.save(bpmn_path)
                wait_for_and_remove_flag()
                return redirect(url_for('parameters'))

    return render_template('index.html')

@app.route('/results')
def results():
    wait_for_and_remove_flag()
    return render_template('results.html')


@app.route('/parameters', methods=['GET', 'POST'])
def parameters():
    bpmn_filename = os.listdir(PREUPLOAD_FOLDER)[0]
    with open(os.path.join(JSON_FOLDER, "bpmn.json"), 'r') as f:
        bpmn_dict = json.load(f)

    if request.method == 'POST':
        diagbp_data = {
            "processInstances": [],
            "startDateTime": str(request.form.get('start_date'))+":00",
            "arrivalRateDistribution": {
                "type": request.form.get('inter_arrival_time_type'),  # Convert to lowercase
                "mean": request.form.get('inter_arrival_time_mean'),
                "arg1": request.form.get('inter_arrival_time_arg1'),
                "arg2": request.form.get('inter_arrival_time_arg2'),
                "timeUnit": request.form.get('inter_arrival_time_time_unit'),
            },
            "timetables": [],
            "resources": [],
            "elements": [],
            "sequenceFlows": [],
            "catchEvents": {}
        }

         # Process instance types
        for key, value in request.form.items():
            if key.startswith('instance_type_'):
                instance_type = value
                instance_count_key = key.replace('instance_type_', 'instance_count_')
                instance_count = request.form.get(instance_count_key)

                diagbp_data["processInstances"].append({
                    "type": instance_type,
                    "count": instance_count
                })

        # Timetables
        timetable_data = {}  # Temporary dictionary to hold timetable data
        for key, value in request.form.items():
            if key.startswith('rule_from_time_'):
                parts = key.split('_')
                timetable_index = int(parts[3])  # Get the timetable index
                rule_index = int(parts[4])        # Get the rule index

                # If the timetable doesn't exist in the dictionary, create it
                if timetable_index not in timetable_data:
                    timetable_data[timetable_index] = {
                        'name': request.form.get(f'timetable_name_{timetable_index}'),
                        'rules': []
                    }

                # Add the rule data to the appropriate timetable
                timetable_data[timetable_index]['rules'].append({
                    "fromTime": str(value)+":00",
                    "toTime": str(request.form.get(f'rule_to_time_{timetable_index}_{rule_index}'))+":00",
                    "fromWeekDay": request.form.get(f'rule_from_day_{timetable_index}_{rule_index}'),
                    "toWeekDay": request.form.get(f'rule_to_day_{timetable_index}_{rule_index}')
                })

        # Now, add the timetables to diagbp_data in the correct order
        diagbp_data["timetables"] = list(timetable_data.values()) 


        # Process resources 
        for key, value in request.form.items():
            if key.startswith('resource_name_'):
                resource_index = key.split("_")[2]  # Extract the resource index from the key

                resource_name = value 
                resource_amount = request.form.get(f'resource_amount_{resource_index}')
                resource_cost = request.form.get(f'resource_cost_{resource_index}')
                resource_timetable = request.form.get(f'resource_timetable_{resource_index}')

                # Setup Time parameters
                setup_time_type = request.form.get(f'resource_{resource_index}_setupTimeType')
                setup_time_mean = request.form.get(f'resource_{resource_index}_setupTimeMean')
                setup_time_arg1 = request.form.get(f'resource_{resource_index}_setupTimeArg1')
                setup_time_arg2 = request.form.get(f'resource_{resource_index}_setupTimeArg2')
                setup_time_unit = request.form.get(f'resource_{resource_index}_setupTimeUnit')
                max_usage = request.form.get(f'resource_maxUsage_{resource_index}')
                if str(setup_time_mean)=="":
                    setup_time_type=""
                    setup_time_unit=""

                diagbp_data["resources"].append({
                    "name": resource_name,
                    "totalAmount": resource_amount,
                    "costPerHour": resource_cost,
                    "timetableName": resource_timetable,
                    "setupTime": {
                        "type": setup_time_type if setup_time_type else "",
                        "mean": setup_time_mean,
                        "arg1": setup_time_arg1,
                        "arg2": setup_time_arg2,
                        "timeUnit": setup_time_unit
                    },
                    "maxUsage": max_usage 
                })

        # Process elements (including those within subprocesses - iterative approach)
        for process_id, process_data in bpmn_dict['process_elements'].items():
            nodes_to_process = [(node_id, node_data) for node_id, node_data in process_data['node_details'].items()]
            while nodes_to_process:
                node_id, node_data = nodes_to_process.pop()

                if node_data['type'] == 'task':
                    durationThreshold= request.form.get(f'durationThreshold_{node_id}', '')
                    duration_threshold_time_unit = request.form.get(f'durationThresholdTimeUnit_{node_id}', 'seconds')
                    if durationThreshold=='':
                        duration_threshold_time_unit = ''
                    # Process task element
                    element_data = {
                        "elementId": node_id,
                        "worklistId": request.form.get(f'worklistId_{node_id}', ''),
                        "fixedCost": request.form.get(f'fixedCost_{node_id}', ''),
                        "costThreshold": request.form.get(f'costThreshold_{node_id}', ''),
                        "durationDistribution": {
                            "type": request.form.get(f'durationType_{node_id}', 'FIXED'),
                            "mean": request.form.get(f'durationMean_{node_id}', ''),
                            "arg1": request.form.get(f'durationArg1_{node_id}', ''),
                            "arg2": request.form.get(f'durationArg2_{node_id}', ''),
                            "timeUnit": request.form.get(f'durationTimeUnit_{node_id}', 'seconds')
                        },
                        "durationThreshold":durationThreshold,
                        "durationThresholdTimeUnit": duration_threshold_time_unit,
                        "resourceIds": []
                    }

                    # Process resources for the current element
                    i = 1
                    while request.form.get(f'resourceName_{i}_{node_id}'):
                        resource_name = request.form.get(f'resourceName_{i}_{node_id}')
                        amount_needed = request.form.get(f'amountNeeded_{i}_{node_id}')
                        group_id = request.form.get(f'groupId_{i}_{node_id}','1')
                        if resource_name and amount_needed:
                            element_data["resourceIds"].append({
                                "resourceName": resource_name,
                                "amountNeeded": amount_needed,
                                "groupId": group_id
                            })
                        i += 1
                    diagbp_data["elements"].append(element_data)

                elif node_data['type'] == 'subProcess':
                    # Add subprocess tasks to the nodes_to_process list
                    for sub_node_id, sub_node_data in node_data['subprocess_details'].items():
                        nodes_to_process.append((sub_node_id, sub_node_data))



        # Process sequence flows
        for flow_id in bpmn_dict['sequence_flows']:
            execution_probability = request.form.get(f'executionProbability_{flow_id}')
            if execution_probability is None:  # Skip if not provided
                continue 
            forced_instance_types = []
            i = 1
            while request.form.get(f'forcedInstanceType_{flow_id}_{i}'):
                forced_instance_type = request.form.get(f'forcedInstanceType_{flow_id}_{i}')
                if forced_instance_type: 
                    forced_instance_types.append({"type": forced_instance_type})
                i += 1

            diagbp_data["sequenceFlows"].append({
                "elementId": flow_id,
                "executionProbability": execution_probability,
                "types": forced_instance_types
            })
            
        # Process catch events (iterative approach)
        for process_id, process_data in bpmn_dict['process_elements'].items():
            nodes_to_process = [(node_id, node_data) for node_id, node_data in process_data['node_details'].items()]
            while nodes_to_process:
                node_id, node_data = nodes_to_process.pop()
                if node_data['type'] in ['intermediateCatchEvent', 'startEvent'] and \
                   node_data.get('subtype') not in ['messageEventDefinition', None]:
                    diagbp_data["catchEvents"][node_id] = {
                        "type": request.form.get(f'catchEventDurationType_{node_id}', 'FIXED'),
                        "mean": request.form.get(f'catchEventDurationMean_{node_id}', ''),
                        "arg1": request.form.get(f'catchEventDurationArg1_{node_id}', ''),
                        "arg2": request.form.get(f'catchEventDurationArg2_{node_id}', ''),
                        "timeUnit": request.form.get(f'catchEventDurationTimeUnit_{node_id}', 'seconds')
                    }
                elif node_data['type'] == 'subProcess':
                    for sub_node_id, sub_node_data in node_data['subprocess_details'].items():
                        nodes_to_process.append((sub_node_id, sub_node_data))

        # Logging option
        diagbp_data["logging_opt"] = request.form.get('logging_opt', 0)  # Default to 0 (disabled)
        diagbp_json = json.dumps(diagbp_data, indent=4)

        source_path = os.path.join(PREUPLOAD_FOLDER, bpmn_filename)
        destination_path = os.path.join(UPLOAD_FOLDER, bpmn_filename)
        with open(source_path, 'r') as bpmn_file:
            bpmn_content = bpmn_file.read()

        with open(destination_path, 'w') as file:
            bpmn_content = bpmn_content.replace('</bpmn:definitions>', f'<diagbp>{diagbp_json}</diagbp>\n</bpmn:definitions>')
            file.write(bpmn_content)
        os.remove(source_path)  

        return redirect(url_for('results'))

    return render_template('parameters.html', bpmn_dict=bpmn_dict)
   

@app.route('/download_logs')
def download_logs():
    # 1. Create the ZIP archive
    zip_filename = 'simulation_logs.zip'
    zip_path = os.path.join(LOGS_FOLDER, zip_filename)
    if os.path.isfile(zip_path): 
        os.remove(zip_path)
    
    with zipfile.ZipFile(zip_path, 'w') as zf:
        for filename in os.listdir(LOGS_FOLDER):
            if filename != zip_filename: # Don't add the zip itself
                file_path = os.path.join(LOGS_FOLDER, filename)
                zf.write(file_path, arcname=filename)  # Add file to archive

    # 2. Send the ZIP file for download
    response = send_from_directory(LOGS_FOLDER, zip_filename, as_attachment=True)

    return response 

@app.route('/download_bpmn_with_parameters')
def download_bpmn_with_parameters():
    for filename in os.listdir(DOWNLOAD_FOLDER):
        if filename.endswith('.bpmn'):
            return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)
    return "BPMN file not found", 404

@app.route('/download_extra_json')
def download_extra_json():
    for filename in os.listdir(DOWNLOAD_FOLDER):
        if filename.endswith('.json'):
            return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)
    return "JSON file not found", 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')