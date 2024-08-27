#!/bin/bash

set -o errexit

# Regular Colors
Green='\033[0;32m'
Yellow='\033[0;33m'
Red='\033[0;31m'
NC='\033[0m' # No Color

# Change to the script's directory
cd "$(dirname "$0")"

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
    echo "Installing dependencies..."
    if [[ $package_manager == "brew" ]]; then
        brew install python node
    elif [[ $package_manager == "apt-get" ]]; then
        $sudo_cmd $package_manager update
        $sudo_cmd $package_manager install -y python3 python3-pip nodejs npm
    else
        $sudo_cmd $package_manager install -y python3 python3-pip nodejs npm
    fi
}

install_python_dependencies() {
    echo "Setting up Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    
    echo "Upgrading pip..."
    python3 -m pip install --upgrade pip
    
    echo "Installing mobileadapt and its dependencies..."
    python3 -m pip install -e ".[dev]"
    
    echo "Installing mobileadapt package..."
    python3 -m pip install mobileadapt
}

install_appium() {
    echo "Installing Appium and drivers..."
    $sudo_cmd npm install -g appium
    appium driver install uiautomator2
    if [[ "$OSTYPE" == "darwin"* ]]; then
        appium driver install xcuitest
    fi
}

start_appium() {
    echo "Starting Appium server..."
    appium &
    APPIUM_PID=$!
    echo "Appium server started with PID: $APPIUM_PID"
    sleep 5  # Give Appium some time to start up
}

setup_mobile_sdk() {
    echo "Setting up Mobile SDK environment..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS-specific paths
        export ANDROID_HOME=$HOME/Library/Android/sdk
        export IOS_HOME=$(xcode-select -p)
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux-specific Android SDK path
        export ANDROID_HOME=$HOME/Android/Sdk
    fi
    
    if [ -d "$ANDROID_HOME" ]; then
        export PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools
        echo "Android SDK path set to: $ANDROID_HOME"
    else
        echo "Android SDK not found at $ANDROID_HOME. Please install Android SDK and set ANDROID_HOME manually."
    fi

    if [[ "$OSTYPE" == "darwin"* ]] && [ -d "$IOS_HOME" ]; then
        echo "iOS SDK path set to: $IOS_HOME"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "iOS SDK not found. Please install Xcode and run xcode-select --install"
    fi
}

# Main script execution
echo -e "${Green}Setting up the mobile adapter environment...${NC}"

check_os
request_sudo
install_dependencies
install_python_dependencies
install_appium
setup_mobile_sdk
start_appium

echo -e "${Green}Mobile adapter setup complete.${NC}"
echo -e "${Yellow}Activating the virtual environment...${NC}"
source "$(dirname "$0")/venv/bin/activate"
echo -e "${Green}Virtual environment activated. You can now use mobileadapt.${NC}"
echo -e "${Yellow}To deactivate the virtual environment when you're done, type 'deactivate'.${NC}"
echo -e "${Yellow}To stop Appium server, run: kill $APPIUM_PID${NC}"

# Keep the script running to maintain the Appium server
wait $APPIUM_PID