import json
import os
import subprocess
import requests
import time
import threading
import sys
import signal
from typing import Optional, Dict, List

class TermuxCryptoGUI:
    def __init__(self):
        self.config_file = os.path.expanduser("~/.crypto_alerts.json")
        self.alerts = self.load_alerts()
        self.pid_file = "crypto_monitor.pid"

    def load_alerts(self) -> List[Dict]:
        """Load saved alerts from config file."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return []
        return []

    def save_alerts(self):
        """Save alerts to config file."""
        with open(self.config_file, 'w') as f:
            json.dump(self.alerts, f, indent=4)

    def show_menu(self) -> str:
        """Show main menu using termux-dialog radio."""
        try:
            menu_options = ["➕ Add Alert", "🗑️ Remove Alert", "📋 List Alerts", "🚀 Start Monitoring", "⏹️ Stop Monitoring", "ℹ️ App Info", "❌ Exit"]
            result = subprocess.run([
                "termux-dialog", "radio",
                "-t", "Termux-Crypto-Alert",  # Changed title here
                "-v", ",".join(menu_options)
            ], capture_output=True, text=True)

            if result.returncode == 0:
                output_json = json.loads(result.stdout)
                if output_json and "index" in output_json:
                    selected_index = int(output_json["index"])
                    return menu_options[selected_index] if 0 <= selected_index < len(menu_options) else "❌ Exit"
                else:
                    return "❌ Exit"
            else:
                print(f"Error running termux-dialog radio, return code: {result.returncode}")
                print(f"Stderr: {result.stderr.decode()}")
                return "❌ Exit"

        except FileNotFoundError:
            print("Error: termux-dialog command not found. Is termux-api installed?")
            return "❌ Exit"
        except json.JSONDecodeError as e:
            print(f"Error parsing dialog output (JSONDecodeError): {e}")
            print(f"Raw termux-dialog stdout: {result.stdout}")
            return "❌ Exit"
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return "❌ Exit"

    def get_input(self, title: str, hint: str = "") -> str:
        """Get user input using termux-dialog."""
        try:
            result = subprocess.run([
                "termux-dialog", "text",
                "-t", title,
                "-i", hint
            ], capture_output=True, text=True)
            return json.loads(result.stdout)["text"]
        except Exception as e:
            print(f"Error getting input: {e}")
            return ""

    def show_confirmation(self, title: str) -> bool:
        """Show confirmation dialog."""
        try:
            result = subprocess.run([
                "termux-dialog", "confirm",
                "-t", title
            ], capture_output=True, text=True)
            return json.loads(result.stdout)["text"] == "yes"
        except Exception as e:
            print(f"Error showing confirmation: {e}")
            return False

    def get_crypto_price(self, symbol: str) -> Optional[float]:
        """Fetch current price for a cryptocurrency."""
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            return data[symbol]["usd"]
        except Exception as e:
            self.show_toast(f"Error fetching price for {symbol}: {e}")
            return None

    def show_toast(self, message: str):
        """Show toast notification."""
        subprocess.run(["termux-toast", "-g", "middle", message])

    def play_sound(self, sound_file: Optional[str] = None):
        """Play alert sound. Now with sound file selection from script directory."""
        try:
            if sound_file and os.path.exists(sound_file):
                subprocess.run(["mpv", sound_file], check=True)
            else:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                sound_files = [f for f in os.listdir(script_dir) if f.lower().endswith(('.mp3', '.wav', '.flac', '.ogg'))]

                if not sound_files:
                    self.show_toast("No sound files found in script directory. Using default alert.")
                    subprocess.run(["mpv", "/data/data/com.termux/files/home/Termux-Crypto-Alert/alertcoin.mp3"], check=True) # Fallback to default
                    return

                result = subprocess.run([
                    "termux-dialog", "sheet",
                    "-t", "Select Alert Sound",
                    "-v", ",".join(sound_files)
                ], capture_output=True, text=True)

                if result.returncode == 0:
                    output_json = json.loads(result.stdout)
                    if output_json and "text" in output_json:
                        selected_sound_file = output_json["text"]
                        sound_path = os.path.join(script_dir, selected_sound_file)
                        if os.path.exists(sound_path):
                            subprocess.run(["mpv", sound_path], check=True)
                        else:
                            self.show_toast(f"Error: Selected sound file not found: {sound_path}")
                    else:
                        self.show_toast("No sound file selected. Using default alert.")
                        subprocess.run(["mpv", "/data/data/com.termux/files/home/Termux-Crypto-Alert/alertcoin.mp3"], check=True) # Fallback to default
                else:
                    self.show_toast(f"Error running termux-dialog sheet: {result.stderr.decode()}")

        except Exception as e:
            self.show_toast(f"Error playing sound: {e}")

    def send_notification(self, message: str):
        """Send Termux notification."""
        try:
            subprocess.run([
                "termux-notification",
                "--title", "Crypto Alert",
                "--content", message,
                "--priority", "high"
            ], check=True)
        except Exception as e:
            self.show_toast(f"Error sending notification: {e}")

    def add_alert(self):
        """Add new alert through GUI."""
        coin = self.get_input("Enter cryptocurrency name (e.g., bitcoin):")
        if not coin:
            return

        price_str = self.get_input("Enter price threshold (USD):")
        try:
            price = float(price_str)
        except ValueError:
            self.show_toast("Invalid price value")
            return

        condition_result = subprocess.run([
            "termux-dialog", "sheet",
            "-v", "⬆️ above, ⬇️ below"
        ], capture_output=True, text=True)
        condition = json.loads(condition_result.stdout)["text"].split(" ")[1]

        use_sound = self.show_confirmation("🔔 Do you want to set a custom alert sound from script folder?")
        sound_file = None
        if use_sound:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            sound_files = [f for f in os.listdir(script_dir) if f.lower().endswith(('.mp3', '.wav', '.flac', '.ogg'))]

            if not sound_files:
                self.show_toast("No sound files found in script directory.")
            else:
                result = subprocess.run([
                    "termux-dialog", "sheet",
                    "-t", "Select Alert Sound from Folder",
                    "-v", ",".join(sound_files)
                ], capture_output=True, text=True)

                if result.returncode == 0:
                    output_json = json.loads(result.stdout)
                    if output_json and "text" in output_json:
                        selected_sound_file_name = output_json["text"]
                        sound_file = os.path.join(script_dir, selected_sound_file_name)
                    else:
                        self.show_toast("No sound file selected, using default.")

        alert = {
            "name": coin.capitalize(),
            "symbol": coin.lower(),
            "condition": condition,
            "price": price
        }
        if sound_file:
            alert["sound_file"] = sound_file

        self.alerts.append(alert)
        self.save_alerts()
        self.show_toast(f"✅ Added alert for {coin} {condition} {price} USD")

    def list_alerts(self):
        """List alerts through GUI."""
        if not self.alerts:
            self.show_toast("No active alerts")
            return

        alert_text = "Active Alerts:\n\n"
        for i, alert in enumerate(self.alerts, 1):
            alert_text += f"{i}. {alert['name']}: {alert['condition']} {alert['price']} USD"
            if 'sound_file' in alert:
                alert_text += f" - Sound: {os.path.basename(alert['sound_file'])}" # Show sound file name
            alert_text += "\n"

        subprocess.run([
            "termux-dialog", "text",
            "-t", "📋 Active Alerts",
            "-i", alert_text
        ])

    def remove_alert(self):
        """Remove alert through GUI."""
        if not self.alerts:
            self.show_toast("No alerts to remove")
            return

        choices = ",".join(f"{i}. {alert['name']}" for i, alert in enumerate(self.alerts, 1))
        result = subprocess.run([
            "termux-dialog", "sheet",
            "-v", choices
        ], capture_output=True, text=True)

        try:
            selected = int(json.loads(result.stdout)["text"].split(".")[0]) - 1
            removed = self.alerts.pop(selected)
            self.save_alerts()
            self.show_toast(f"🗑️ Removed alert for {removed['name']}")
        except (ValueError, IndexError):
            self.show_toast("❌ Invalid selection")

    def monitor_alerts(self):
        """Monitor cryptocurrency prices and trigger alerts."""
        self.show_toast("🚀 Starting price monitoring in background...")
        print(f"DEBUG: Monitoring process started.")

        try:
            while True:
                for alert in self.alerts:
                    price = self.get_crypto_price(alert["symbol"])
                    if price is None:
                        continue

                    if (alert["condition"] == "above" and price > alert["price"]) or \
                       (alert["condition"] == "below" and price < alert["price"]):
                        message = f"🚨 ALERT! {alert['name']} price is {alert['condition']} {alert['price']} USD"
                        self.send_notification(message)
                        threading.Thread(target=self.play_sound, args=(alert.get('sound_file'),)).start()

                time.sleep(30)
        except KeyboardInterrupt:
            self.show_toast("🛑 Stopping price monitoring...")
            print(f"DEBUG: Monitoring process stopped by KeyboardInterrupt.")
        finally:
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
                print(f"DEBUG: PID file '{self.pid_file}' removed.")
            else:
                print(f"DEBUG: PID file '{self.pid_file}' not found during cleanup.")


    def start_monitoring_background(self):
        """Starts monitoring in background and saves PID."""
        script_path = os.path.abspath(__file__)
        command = f"python {script_path} monitor"
        try:
            process = subprocess.Popen(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=os.setsid)
            pid = process.pid
            with open(self.pid_file, "w") as f:
                f.write(str(pid))
            self.show_toast("🚀 Monitoring started in background")
            print(f"DEBUG: Background monitoring started with PID: {pid}. PID saved to '{self.pid_file}'.")
        except Exception as e:
            self.show_toast(f"Error starting monitoring: {e}")
            print(f"DEBUG: Error starting background monitoring: {e}")


    def stop_monitoring(self):
        """Stops the background monitoring process if it's running."""
        if os.path.exists(self.pid_file):
            with open(self.pid_file, "r") as f:
                pid_str = f.read().strip()
                try:
                    pid = int(pid_str)
                    print(f"DEBUG: Attempting to stop monitoring process with PID: {pid} (read from '{self.pid_file}').")
                    try:
                        os.killpg(pid, 0)
                        os.killpg(pid, signal.SIGTERM)
                        os.remove(self.pid_file)
                        self.show_toast("⏹️ Monitoring stopped.")
                        print(f"DEBUG: Monitoring process with PID: {pid} stopped successfully. PID file removed.")
                    except ProcessLookupError:
                        os.remove(self.pid_file)
                        self.show_toast("Warning: Monitoring process not found (PID from file). PID file removed.")
                        print(f"DEBUG: ProcessLookupError: Monitoring process with PID: {pid} not found. PID file removed.")
                    except PermissionError:
                        self.show_toast("Error: Permission denied to stop monitoring process.")
                        print(f"DEBUG: PermissionError: Permission denied to stop monitoring process with PID: {pid}.")
                    except Exception as e:
                        self.show_toast(f"Error stopping monitoring process: {e}")
                        print(f"DEBUG: Error stopping monitoring process with PID: {pid}: {e}")

                except ValueError:
                    self.show_toast("Error: Invalid PID in file. PID file removed.")
                    os.remove(self.pid_file)
                    print(f"DEBUG: ValueError: Invalid PID in file '{self.pid_file}'. PID file removed.")
                except FileNotFoundError:
                    self.show_toast("Warning: PID file not found (already removed?). Monitoring might not be running.")
                    print(f"DEBUG: FileNotFoundError: PID file '{self.pid_file}' not found.")
                except Exception as e:
                    self.show_toast(f"Error reading PID file: {e}")
                    print(f"DEBUG: Error reading PID file '{self.pid_file}': {e}")

        else:
            self.show_toast("Monitoring is not running.")
            print(f"DEBUG: Monitoring is not running (PID file '{self.pid_file}' not found).")

    def show_app_info(self):
        """Show application info and contact details."""
        app_info_text = """
Termux-Crypto-Alert

App for managing crypto
price alerts in Termux

Facebook: @SRX003
Telegram: @SRX03
"""
        subprocess.run([
            "termux-dialog", "text",
            "-t", "ℹ️ App Info",
            "-i", app_info_text.strip() # Use strip to remove leading/trailing whitespace for cleaner look
        ])


def main():
    app = TermuxCryptoGUI()

    while True:
        choice = app.show_menu()

        if choice == "➕ Add Alert":
            app.add_alert()
        elif choice == "📋 List Alerts":
            app.list_alerts()
        elif choice == "🗑️ Remove Alert":
            app.remove_alert()
        elif choice == "🚀 Start Monitoring":
            if not os.path.exists(app.pid_file):
                app.start_monitoring_background()
            else:
                app.show_toast("Monitoring is already running. Stop it first to restart.")
        elif choice == "⏹️ Stop Monitoring":
            app.stop_monitoring()
        elif choice == "ℹ️ App Info": # Added this condition
            app.show_app_info()      # Call the new function
        elif choice == "❌ Exit":
            break

    app.show_toast("👋 Goodbye!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "monitor":
        app = TermuxCryptoGUI()
        app.monitor_alerts()
    else:
        main()
