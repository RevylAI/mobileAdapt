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
    echo "Installing Python dependencies..."
    $sudo_cmd pip3 install -r ../requirements.txt
}

install_appium() {
    if ! is_command_present appium; then
        echo "Installing Appium..."
        $sudo_cmd npm install -g appium
    fi
}

install_ios_dependencies() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Installing iOS dependencies..."
        brew install libimobiledevice
        brew install ideviceinstaller
        brew install ios-deploy
        brew install carthage
    else
        echo "iOS development is only supported on macOS"
    fi
}

install_android_dependencies() {
    echo "Installing Android dependencies..."
    
    # Set up Android SDK directory
    export ANDROID_SDK_ROOT="$HOME/Library/Android/sdk"
    export ANDROID_HOME="$ANDROID_SDK_ROOT"
    export PATH="$ANDROID_SDK_ROOT/cmdline-tools/latest/bin:$ANDROID_SDK_ROOT/platform-tools:$ANDROID_SDK_ROOT/emulator:$PATH"
    
    # Remove potentially conflicting directories
    rm -rf $ANDROID_SDK_ROOT/emulator-2 $ANDROID_SDK_ROOT/platform-tools-2
    
    # Download and extract Android command-line tools
    echo "Downloading Android command-line tools..."
    curl -o cmdline-tools.zip https://dl.google.com/android/repository/commandlinetools-mac-9477386_latest.zip
    unzip -q cmdline-tools.zip -d $ANDROID_SDK_ROOT
    mv $ANDROID_SDK_ROOT/cmdline-tools $ANDROID_SDK_ROOT/latest
    mkdir -p $ANDROID_SDK_ROOT/cmdline-tools
    mv $ANDROID_SDK_ROOT/latest $ANDROID_SDK_ROOT/cmdline-tools/
    rm cmdline-tools.zip
    
    # Add Android SDK tools to PATH
    export PATH="$ANDROID_SDK_ROOT/cmdline-tools/latest/bin:$ANDROID_SDK_ROOT/platform-tools:$ANDROID_SDK_ROOT/emulator:$PATH"
    
    # Install Android SDK components
    echo "y" | sdkmanager --sdk_root=${ANDROID_SDK_ROOT} "platform-tools" "platforms;android-30" "build-tools;30.0.3" "emulator" "system-images;android-30;google_apis;x86_64"
    
    # Check for existing AVDs
    existing_avds=$(avdmanager list avd | grep "Name:" | cut -d ":" -f 2 | tr -d ' ')
    
    if [ -n "$existing_avds" ]; then
        echo -e "${Yellow}Existing Android Virtual Devices found:${NC}"
        echo "$existing_avds"
        echo -e "${Yellow}Choose an AVD to use:${NC}"
        select avd_name in $existing_avds; do
            if [ -n "$avd_name" ]; then
                echo "Using existing AVD: $avd_name"
                break
            else
                echo "Invalid selection. Please try again."
            fi
        done
    else
        echo "No existing AVDs found. Creating a new one named 'test_avd'."
        avd_name="test_avd"
        echo "no" | avdmanager create avd -n $avd_name -k "system-images;android-30;google_apis;x86_64"
    fi

    # Export the AVD name for later use
    export SELECTED_AVD_NAME=$avd_name
}

# Main script execution
echo -e "${Green}Setting up the environment...${NC}"

check_os
request_sudo
install_dependencies

install_python_dependencies
install_appium

# Ask user for platform choice
echo -e "${Yellow}Which platform would you like to set up? (android/ios)${NC}"
read platform_choice

if [[ "$platform_choice" == "ios" ]]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        install_ios_dependencies
    else
        echo "iOS development is only supported on macOS"
        exit 1
    fi
elif [[ "$platform_choice" == "android" ]]; then
    install_android_dependencies

    printf "${Yellow}Killing any running emulators...${NC}\n"
    adb devices | grep emulator | cut -f1 | while read line; do adb -s $line emu kill; done

    # Wait for emulators to fully shut down
    sleep 10

    printf "${Yellow}Starting Android emulator...${NC}\n"
    $ANDROID_SDK_ROOT/emulator/emulator -avd $SELECTED_AVD_NAME -no-snapshot -no-audio -no-boot-anim -read-only &

    printf "${Yellow}Waiting for Android emulator to start...${NC}\n"
    timeout=300  # 5 minutes
    start_time=$(date +%s)
    while true; do
        if adb shell getprop sys.boot_completed 2>/dev/null | grep -q '1'; then
            echo "Emulator is ready."
            break
        fi

        if adb shell getprop init.svc.bootanim 2>/dev/null | grep -q 'stopped'; then
            echo "Boot animation has stopped. Waiting for system to be fully ready..."
            sleep 10
            break
        fi

        current_time=$(date +%s)
        elapsed=$((current_time - start_time))
        if [ $elapsed -ge $timeout ]; then
            echo "Timeout waiting for emulator to start. Please check your AVD configuration."
            echo "You can try starting the emulator manually using Android Studio and then run this script again."
            exit 1
        fi

        if [ $((elapsed % 10)) -eq 0 ]; then
            echo "Still waiting for emulator to start... (${elapsed} seconds elapsed)"
        fi

        sleep 2
    done

    printf "${Yellow}Emulator started successfully. Proceeding with the rest of the setup...${NC}\n"

    # Additional wait to ensure system is fully ready
    printf "${Yellow}Waiting for system to be fully ready...${NC}\n"
    adb wait-for-device shell 'while [[ -z $(getprop sys.boot_completed) ]]; do sleep 1; done; input keyevent 82'

    printf "${Green}Android emulator is now fully ready.${NC}\n"
else
    echo "Invalid choice. Please run the script again and choose either 'android' or 'ios'."
    exit 1
fi

echo -e "${Yellow}Starting Appium server in a new terminal window...${NC}"
# Kill any existing Appium processes
pkill -f appium || true

# Create a temporary shell script
cat << EOF > /tmp/run_appium.sh
#!/bin/bash
export ANDROID_SDK_ROOT='$ANDROID_SDK_ROOT'
export ANDROID_HOME='$ANDROID_HOME'
export PATH='$PATH'
cd '$(pwd)'
appium --log appium.log
EOF

# Make the script executable
chmod +x /tmp/run_appium.sh

# Open a new terminal window and run the script
open -a Terminal /tmp/run_appium.sh

echo -e "${Yellow}Waiting for Appium server to start...${NC}"
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:4723/wd/hub/status > /dev/null; then
        echo -e "${Green}Appium server is up and running.${NC}"
        break
    fi
    attempt=$((attempt+1))
    echo -e "${Yellow}Waiting for Appium server (attempt $attempt/$max_attempts)...${NC}"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${Red}Failed to start Appium server. Please check the appium.log file for details.${NC}"
    exit 1
fi

# Clean up the temporary script
rm /tmp/run_appium.sh

echo -e "${Yellow}Running the Python script to interact with the device...${NC}"
if [[ "$platform_choice" == "android" ]]; then
    # Change to the parent directory of 'deploy'
    cd ..
    # Add the current directory to PYTHONPATH
    export PYTHONPATH=$PYTHONPATH:$(pwd)
    # Run the Python script with environment variables
    env ANDROID_SDK_ROOT="$ANDROID_SDK_ROOT" ANDROID_HOME="$ANDROID_HOME" PATH="$PATH" python3 -u testing/run_android.py
    # Change back to the 'deploy' directory
    cd deploy
else
    # Run the iOS script without suppressing output
    python3 -u scripts/run_ios_device.py
fi

echo -e "${Green}Setup and device interaction complete.${NC}"