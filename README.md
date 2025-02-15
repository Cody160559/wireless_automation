# Wireless Automation Toolkit

This repository contains scripts and Ansible playbooks for automating tasks on Cisco Wireless LAN Controllers (WLC) and Access Points (AP). These tools are designed to manage WLANs, move APs between controllers, reboot APs, and enable/disable guest portal access.

---

## Table of Contents

1. [Setup](#setup)
    - [Virtual Environment](#virtual-environment)
    - [Required Python Packages](#required-python-packages)
2. [Scripts Overview](#scripts-overview)
    - [Enable/Disable Guest Portal Access](#1-enabledisable-guest-portal-access)
    - [Move AP Between Controllers](#2-move-ap-between-controllers)
    - [Reboot APs by Site Tag](#3-reboot-aps-by-site-tag)
3. [Ansible Playbooks](#ansible-playbooks)
    - [Enable Guest Portal Access](#1-enable-guest-portal-access)
4. [Usage](#usage)
    - [Running Python Scripts](#running-python-scripts)
    - [Running Ansible Playbooks](#running-ansible-playbooks)
5. [Logs](#logs)
6. [Notes](#notes)

---

## Setup

### Virtual Environment

1. Create a Python virtual environment:
   ```bash
   python3 -m venv venv
   ```
2. Activate the virtual environment:
   - **Linux/macOS**:
     ```bash
     source venv/bin/activate
     ```
   - **Windows**:
     ```bash
     .\venv\Scripts\activate
     ```

### Required Python Packages

Install the required dependencies:
```bash
pip install -r requirements.txt
```

If `requirements.txt` is not available, manually install the following:
```bash
pip install paramiko netmiko ansible pyyaml
```

---

## Scripts Overview

### 1. Enable/Disable Guest Portal Access

- **`airos_enable_guest_portal.py`**:
  Enables the guest portal on a specified SSID by configuring WLAN settings.

- **`airos_disable_guest_portal.py`**:
  Disables the guest portal for a specified SSID by modifying WLAN configurations.

### 2. Move AP Between Controllers

- **`move_ap_c2c.py`**:
  Moves Access Points (APs) from a source WLC to a target WLC, verifying the migration and logging results.

### 3. Reboot APs by Site Tag

- **`reboot_AP_site_tag.py`**:
  Reboots all APs assigned to a specific site tag in random order, with delays between reboots.

---

## Ansible Playbooks

### 1. Enable Guest Portal Access

- **`enable_guest_wifi_portal.ansible.yml`**:
  Automates enabling guest portal access on Cisco IOS XE WLCs for a specified SSID.

---

## Usage

### Running Python Scripts

1. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```
2. Run the desired script:
   ```bash
   python <script_name>.py
   ```
   Replace `<script_name>` with the script file name.

3. Follow the on-screen prompts for credentials and required inputs.

### Running Ansible Playbooks

1. Ensure the `ansible.cfg` and inventory files are properly configured.
2. Run the playbook:
   ```bash
   ansible-playbook <playbook_name>.yml -i inventory.yml
   ```
3. Example for enabling the guest portal:
   ```bash
   ansible-playbook enable_guest_wifi_portal.ansible.yml -i inventory.yml
   ```
4. Enter the SSH username and password when prompted.

---

## Logs

- **`completed_aps.log`**:
  - Used by scripts like `move_ap_c2c.py` to log the migration status of Access Points.
  - Contains details such as successful connections, authentication, and AP migrations.

---

## Notes

- Ensure you have SSH access to the WLCs and appropriate permissions.
- Update the inventory or script configuration to match your network setup.
