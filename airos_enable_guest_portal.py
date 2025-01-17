import paramiko
import yaml
from getpass import getpass
import time
import re

# Load the host file (YAML format)
def load_host_file(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

# Function to execute a command and return output
def execute_command(remote_conn, command):
    remote_conn.send(command + "\n")
    time.sleep(2)
    return remote_conn.recv(65535).decode()

# Perform actions on a given AIROS WLC
def manage_wlan_on_airos(host, username, password, ssid):
    try:
        # Create an SSH client
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Connect to the AIROS WLC
        print(f"Connecting to {host}...")
        ssh_client.connect(hostname=host, username=username, password=password)

        # Open an interactive shell session
        remote_conn = ssh_client.invoke_shell()
        time.sleep(1)

        # Handle login prompts
        output = remote_conn.recv(65535).decode()
        if "User:" in output:
            remote_conn.send(username + "\n")
            time.sleep(1)
            output = remote_conn.recv(65535).decode()
        if "Password:" in output:
            remote_conn.send(password + "\n")
            time.sleep(1)
            output = remote_conn.recv(65535).decode()

        # Step 1: Get WLAN ID for the SSID
        print(f"Fetching WLAN ID for SSID '{ssid}' on {host}...")
        wlan_summary_output = execute_command(remote_conn, "show wlan summary")

        # Extract the WLAN ID for the specified SSID
        wlan_id = None
        for line in wlan_summary_output.splitlines():
            if ssid in line:
                match = re.search(r"^\s*(\d+)", line)
                if match:
                    wlan_id = match.group(1)
                    break

        if not wlan_id:
            print(f"Error: Could not find WLAN ID for SSID '{ssid}' on {host}.")
            return

        print(f"Found WLAN ID {wlan_id} for SSID '{ssid}' on {host}.")

        # Step 2: Run configuration commands
        commands = [
            f"config wlan disable {wlan_id}",
            f"config wlan mac-filtering enable {wlan_id}",
            f"config wlan aaa-override enable {wlan_id}",
            f"config wlan nac radius enable {wlan_id}",
            f"config wlan mobility anchor delete {wlan_id} 162.41.34.23",
            f"config wlan mobility anchor add {wlan_id}  162.41.34.21",
            f"config wlan enable {wlan_id}",
            f"show wlan {wlan_id}",
        ]

        for command in commands:
            print(f"Executing command: {command}")
            output = execute_command(remote_conn, command)
            print(output)

    except Exception as e:
        print(f"Error on {host}: {e}")
    finally:
        ssh_client.close()

# Main function
def main():
    # Prompt for credentials
    username = input("Enter the SSH username: ")
    password = getpass("Enter the SSH password: ")

    # Load the host file
    file_path = "./inventory_files/WS_WLC_AIRPS_SM-Hosp_inventory.yaml"  # Replace with the path to your host file
    hosts_data = load_host_file(file_path)

    # Extract AIROS hosts
    airos_hosts = []
    for host, details in hosts_data.get('all', {}).get('children', {}).get('WLCs', {}).get('children', {}).get('AIROS', {}).get('hosts', {}).items():
        if details.get('ansible_network_os') == "airos":
            airos_hosts.append(host)

    # SSID to manage
    ssid = "WHS_Guest"

    # Manage WLAN on all AIROS hosts
    for host in airos_hosts:
        manage_wlan_on_airos(host, username, password, ssid)

if __name__ == "__main__":
    main()
