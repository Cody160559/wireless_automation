import time
import random
from netmiko import ConnectHandler
from concurrent.futures import ThreadPoolExecutor

# Configure logging to file only
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    filename="completed_aps.log",  # Log file for completed APs
    filemode="w"  # Overwrite log file on each run
)


#Declare VARs for script
username = input("What is your usernamename? ")
password = input("What is your Password? ")
SOURCE_CONTROLLER_IP = "10.128.0.150"
TARGET_CONTROLLER_IP = "10.128.0.151"

# Source WLC credentials
source_wlc = {
    'host': SOURCE_CONTROLLER_IP,
    'port': 22,
    'username': username,
    'password': password,
    'device_type': 'cisco_ios',  # Use 'cisco_ios' for Cisco IOS-XE
}

# Target WLC credentials
target_wlc = {
    'host': TARGET_CONTROLLER_IP,
    'port': 22,
    'username': username,
    'password': password,
    'device_type': 'cisco_ios',  # Use 'cisco_ios' for Cisco IOS-XE
}

# Functions for WLC operations
def remove_secondary_controller(connection, ap_name):
    command = f"ap name {ap_name} controller secondary None"
    return connection.send_command(command)

def configure_primary_controller(connection, ap_name, controller_name, controller_ip):
    command = f"ap name {ap_name} controller primary {controller_name} {controller_ip}"
    return connection.send_command(command)

def reset_ap(connection, ap_name):
    command = f"ap name {ap_name} reset"
    return connection.send_command(command)

def is_ap_connected_to_target_controller(ap_name):
    """
    Check if the AP is connected to the target controller.
    """
    try:
        with ConnectHandler(**target_wlc) as connection:
            command = f"show ap name {ap_name} config general"
            response = connection.send_command(command)
            if TARGET_CONTROLLER_IP in response:
                return True
    except Exception:
        pass
    return False

def wait_for_ap(ap_name, timeout=600, interval=30):
    """
    Wait for the AP to appear on the target controller.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        print(f"Waiting for AP {ap_name} to connect to the target controller...")
        if is_ap_connected_to_target_controller(ap_name):
            return True
        time.sleep(interval)
    return False

def process_ap(ap_name, index, total):
    """
    Process an AP: remove secondary controller, configure primary controller, reset AP, and verify connection.
    """
    try:
        print(f"Processing AP {index}/{total}: {ap_name}")
        with ConnectHandler(**source_wlc) as connection:
            # Remove secondary controller
            print(f"[{index}/{total}] Removing secondary controller for AP: {ap_name}")
            remove_secondary_controller(connection, ap_name)

            # Configure primary controller
            print(f"[{index}/{total}] Configuring primary controller for AP: {ap_name}")
            configure_primary_controller(connection, ap_name, "K-WLC-C9800-Tmp1", TARGET_CONTROLLER_IP)

            # Reset AP
            print(f"[{index}/{total}] Resetting AP: {ap_name}")
            reset_ap(connection, ap_name)

            # Wait for AP to connect to the target controller
            print(f"[{index}/{total}] Waiting for AP {ap_name} to connect to the target controller...")
            if wait_for_ap(ap_name):
                print(f"[{index}/{total}] AP {ap_name} successfully moved to the target controller.")
                logging.info(f"AP {ap_name} successfully moved to target controller.")
            else:
                print(f"[{index}/{total}] AP {ap_name} failed to connect to the target controller.")
                logging.warning(f"AP {ap_name} failed to connect to target controller.")
    except Exception as e:
        print(f"Error processing AP {ap_name}: {e}")
        logging.error(f"Error processing AP {ap_name}: {e}")

# Read AP names from file
try:
    with open(r'C:\Users\csmith66\Documents\Git\wireless_automation\inventory_files\testbatch.txt', 'r') as ap_list_file:
        ap_names = [line.strip() for line in ap_list_file if line.strip()]
    if not ap_names:
        print("No AP names found in the input file.")
        exit()
except Exception as e:
    print(f"Error reading input file: {e}")
    exit()

# Randomize the order of APs
random.shuffle(ap_names)

# Process APs in random batches of 5 concurrently
batch_size = 2
total_aps = len(ap_names)

for i in range(0, len(ap_names), batch_size):
    batch = ap_names[i:i+batch_size]
    print(f"### Starting batch: {batch}")
    with ThreadPoolExecutor(max_workers=batch_size) as executor:
        executor.map(
            lambda ap: process_ap(ap, ap_names.index(ap) + 1, total_aps),
            batch
        )
