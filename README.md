# Termux Crypto Alert - GUI

A graphical user interface (GUI) Python script for Termux to manage cryptocurrency price alerts and receive notifications directly on your Android device. This script utilizes Termux dialogs for a user-friendly menu interface within your Termux environment, **using the KuCoin API for price data.**

## Features

*   **Graphical User Interface (GUI):**  Interactive menu-driven interface using Termux dialogs for easy navigation and alert management.
*   **Add Alerts:** Easily add new cryptocurrency price alerts with customizable conditions (above or below a threshold) and target prices in your chosen quote currency (e.g., USDT).
*   **Remove Alerts:** Delete existing alerts when they are no longer needed.
*   **List Alerts:** View all currently active alerts with their details and real-time status.
*   **Restart Monitoring:**  Initiate or restart price monitoring in the background to continuously check for alert conditions.
*   **Stop Monitoring:** Halt the background monitoring process.
*   **Custom Alert Sounds:** Option to select custom sound files for alerts from the script's directory. Default sound is also included.
*   **Termux Notifications:** Receive instant notifications when an alert condition is triggered.
*   **Price History:** View and share price history charts for your alerts, helping you analyze price movements.
*   **Backtest Alert:** Simulate alert triggers over historical data to evaluate alert effectiveness.
*   **Settings:** Customize script settings such as check interval and price history duration.
*   **Export/Import Alerts:** Save your alerts to a JSON file for backup or sharing, and import them back when needed.
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
    *   **Matplotlib (Optional):** For price history charts. Install if you want to use the "Price History" feature.
        ```bash
        pip install matplotlib
        ```

4.  **Python Libraries:** Install required Python libraries using `pip`
    *   Ensure you have `pip` installed for Python in Termux

    **Install Python `requests` Library:
    ```bash
    pip install requests
    ```

### NOTE:
 **Sound Files : If you want to use custom alert sounds, place `.mp3`, `.wav`, `.flac`, or `.ogg` sound files in the same directory as the script.**

## Finding the Trading Pair Symbol (KuCoin)

To add an alert, you need the **KuCoin trading pair symbol** (e.g., BTC-USDT). This symbol is used to fetch price data from KuCoin.

1.  **Go to KuCoin:** Open the KuCoin website or app.
2.  **Search for Pair:** Search for the cryptocurrency pair you want (e.g., "BTCUSDT").
3.  **Find Symbol:** The trading pair symbol (e.g., `BTC-USDT`) is on the trading page.
4.  **Use in Script:** Enter this symbol when adding an alert in the script.

**Important Notes:**

*   Use **uppercase** symbols with a hyphen (e.g., `BTC-USDT`).
*   Ensure it's the **correct trading pair** from KuCoin.
*   Common quote currencies are USDT, BTC, and ETH.

## _________________________________________________________________________________


## Installation

1.  **Clone the repository (or download the script):**
    ```bash
    git clone https://github.com/simix/Termux-Crypto-Alert.git
    cd Termux-Crypto-Alert
    ```

2.  **Make the script executable:**
    ```bash
    chmod +x TermuxCryptoAlert.py
    ```

## Usage

1.  **Run the script:**
    ```bash
    python TermuxCryptoAlert.py
    ```
    This launches the menu.

    ![Screenshot_20250203_101850](https://github.com/user-attachments/assets/e2ab3b75-dad0-4b29-adfb-f279eded21bb)



2.  **Navigate the Menu:** Tap options in the dialog:

    *   **➕ Add Alert:** Create a new alert. Enter the KuCoin trading pair (e.g., BTC-USDT), price, condition, and optional sound.
    *   **🗑️ Remove Alert:** Delete an alert.
    *   **📋 List Alerts:** View all alerts and their status.
    *   **🔄 Restart Monitoring:** Start/restart background monitoring.
    *   **⏹️ Stop Monitoring:** Stop background monitoring.
    *   **📈 Price History:** View and share price chart for an alert.
    *   **📊 Backtest Alert:** Simulate past triggers for an alert.
    *   **⚙️ Settings:** Configure check interval and history days.
    *   **📤 Export Alerts:** Export alerts to a JSON file.
    *   **📥 Import Alerts:** Import alerts from a JSON file.
    *   **ℹ️ App Info:** Show app information.
    *   **❌ Exit:** Close the script.

## Background Monitoring Notes

*   "🔄 Restart Monitoring" starts background; use after adding alerts.
*   Use "⏹️ Stop Monitoring" to halt it properly.

## Customization

*   **Alert Sounds:** Place sound files (`.mp3`, `.wav`, `.flac`, `.ogg`) in the script's directory.
*   **Settings:** Use "⚙️ Settings" to adjust `check_interval` and `max_history_days`.

## Contact

*   **Facebook:** [https://www.facebook.com/SRX003](https://www.facebook.com/SRX003)
*   **Telegram:** [@SRX03](https://t.me/SRX03)

## License

Personal use and modification are allowed.

---

**Enjoy Termux Crypto Alert GUI!**
