def diagbp(diagbpPath, bpmn_dict):
    import json
    from datetime import datetime
    from collections import defaultdict

    
    #PROCESS INSTANCES
    exit_loop = False
    processInstances=[]
    print("-------------------PROCESS INSTANCES----------------------")
    keys=["type","count"]
    i=0
    while True:
        i=i+1
        tempDict={}
        for key in keys:
            value=input(f"Insert the {key} for the group n.{i} of process instances (insert empty value to skip to start date): ")
            if not value:
                print("\n")
                exit_loop = True 
                break

            if key=="type":
                tempDict[key] = value.upper()
            else:
                tempDict[key] = value
        if exit_loop: 
            break
        processInstances.append(tempDict)
    
    #DATETIME
    print("-------------------DATETIME----------------------")
    date_str = input("Enter process start date in dd/mm/yyyy format (leave this and next field empty to use datetime of now): ")
    time_str = input("Enter process start time in hh:mm:ss format: ")
    datetime_str = f"{date_str} {time_str}"
    if not datetime_str.strip():
        default_date = datetime.now()
        startDateTime = default_date.strftime("%Y-%m-%dT%H:%M:%S")
    else:
        datetime_obj = datetime.strptime(datetime_str, "%d/%m/%Y %H:%M:%S")
        startDateTime = datetime_obj.strftime("%Y-%m-%dT%H:%M:%S")
    
    #ARRIVAL RATE DISTRIBUTION
    print("-------------------ARRIVAL RATE DISTRIBUTION----------------------")
    arrivalRateDistribution = {}
    keys=["type","mean", "arg1", "arg2", "timeUnit"]
    for key in keys:
        keyDisplay=key
        if key=="type":
            keyDisplay="Inter arrival time type (Fixed, Normal, Exponential, Uniform, Triangular, Log-Normal, Gamma, Histogram)"
        if key=="timeUnit":
            keyDisplay="time unit (seconds/minutes/hours/days)"
        value=input(f"Insert the {keyDisplay} for the arrival rate distribution: ")
        if key=="type":
            value=value.upper()
        arrivalRateDistribution[key] = value

    #TIMETABLES
    print("-------------------TIMETABLES----------------------")
    timetables=[]
    i=0
    while True:
        i=i+1
        timetable={}
        value=input(f"Insert the name of the timetable n.{i} (insert empty value to skip to resources): ")
        if not value:
            print("\n")
            break
        timetable["name"] = value
        rules=[]
        while True:
            rule={}
            fromTime=input(f"Insert the start time (hh:mm:ss) for timetable {value} (insert empty value to end rules for this timetable and go to next timetable): ")
            if not fromTime:
                break
            toTime=input(f"Insert the end time (hh:mm:ss) for timetable {value}: ")
            fromWeekDay=input(f"Insert the start day for timetable {value}: ")
            fromWeekDay=fromWeekDay.upper()
            toWeekDay=input(f"Insert the end day for timetable {value}: ")
            toWeekDay=toWeekDay.upper()
            rule['fromTime'] = fromTime
            rule['toTime'] = toTime
            rule['fromWeekDay'] = fromWeekDay
            rule['toWeekDay'] = toWeekDay
            rules.append(rule)
        timetable["rules"]=rules
        timetables.append(timetable)

    #RESOURCES
    print("-------------------RESOURCES----------------------")
    resources=[]
    exit_loop = False
    keys=["name","totalAmount", "costPerHour", "timetableName"]
    i=0
    while True:
        i=i+1
        resource={}
        for key in keys:
            keyDisplay=key
            if key=="timetableName":
                keyDisplay="timetable name (use the same name given before to the timetable you are referring to)"
            value=input(f"Insert the {keyDisplay} for the resource type n.{i} (insert empty value to skip to elements): ")
            if not value:
                print("\n")
                exit_loop = True 
                break
            resource[key] = value
        if exit_loop: 
            break
        resources.append(resource)
    
    #ELEMENTS
    print("-------------------BPMN TASKS SPECIFICATION (duration etc.)----------------------")
    process_task_dict = {} #key is process name, value is list of task names and ids
    support_big = {}
    elements=[]
    for participant_id, participant in bpmn_dict['collaboration']['participants'].items():
        process_details = bpmn_dict['process_elements'][participant['processRef']]
        process_name = participant['name']

        task_nodes = [(node_id, node['name']) for node_id, node in process_details['node_details'].items() if node['type'] == 'task']
        all_nodes = [(node_id, node['name'], node['type']) for node_id, node in process_details['node_details'].items()]
        for node_id, node in process_details['node_details'].items():
            if node['type'] == 'subProcess':
                task_nodes.extend([(sub_node_id, sub_node['name']) for sub_node_id, sub_node in node['subprocess_details'].items() if sub_node['type'] == 'task'])
                all_nodes.extend([(sub_node_id, sub_node['name'], sub_node['type']) for sub_node_id, sub_node in node['subprocess_details'].items()])

        process_task_dict[process_name] = task_nodes
        support_big[process_name]=all_nodes
    
    support={}
    for process_name, all_nodes in support_big.items():
        for node_id, task_name, node_type in all_nodes:
            support[node_id] = (task_name, node_type)

    for process_name, task_nodes in process_task_dict.items():
        for node_id, task_name in task_nodes:
            element={}
            element["elementId"]=node_id
            group1=["worklistId", "fixedCost", "costThreshold"]
            for key in group1:
                value=input(f"Insert the {key} for the task '{task_name}' of process {process_name}: ")
                element[key] = value
            durationDistributionDict={}
            groupDur=["type", "mean", "arg1", "arg2", "timeUnit"]
            for key in groupDur:
                keyDisplay=key
                if key=="type":
                    keyDisplay="Execution time type (Fixed, Normal, Exponential, Uniform, Triangular, Log-Normal, Gamma, Histogram)"
                if key=="timeUnit":
                    keyDisplay="time unit (seconds/minutes/hours/days)"
                value=input(f"Insert the {keyDisplay} for the duration distribution of task '{task_name}' of process {process_name}: ")
                durationDistributionDict[key] = value
            element["durationDistribution"]=durationDistributionDict
            group2=["durationThreshold", "durationThresholdTimeUnit"]
            for key in group2:
                value=input(f"Insert the {key} for the task '{task_name}' of process {process_name}: ")
                element[key] = value
            resourceIds=[]

            exit_loop = False
            i=0
            while True:
                i=i+1
                resourceId={}
                groupR=["resourceName", "amountNeeded", "groupId"]
                for key in groupR:
                    value=input(f"Resource n.{i} | Insert the {key} for the task '{task_name}' of process {process_name}: ")
                    if not value:
                        exit_loop=True
                        break
                    resourceId[key] = value
                if exit_loop:
                    break
                resourceIds.append(resourceId)
            element["resourceIds"]=resourceIds
            elements.append(element)
            print("--------------------")

    #SEQUENCE FLOWS
    sequence_flows=[]
    print("-------------------XOR PROBABILITIES----------------------")
    sourceRef_counts = defaultdict(int)
    # Iterate over the sequence_flows and count the occurrences of each sourceRef
    for flow in bpmn_dict['sequence_flows'].values():
        sourceRef_counts[flow['sourceRef']] += 1
    # Create a new dictionary to store the flows where the sourceRef appears 2 or more times
    filtered_flows = {}
    # Iterate over the sequence_flows again and add the flows where the sourceRef appears 2 or more times to the new dictionary
    for id, flow in bpmn_dict['sequence_flows'].items():
        if sourceRef_counts[flow['sourceRef']] >= 2:
            filtered_flows[id] = flow
    for id, flow in filtered_flows.items():
        flowName=flow["name"]
        sourceId=flow["sourceRef"]
        targetId=flow["targetRef"]
        sourceName, sourceType = support[sourceId]
        targetName, targetType = support[targetId]
        if sourceType=="exclusiveGateway":
            sequence_flow={}
            sequence_flow["elementId"]=id
            print(f"\nYou are now inserting data for the sequence flow named '{flowName}' that goes from '{sourceName}' to '{targetName}'")
            sequence_flow["executionProbability"]=input(f"Insert a probability (0 to 1 i.e: 0.5):  ")
            types=[]
            i=0
            while True:
                i=i+1
                singleType={}
                singleType["type"] = input(f"Insert the instance type n.{i} that is forced to go into this sequence flow (leave blank to skip): ")
                singleType["type"] = singleType["type"].upper()
                if not singleType["type"]:
                    break
                types.append(singleType)
            sequence_flow["types"]=types
            sequence_flows.append(sequence_flow)
    #TODO: popolare array sequence_flows chiedendo dati per ogni sourceName|flowName|targetName, elementId è id.

    """
    "sequenceFlows": [
        {
          "elementId": "Flow_16n1wa9",
          "executionProbability": "0.5",
          "types": [
            {
              "type": "A"
            },
            {
              "type": "B"
            }
          ],
          "_COMMENTO":"types indica che se sono in un istanza di quel type, allora la scelta è forzata su questa direzione"
        },
        {
          "elementId": "Flow_0d86tug",
          "executionProbability": "0.5"
        }
      ]
    """



    #DATA FINAL
    data = {
        "processInstances": processInstances,
        "startDateTime": startDateTime,
        "arrivalRateDistribution": arrivalRateDistribution,
        "timetables": timetables,
        "resources": resources,
        "elements": elements,
        "sequenceFlows": sequence_flows
    }

    with open(diagbpPath, 'w') as f:
        json.dump(data, f)