# Termux Crypto Alert - GUI

A graphical user interface (GUI) Python script for Termux to manage cryptocurrency price alerts and receive notifications directly on your Android device. This script utilizes Termux dialogs for a user-friendly menu interface within your Termux environment.

## Features

*   **Graphical User Interface (GUI):**  Interactive menu-driven interface using Termux dialogs for easy navigation and alert management.
*   **Add Alerts:** Easily add new cryptocurrency price alerts with customizable conditions (above or below a threshold) and target prices in USD.
*   **Remove Alerts:** Delete existing alerts when they are no longer needed.
*   **List Alerts:** View all currently active alerts with their details.
*   **Start Monitoring:** Initiate price monitoring in the background to continuously check for alert conditions.
*   **Stop Monitoring:** Halt the background monitoring process.
*   **Custom Alert Sounds:** Option to select custom sound files for alerts from the script's directory. Default sound is also included.
*   **Termux Notifications:** Receive instant notifications when an alert condition is triggered.
*   **App Info:** Access application information and contact details within the script's menu.

## Requirements

1.  **Termux:** Android terminal emulator application.
    *   [Install Termux from F-Droid](https://f-droid.org/en/packages/com.termux/) or [Google Play Store](https://play.google.com/store/apps/details?id=com.termux)

2.  **Termux-API App:**  **Crucially, you need to install the Termux-API *app* (APK) in addition to the Termux-API package within Termux.**
    *   Download the Termux-API app APK from:
        *   [F-Droid](https://f-droid.org/en/packages/com.termux.api/) (Recommended)
        *   [GitHub Releases](https://github.com/termux/termux-api/releases)
    *   Install the downloaded APK on your Android device.
    *   After installation, grant necessary permissions to Termux-API app when prompted by Android (especially for notifications and storage if you plan to use custom sounds from shared storage).

3.  **Termux Packages:** Install the following packages within Termux:
    *   **Python:**
        ```bash
        pkg install python
        ```
    *   **Termux-API package:**
        ```bash
        pkg install termux-api
        ```
    *   **MPV (Recommended):** For playing alert sounds.
        ```bash
        pkg install mpv
        ```

4.  **Python Libraries:** Install required Python libraries using `pip`
    *   Ensure you have `pip` installed for Python in Termux

    **Install Python `requests` Library:
    ```bash
    pip install requests
    ```

### NOTE:
 **Sound Files : If you want to use custom alert sounds, place `.mp3`, `.wav`, `.flac`, or `.ogg` sound files             in the same directory as the script. Otherwise, you can enter the full path to a sound file located anywhere             on your device when prompted to select a sound.**

## _________________________________________________________________________________


## Installation

1.  **Clone the repository (or download the script):**
    If you are using Git in Termux:
    ```bash
    git clone https://github.com/simix/Termux-Crypto-Alert.git
    cd Termux-Crypto-Alert
    ```

3.  **Make the script executable:**
    ```bash
    chmod +x TermuxCryptoAlert.py
    ```

## Usage

1.  **Run the script:**
    ```bash
    python TermuxCryptoAlert.py
    ```
    This command will launch the **graphical user interface** menu using `termux-dialog`.
    
    ![Screenshot_20250130_233408](https://github.com/user-attachments/assets/a181dc21-e225-41c1-8203-f4560512abb3)


3.  **Navigate the Menu:** tap on the options within the Termux dialog to navigate the menu.

    *   **➕ Add Alert:**  Select to create a new alert. Follow the prompts in the dialogs to enter cryptocurrency name, price threshold, condition, and optionally select a custom sound.

    *   **🗑️ Remove Alert:**  Select to remove an existing alert. Choose the alert to remove from the list presented in the dialog.

    *   **📋 List Alerts:**  Select to display a dialog box listing all active alerts and their details.

    *   **🚀 Start Monitoring:** Select to start the background price monitoring. You will receive a toast notification indicating it has started.

    *   **⏹️ Stop Monitoring:** Select to stop the background price monitoring. You will receive a toast notification confirming it has stopped.

    *   **ℹ️ App Info:** Select to view application information and contact details in a dialog box.

    *   **❌ Exit:** Select to close the script and exit the menu.

## Background Monitoring Notes

*   When "🚀 Start Monitoring" is selected, the script initiates a background process to monitor prices.
*   Always use "⏹️ Stop Monitoring" from the menu to properly halt the background process. Closing the Termux session might not immediately stop it.
*   Be aware of Android and Termux background execution limitations, which might affect long-term reliability of background monitoring, especially on devices with aggressive battery optimization.

## Customization

*   **Alert Sounds:** Place custom sound files (`.mp3`, `.wav`, `.flac`, `.ogg`) in the same directory as `TermuxCryptoAlert.py`. The script will detect these and allow you to choose them when adding alerts.

## Contact

*   **Facebook:** [https://www.facebook.com/SRX003](https://www.facebook.com/SRX003)
*   **Telegram:** [@SRX03](https://t.me/SRX03)

## License

This script is open for personal use and modification. Feel free to use and adapt it as needed.

---

**Enjoy managing your crypto alerts with the Termux Crypto Alert Manager GUI!**
