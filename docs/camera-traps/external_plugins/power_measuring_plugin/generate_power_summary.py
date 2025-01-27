from datetime import datetime
import json
import os 
from validate_schemas import validate_log_schema, validate_metadata_schema

LOG_DIR = os.environ.get('TRAPS_POWER_LOG_PATH', "/logs/")

def generate_power_summary():
    # open metadata file
    metadata_path = None 
    for f in os.listdir(LOG_DIR):
        if f.startswith('metadata'):
            metadata_path = os.path.join(LOG_DIR, f)
    if not metadata_path:
        print(f"Did not find a metadata file inside {LOG_DIR}; quitting.")
        exit()
    try:
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
            print(f"Summary got metadata: {metadata}")
    except FileNotFoundError:
        print(f"metadata.json not found at path {metadata_path}")
        exit()

    try:
        tools = metadata["tools"]["devices"]
    except Exception as e:
        print(f"Summary did not find a devices, quitting; e: {e}")
        exit()
    # get file paths from metadata file:
    for tool in tools:
        tool_type = tool["device_type"]
        if tool_type == "cpu":
            cpu_file_path = tool["measurement_log_path"]
        elif tool_type == "gpu":
            gpu_file_path = tool["measurement_log_path"]
    
    # parse each of the CPU and GPU files in the same way
    paths = [cpu_file_path, gpu_file_path]
    for p in paths: 
        try:
            with open(p, 'r') as f:
                log_data = json.load(f)
        except FileNotFoundError:
            print(f"could not find json file at path: {p}.")
            exit()  

        # validate 
        validate_metadata_schema(metadata)
        validate_log_schema(log_data)

        # Only initialize summary list the first time
        if p == cpu_file_path:
            plugin_summary, pid_summary = summary_init(metadata)
            summary = {"plugin power summary report": plugin_summary, "pid power summary report": pid_summary}

        # start and end time
        monitor_times(log_data, pid_summary)

        # sum power consumption
        if p == cpu_file_path:
            sum_power_consumption(log_data, pid_summary, plugin_summary, 'cpu_power_consumption')
        else:
            sum_power_consumption(log_data, pid_summary, plugin_summary, 'gpu_power_consumption')
 
    # write to json file
    with open(os.path.join(LOG_DIR, "power_summary_report.json"), "w") as outfile: 
        print("Writing to power_summary_report.json")
        json.dump(summary, outfile, indent=2)

def sum_power_consumption(log, pid_summary, plugin_summary, device):
    """
    sum power log, given log list of dicts, summary list of dicts, device string
    """
    for pid_report in pid_summary:
        pid_report[device] = 0
        num_measurements = 0
        for entry in log:
            logs_at_time = (list(entry.values())[0]) # [[0.0, '2437322'], [1.4, '3423844'], [2.3, '4737228']]
            for j in logs_at_time:
                # if pid in log matches summary, increment power value
                if int(j[1]) == pid_report['pid']:
                    pid_report[device] += float(j[0])
                    num_measurements += 1 
        # take an average of the watts
        if num_measurements > 0:
            pid_report[device] = pid_report[device] / float(num_measurements)

    for plugin_report in plugin_summary:
        plugin_report[device] = 0
        num_measurements = 0
        for pid_report in pid_summary:
            if plugin_report["plugin"] == pid_report['plugin_name']:
                plugin_report[device] += pid_report[device]
                num_measurements += 1 
        # take an average of the watts
        if num_measurements > 0:
            pid_report[device] = pid_report[device] / float(num_measurements)


    return pid_summary, plugin_summary
    
def summary_init(metadata):
    """
    initialize summary report
    """
    pid_summary = []
    plugin_summary = []
    for plugin in metadata['plugins']:
        plugin_summary_dict = {"plugin": plugin['name'], "cpu_power_consumption": None, "gpu_power_consumption": None}
        plugin_summary.append(plugin_summary_dict)
        for pid in plugin['pids']:
            pid_summary_dict = {"pid": pid, "plugin_name": plugin['name'], 
                "start_time": None, "end_time": None, 
                "cpu_power_consumption": None, "gpu_power_consumption": None}
            pid_summary.append(pid_summary_dict)
        
    
    return plugin_summary, pid_summary

def monitor_times(log, summary):
    """
    find start and end time
    """
    all_times = []

    for report in summary:
        for entry in log:
            time = list(entry.keys())[0]
            logs_at_time = (list(entry.values())[0]) # [[0.0, '2437322'], [1.4, '3423844'], [2.3, '4737228']]
            for j in logs_at_time:
                # if pid in log matches summary, append start time and end
                if int(j[1]) == report['pid']:
                    log_datetime = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
                    if report['start_time'] is None and report['end_time'] is None:
                        report['start_time'] = time
                        report['end_time'] = time
                    else:
                        summary_starttime_datetime = datetime.strptime(report['start_time'], "%Y-%m-%d %H:%M:%S")
                        summary_endtime_datetime = datetime.strptime(report['end_time'], "%Y-%m-%d %H:%M:%S")
                        if summary_starttime_datetime > log_datetime:
                            report['start_time'] = time
                        if summary_endtime_datetime < log_datetime:
                            report['end_time'] = time

def main():
    generate_power_summary()  

if __name__ == "__main__":
    main()
