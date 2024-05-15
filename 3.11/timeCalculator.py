#this func takes as input the type, mean, arg1 and arg2 and returns an amount of time

import numpy as np

def convert_to_seconds(input_dict):
    # Define a dictionary to convert time units to seconds
    time_units = {
        "seconds": 1,
        "minutes": 60,
        "hours": 3600,
        "days": 86400
    }

    # Get the type
    type_ = input_dict["type"].upper()

    # Get the mean value
    if input_dict["mean"] != "":
        mean = float(input_dict["mean"])
    else:
        mean = 0.0  # or any other default value

    # Get the time unit
    time_unit = input_dict["timeUnit"].lower()


    # Initialize duration
    duration = 0

    # Calculate duration based on the type
    if type_ == "FIXED":
        duration = mean
    elif type_ == "NORMAL":
        std_dev = float(input_dict["arg1"])
        duration = max(0, np.random.normal(mean, std_dev))
    elif type_ == "EXPONENTIAL":
        duration = np.random.exponential(mean)
    elif type_ == "UNIFORM": #UNIFORM DOESN'T USE MEAN
        low = float(input_dict["arg1"])
        high = float(input_dict["arg2"])
        duration = np.random.uniform(low, high)
    elif type_ == "TRIANGULAR":
        low = float(input_dict["arg1"])
        high = float(input_dict["arg2"])
        mode = mean
        duration = np.random.triangular(low, mode, high)
    elif type_ == "LOGNORMAL":
        std_dev = float(input_dict["arg1"])
        duration = np.random.lognormal(mean, std_dev)
    elif type_ == "GAMMA":
        shape = float(input_dict["arg1"])
        scale = mean / shape
        duration = np.random.gamma(shape, scale)
    elif type_ == "HISTOGRAM":
        # For histogram, we assume arg1 is a list of bin edges and arg2 is a list of corresponding frequencies
        bin_edges = [float(x) for x in input_dict["arg1"].split(',')]
        frequencies = [float(x) for x in input_dict["arg2"].split(',')]
        duration = np.random.choice(bin_edges, p=frequencies)

    # Convert the duration to seconds
    seconds = duration * time_units[time_unit]

    # Return the amount of seconds
    return seconds
