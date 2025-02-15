#!/usr/bin/env python3

import re
import random
import time
import getpass
from netmiko import ConnectHandler

def parse_site_tags(show_output):
    """
    Parse 'show wireless tag site summary' output to list available site tags.
    """
    site_tags = []
    for line in show_output.splitlines():
        line = line.strip()
        if not line:
            continue
        if ("Site Tag Name" in line) or ("Number of Site Tags" in line) or ("--------" in line):
            continue
        parts = line.split()
        if parts:
            site_tags.append(parts[0])
    return site_tags

def parse_aps_by_site_tag(show_output, chosen_tag):
    """
    Parse 'show ap tag summary' to return a list of AP names whose Site Tag matches chosen_tag.

    Example line in 'show ap tag summary':
      AD3A-LAB-AP01   00f6.6373.5366   LAB    APG_AD    AD    No  Static

    Columns:
      0 => AP Name
      1 => AP Mac
      2 => Site Tag Name
      3 => Policy Tag Name
      4 => RF Tag Name
      5 => Misconfigured
      6 => Tag Source
    """
    ap_list = []
    for line in show_output.splitlines():
        line = line.strip()
        # Skip headers/separators
        if not line:
            continue
        if ("AP Name" in line) or ("-------" in line) or ("Number of APs" in line):
            continue
        
        parts = line.split(None, 6)
        if len(parts) < 3:
            continue
        
        ap_name  = parts[0]
        site_tag = parts[2]
        
        if site_tag == chosen_tag:
            ap_list.append(ap_name)
    return ap_list

def main():
    # Prompt for device login info
    controller_ip = input("Enter the 9800 controller IP address: ")
    username = input("Enter username: ")
    password = getpass.getpass("Enter password: ")

    # Netmiko connection parameters
    wlc = {
        'device_type': 'cisco_ios',  # Usually works for Catalyst 9800
        'ip': controller_ip,
        'username': username,
        'password': password,
        'fast_cli': False,
    }

    # Connect
    net_connect = ConnectHandler(**wlc)

    # 1) Disable paging to avoid "--More--" issues
    net_connect.send_command("terminal length 0", delay_factor=2, read_timeout=30)

    # 2) Ensure we are at exec prompt, not in config mode
    net_connect.exit_config_mode()

    # 3) Retrieve site tags from 'show wireless tag site summary'
    print("\nRetrieving Site Tags...\n")
    site_tag_summary = net_connect.send_command(
        command_string="show wireless tag site summary",
        delay_factor=2,
        read_timeout=30
    )
    site_tags = parse_site_tags(site_tag_summary)
    site_tags = sorted(set(site_tags))  # Deduplicate + sort

    if not site_tags:
        print("No site tags found. Exiting.")
        net_connect.disconnect()
        return

    # Present site tag menu
    print("Available Site Tags:\n")
    for idx, tag in enumerate(site_tags, start=1):
        print(f"{idx}) {tag}")
    print()

    # Let user pick a site tag
    while True:
        choice = input("Enter the number of the Site Tag you want to reboot APs for: ")
        if choice.isdigit() and 1 <= int(choice) <= len(site_tags):
            chosen_tag = site_tags[int(choice) - 1]
            break
        else:
            print("Invalid choice. Try again.\n")

    print(f"\nYou selected site tag: {chosen_tag}\n")

    # 4) Retrieve APs matching that site tag from 'show ap tag summary'
    print("Retrieving APs assigned to that site tag...\n")
    ap_tag_summary = net_connect.send_command(
        command_string="show ap tag summary",
        delay_factor=5,
        read_timeout=120
    )
    ap_list = parse_aps_by_site_tag(ap_tag_summary, chosen_tag)

    if not ap_list:
        print(f"No APs found for site tag '{chosen_tag}'. Exiting.")
        net_connect.disconnect()
        return

    print(f"Found {len(ap_list)} AP(s) with site tag '{chosen_tag}'.\n")

    # 5) Randomize AP list
    random.shuffle(ap_list)

    print("Rebooting APs in random order:\n")
    for ap in ap_list:
        print(f" - {ap}")
    print()

    # 6) Reboot each AP, one by one, with 5-minute delay in between
    for i, ap in enumerate(ap_list, start=1):
        print(f"--- Rebooting AP {i}/{len(ap_list)}: {ap} ---")
        # Use 'reset' instead of 'reload'
        command = f"ap name {ap} reset"
        reboot_output = net_connect.send_command_timing(command, strip_prompt=False, strip_command=False)
        
        # If controller asks for confirmation, handle it
        if "confirm" in reboot_output.lower():
            reboot_output += net_connect.send_command_timing("\n", strip_prompt=False, strip_command=False)

        print(reboot_output)
        print(f"--- Finished rebooting AP: {ap} ---\n")

        # Wait 5 minutes before rebooting the next AP
        if i < len(ap_list):
            print("Waiting 5 minutes before rebooting the next AP...\n")
            time.sleep(300)  # 300 seconds = 5 minutes

    print("All selected APs have been rebooted.\n")
    net_connect.disconnect()

if __name__ == "__main__":
    main()
