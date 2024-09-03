#!/bin/bash

set -o errexit

# Change to the script's directory
cd "$(dirname "$0")"

check_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macOS detected"
        package_manager="brew"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "Linux detected"
        if type apt-get >/dev/null 2>&1; then
            package_manager="apt-get"
        elif type yum >/dev/null 2>&1; then
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
    echo "Installing dependencies..."
    if [[ $package_manager == "brew" ]]; then
        brew install node
    elif [[ $package_manager == "apt-get" ]]; then
        $sudo_cmd $package_manager update
        $sudo_cmd $package_manager install -y nodejs npm
    else
        $sudo_cmd $package_manager install -y nodejs npm
    fi
}

install_appium() {
    echo "Installing Appium..."
    $sudo_cmd npm install -g appium
}

cd ..
poetry install