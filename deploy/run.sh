#!/bin/bash

set -o errexit

# Regular Colors
Green='\033[0;32m'
Yellow='\033[0;33m'
Red='\033[0;31m'
NC='\033[0m' # No Color

is_command_present() {
    type "$1" >/dev/null 2>&1
}

check_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macOS detected"
        package_manager="brew"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "Linux detected"
        if is_command_present apt-get; then
            package_manager="apt-get"
        elif is_command_present yum; then
            package_manager="yum"
        else
            echo "Unsupported package manager. Please install Python3, pip3, and npm manually."
            exit 1
        fi
    else
        echo "Unsupported OS"
        exit 1
    fi
}

request_sudo() {
    if [[ $EUID != 0 ]]; then
        sudo_cmd="sudo"
        echo "We need sudo access to complete the installation."
        sudo -v
    fi
}

install_dependencies() {
    if ! is_command_present python3; then
        echo "Installing Python3..."
        if [[ $package_manager == "brew" ]]; then
            brew install python
        else
            $sudo_cmd $package_manager install -y python3
        fi
    fi

    if ! is_command_present pip3; then
        echo "Installing pip3..."
        if [[ $package_manager == "brew" ]]; then
            brew install python
        else
            $sudo_cmd $package_manager install -y python3-pip
        fi
    fi

    if ! is_command_present npm; then
        echo "Installing npm..."
        if [[ $package_manager == "brew" ]]; then
            brew install node
        elif [[ $package_manager == "apt-get" ]]; then
            $sudo_cmd $package_manager install -y nodejs npm
        else
            $sudo_cmd $package_manager install -y nodejs npm
        fi
    fi
}

install_python_dependencies() {
    echo "Setting up Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    
    echo "Upgrading pip..."
    python3 -m pip install --upgrade pip
    
    echo "Installing Python dependencies..."
    # Change the path to requirements.txt
    python3 -m pip install -r ../requirements.txt
}

install_appium() {
    if ! is_command_present appium; then
        echo "Installing Appium..."
        $sudo_cmd npm install -g appium
    fi
}

start_mobile_adapter() {
    echo -e "${Yellow}Starting mobile adapter...${NC}"
    source venv/bin/activate
    python3 ../main.py
}

# Main script execution
echo -e "${Green}Setting up the mobile adapter environment...${NC}"

check_os
request_sudo
install_dependencies
install_python_dependencies
install_appium
start_mobile_adapter

echo -e "${Green}Mobile adapter setup and startup complete.${NC}"