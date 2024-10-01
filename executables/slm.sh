#!/bin/bash
cd "$(dirname "$0")" || return

# Set local variables
executable="slm"
dir_current=$(pwd)
dir_download="$dir_current/slm"
dir_download_temp="${dir_download}_temp"
dir_download_dist="$dir_download/dist"
dir_download_dist_executable="$dir_download_dist/$executable"
file_python="$dir_download/$executable.py"
file_spec="$dir_download/$executable.spec"
dir_existing="$dir_current/_internal"
dir_existing_upgrade="$dir_existing/program_files"
dir_download_upgrade="$dir_download/_internal"
link="https://www.dropbox.com/scl/fi/b5loo1yndyfasqgek1vv3/slm_python.zip?rlkey=g1wcyl22kewg05cu55nqssbt7&dl=1"
outfile="slm.zip"

continue_install="false"
continue_startup="false"
continue_port="false"

# Function to check if the OS is Synology
is_synology() {
    if [ -f /etc.defaults/VERSION ]; then
        return 0
    else
        return 1
    fi
}

# Check the system type (distribution) and install necessary prerequisites
if ! command -v unzip &> /dev/null; then
    echo "unzip is not installed. Installing..."
    if [[ -f /etc/os-release ]]; then
        source /etc/os-release
        case "$ID" in
            debian|ubuntu|linuxmint)
                # Debian/Ubuntu/Mint
                sudo apt-get install unzip
                ;;
            fedora|centos|rhel)
                # RedHat/CentOS/Fedora
                sudo dnf install unzip
                ;;
            arch|manjaro)
                # Arch/Manjaro
                sudo pacman -S unzip
                ;;
            opensuse)
                # OpenSUSE
                sudo zypper install unzip
                ;;
            *)
                if is_synology; then
                    # Synology
                    sudo synopkg install unzip
                else
                    echo "Unknown system type or unsupported distribution."
                fi
                ;;
        esac
    else
        echo "Unable to determine system type."
    fi
fi

if ! command -v pip &> /dev/null; then
    echo "pip is not installed. Installing..."
    if [[ -f /etc/os-release ]]; then
        source /etc/os-release
        case "$ID" in
            debian|ubuntu|linuxmint)
                # Debian/Ubuntu/Mint
                sudo apt-get install python3-pip
                ;;
            fedora|centos|rhel)
                # RedHat/CentOS/Fedora
                sudo dnf install python3-pip
                ;;
            arch|manjaro)
                # Arch/Manjaro
                sudo pacman -S python-pip
                ;;
            opensuse)
                # OpenSUSE
                sudo zypper install python3-pip
                ;;
            *)
                if is_synology; then
                    # Synology
                    sudo synopkg install python3-pip
                else
                    echo "Unknown system type or unsupported distribution."
                fi
                ;;
        esac
    else
        echo "Unable to determine system type."
    fi
fi

# Check if pip3 is available
if command -v pip3 &> /dev/null
then
    PIP_CMD="pip3"
# Check if pip is available
elif command -v pip &> /dev/null
then
    PIP_CMD="pip"
else
    echo "Neither pip nor pip3 is installed."
    exit 1
fi

# Run the executable
if [ $# -eq 0 ]; then
    if [ -e "$executable" ]; then
        # Run Executable in background and disown it
        nohup "./$executable" > /dev/null 2>&1 &
        disown
    else
        # Display error message and pause
        echo "Stream Link Manager not installed. Please install using './slm.sh install'."
        read -n 1 -s -r -p "Press any key to continue..."
    fi
fi

# Handle additional commands
if [ -n "$1" ]; then
    case "$1" in
        install)
            echo "WARNING: Installing will overwrite any existing installation and user files."
            while true; do
                read -p "Do you wish to continue? (Y/N): " choice
                if [ "$choice" == "Y" ] || [ "$choice" == "y" ]; then
                    echo "Beginning installation..."
                    continue_install="true"
                    break
                elif [ "$choice" == "N" ] || [ "$choice" == "n" ]; then
                    echo "Installation canceled."
                    break
                else
                    echo "Invalid input. Please try again."
                fi
            done
            ;;
        upgrade)
            echo "Beginning upgrade..."
            continue_install="true"
            ;;
        startup)
            echo "Beginning startup routine..."
            continue_startup="true"
            ;;
        port)
            echo "Beginning port routine..."
            continue_port="true"
            ;;
        *)
            echo "Invalid command. Usage: 'slm [install | upgrade | startup | port]'"
            exit 1
            ;;
    esac
fi

# Installation and Upgrade
if [ $continue_install = "true" ]; then
    # Check if the process is running
    pid=$(pgrep -f "^./$executable$")

    if [ -n "$pid" ]; then
        echo "Process $executable is running with PID $pid. Killing it now..."
        kill -9 $pid
        echo "Process $executable has been killed."
    else
        echo "Process $executable is not running."
    fi

    # Download and extract files
    echo "Downloading Stream Link Manager files..."
    wget -q -O "$outfile" "$link"
    sleep 5

    echo "Extracting Stream Link Manager files..."
    if [ -f "$executable" ]; then
        rm -f "$executable"
    fi
    unzip -q "$outfile" -d "${outfile%.zip}"
    sleep 5

    echo "Building Stream Link Manager executable..."
    cd "$dir_download" || return
    $PIP_CMD install -r requirements.txt
    pyinstaller --noconfirm --onedir --console --add-data "requirements.txt:." --add-data "static:static/" --add-data "templates:templates/"  "$file_python"
    rm -f "requirements.txt"
    rm -rf static
    rm -rf templates
    rm -f "$file_python"
    rm -f "$file_spec"
    rm -rf build
    cp -r "$dir_download_dist_executable"/* "$dir_download"
    [ -d "$dir_download_dist" ] && rm -rf "$dir_download_dist"
    cd "$dir_current" || return
    sleep 5

    if [ "$1" == "upgrade" ] && [ -d "$dir_existing_upgrade" ]; then
        echo "Moving user program files..."
        mv -f "$dir_existing_upgrade" "$dir_download_upgrade"
        sleep 5
    fi

    # Clean up files
    echo "Cleaning up files..."
    rm -f "$outfile"
#    [ -f "$executable" ] && rm -f "$executable"
    [ -d "$dir_existing" ] && rm -rf "$dir_existing"
    sleep 5

    # Move files to final destination
    echo "Moving files to final destination..."
    mv "$dir_download" "$dir_download_temp"
    cp -r "$dir_download_temp"/* "$dir_current"
    [ -d "$dir_download_temp" ] && rm -rf "$dir_download_temp"
    chmod +x "$executable"
    sleep 5

    if [ "$1" == "upgrade" ]; then
        echo "Upgrade completed!"
        sleep 5
    else
        echo "Installation completed!"
    fi
fi

# Startup commands
if [ "$continue_startup" = "true" ]; then
    script_path=$(realpath "$0")
    startup_script_name="${executable}_startup.sh"

    echo "Setting up $startup_script_name to run at startup..."

    # Create the startup script in the current directory
    echo "#!/bin/bash" > "$startup_script_name"
    echo "$script_path" >> "$startup_script_name"
    chmod +x "$startup_script_name"

    # Determine the OS and move the script to the appropriate startup folder
    if [[ -f /etc/os-release ]]; then
        source /etc/os-release
        case "$ID" in
            debian|ubuntu|linuxmint)
                # Debian/Ubuntu/Mint
                sudo mv "$startup_script_name" /etc/init.d/
                sudo update-rc.d "$startup_script_name" defaults
                ;;
            fedora|centos|rhel|arch|manjaro|opensuse)
                # RedHat/CentOS/Fedora/Arch/Manjaro/OpenSUSE
                sudo mv "$startup_script_name" /etc/systemd/system/
                sudo systemctl enable "$startup_script_name"
                ;;
            *)
                if is_synology; then
                    # Synology
                    sudo mv "$startup_script_name" /usr/local/etc/rc.d/
                else
                    echo "Unknown system type or unsupported distribution."
                fi
                ;;
        esac
    else
        echo "Unable to determine system type."
    fi

    echo "Finished setting up startup commands."
fi

# Port commands
if [ $continue_port = "true" ]; then
    while true; do
        read -p "Enter a port number (1000-9999) or press Enter to use the default (5000): " port
        if [ -z "$port" ]; then
            port=5000
            break
        elif [[ "$port" =~ ^[0-9]+$ ]] && [ "$port" -ge 1000 ] && [ "$port" -le 9999 ]; then
            break
        else
            echo "Invalid input. Please enter a number between 1000 and 9999."
        fi
    done
    export SLM_PORT=$port
    echo "SLM_PORT set to $port"
    sudo ufw allow $port
    echo "Port $port opened in the firewall."

    # Append the environment variable to .bashrc
    echo "export SLM_PORT=$port" >> ~/.bashrc
    echo "SLM_PORT=$port has been added to .bashrc"

    # Reminder to source .bashrc manually
    echo "Please run 'source ~/.bashrc' to apply the changes to your current shell session."
fi

#Finish and Exit
echo ""
exit 0