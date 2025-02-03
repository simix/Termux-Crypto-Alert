import json
import os
import subprocess
import requests
import time
import threading
import sys
import signal
from typing import Optional, Dict, List
import matplotlib.pyplot as plt  # Make sure to install matplotlib: pip install matplotlib

class TermuxCryptoGUI:
    def __init__(self):
        self.config_file = os.path.expanduser("~/.crypto_alerts.json")
        self.alerts = self.load_alerts()
        self.triggered_alerts = [] # Holds alerts triggered in the current check interval
        self.currently_alerting = set() # Track alerts currently in alerting state to repeat notifications
        self.settings = {
            "check_interval": 30,
            "max_history_days": 7
        }
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
        """Expanded main menu"""
        menu_options = [
            "➕ Add Alert", "🗑️ Remove Alert", "📋 List Alerts",
            "📈 Price History", "📊 Backtest Alert", "⚙️ Settings",
            "📤 Export Alerts", "📥 Import Alerts", "🔄 Restart Monitoring",
            "⏹️ Stop Monitoring", "ℹ️ App Info", "❌ Exit"
        ]
        return self.handle_menu_selection(menu_options)

    def handle_menu_selection(self, menu_options: List[str]) -> str:
        """Show main menu using termux-dialog radio and handle selection."""
        try:
            result = subprocess.run([
                "termux-dialog", "radio",
                "-t", "Termux-Crypto-Alert",
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
        """Fetch current price for a cryptocurrency trading pair from KuCoin."""
        url = f"https://api.kucoin.com/api/v1/market/orderbook/level1?symbol={symbol}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            # Check API response code
            if data.get('code') != '200000':
                self.show_toast(f"KuCoin API error: {data.get('msg')}")
                return None

            price_str = data['data']['price']
            return float(price_str)
        except requests.exceptions.HTTPError as e:
            self.show_toast(f"HTTP error fetching price for {symbol}: {e}")
            return None
        except KeyError as e:
            self.show_toast(f"Invalid response format for {symbol}: {e}")
            return None
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
                    subprocess.run(["mpv", "/data/data/com.termux/files/home/Termux-Crypto-Alert/alertcoin.mp3"], check=True)  # Fallback to default
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
                        subprocess.run(["mpv", "/data/data/com.termux/files/home/Termux-Crypto-Alert/alertcoin.mp3"], check=True)  # Fallback to default
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
        coin = self.get_input("Enter trading pair (e.g., BTC-USDT):").strip()
        if not coin:
            return

        # Validate trading pair format
        symbol_parts = coin.upper().split('-')
        if len(symbol_parts) != 2:
            self.show_toast("Invalid format. Use SYMBOL-QUOTE like BTC-USDT")
            return
        base, quote = symbol_parts

        price_str = self.get_input(f"Enter price threshold (in {quote}):")
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
            "name": f"{base}/{quote}",
            "symbol": f"{base}-{quote}",
            "condition": condition,
            "price": price,
            "quote": quote
        }
        if sound_file:
            alert["sound_file"] = sound_file

        self.alerts.append(alert)
        self.save_alerts()
        self.show_toast(f"✅ Added alert for {base}-{quote} {condition} {price} {quote}")

    def list_alerts(self):
        """Interactive alert list with real-time data"""
        if not self.alerts:
            self.show_toast("No active alerts")
            return

        alert_options = []
        for i, alert in enumerate(self.alerts, 1):
            status = self.get_alert_status(alert)
            alert_options.append(
                f"{status} {i}. {alert['name']} "
                f"{alert['condition']} {alert['price']} {alert.get('quote', '?')}"
            )

        choice = self.show_sheet_dialog("📋 Active Alerts", alert_options)
        if choice:
            self.handle_alert_action(choice)  # handle_alert_action needs to be implemented

    def remove_alert(self):
        """Remove alert through GUI."""
        if not self.alerts:
            self.show_toast("No alerts to remove")
            return

        choices = [f"{i+1}. {alert['name']}" for i, alert in enumerate(self.alerts)]
        result = subprocess.run([
            "termux-dialog", "sheet",
            "-t", "Select Alert to Remove",
            "-v", ",".join(choices)
        ], capture_output=True, text=True)

        try:
            selected = int(json.loads(result.stdout)["text"].split(".")[0]) - 1
            removed = self.alerts.pop(selected)
            self.save_alerts()
            self.show_toast(f"🗑️ Removed alert for {removed['name']}")
        except (ValueError, IndexError):
            self.show_toast("❌ Invalid selection")

    def get_alert_status(self, alert):
        """Return emoji status with current price"""
        price = self.get_crypto_price(alert["symbol"])
        if not price:
            return "❔"

        if alert["condition"] == "above":
            return "�" if price > alert["price"] else "🔴"
        return "�" if price < alert["price"] else "🔴"

    def show_sheet_dialog(self, title: str, options: List[str]) -> Optional[str]:
        """Show sheet dialog and return selected option."""
        if not options:
            return None
        try:
            result = subprocess.run([
                "termux-dialog", "sheet",
                "-t", title,
                "-v", ",".join(options)
            ], capture_output=True, text=True)
            if result.returncode == 0:
                output_json = json.loads(result.stdout)
                if output_json and "text" in output_json:
                    return output_json["text"]
            return None
        except Exception as e:
            print(f"Error showing sheet dialog: {e}")
            return None

    def handle_alert_action(self, choice: str):
        """Handle action selected from alert list (to be implemented)"""
        alert_index = int(choice.split(".")[0].split()[-1]) - 1  # Extract alert index
        if 0 <= alert_index < len(self.alerts):
            selected_alert = self.alerts[alert_index]
            action_options = ["View History", "Backtest", "Remove", "Cancel"] # Snooze removed
            action_choice = self.show_sheet_dialog(f"Alert {alert_index + 1} Options", action_options)
            if action_choice == "Remove":
                self.remove_single_alert_by_index(alert_index)
            elif action_choice == "View History":
                self.show_price_history_for_alert(selected_alert)
            elif action_choice == "Backtest":
                self.backtest_alert_for_alert(selected_alert)
            # "Cancel" does nothing, just returns to menu

    def remove_single_alert_by_index(self, index: int):
        """Remove a single alert by its index."""
        if 0 <= index < len(self.alerts):
            removed_alert = self.alerts.pop(index)
            self.save_alerts()
            self.show_toast(f"🗑️ Removed alert for {removed_alert['name']}")
        else:
            self.show_toast("Invalid alert index for removal.")


    def show_price_history_for_alert(self, alert):
        """Display price chart for a specific alert."""
        days = self.settings["max_history_days"]
        url = (f"https://api.kucoin.com/api/v1/market/candles?"
               f"symbol={alert['symbol']}&type=1day&startAt={int(time.time()) - (days * 86400)}")
        try:
            data = requests.get(url).json()["data"]
            prices = [float(candle[2]) for candle in data]  # Closing prices
            plt.figure(figsize=(8, 4))
            plt.plot(prices)
            plt.title(f"{alert['name']} {days}-Day History")
            plt.xlabel("Days Ago")
            plt.ylabel("Price")
            plt.savefig("price_history.png")
            subprocess.run(["termux-share", "price_history.png"])
            self.show_toast("📈 Price history chart shared.")
        except Exception as e:
            self.show_toast(f"Chart error: {str(e)}")

    def backtest_alert_for_alert(self, alert):
        """Simulate alert performance over historical data for a specific alert."""
        days = self.settings["max_history_days"]  # Use default backtest days from settings
        url = (f"https://api.kucoin.com/api/v1/market/candles?"
               f"symbol={alert['symbol']}&type=1hour&startAt={int(time.time()) - (days * 86400)}")
        triggers = 0
        try:
            data = requests.get(url).json()["data"]
            for candle in data:
                price = float(candle[2])
                if (alert["condition"] == "above" and price > alert["price"]) or \
                   (alert["condition"] == "below" and price < alert["price"]):
                    triggers += 1

            self.show_alert_result(
                f"Backtest Results\n{alert['name']}\n"
                f"Triggers: {triggers}\nPeriod: {days} days"
            )
        except Exception as e:
            self.show_toast(f"Backtest failed: {str(e)}")

    def show_alert_result(self, message: str):
        """Display alert result in a dialog."""
        subprocess.run([
            "termux-dialog", "text",
            "-t", "Alert Result",
            "-i", message
        ])

    def show_settings(self):
        """Interactive settings configuration"""
        settings_options = [
            f"🔄 Check Interval ({self.settings['check_interval']}s)",
            f"📅 Max History Days ({self.settings['max_history_days']})",
            "🔙 Back"
        ]

        while True:
            choice = self.show_sheet_dialog("⚙️ Settings", settings_options)
            if not choice:  # User cancelled or closed dialog
                break
            if "Check Interval" in choice:
                self.update_setting("check_interval", "Enter check interval (seconds):", int)
            elif "History Days" in choice:
                self.update_setting("max_history_days", "Enter max history days:", int)
            else:
                break  # "Back" or invalid choice

    def update_setting(self, setting_key: str, prompt: str, type_変換):
        """Update a setting value."""
        current_value = self.settings[setting_key]
        user_input = self.get_input(prompt, str(current_value))
        if user_input:
            try:
                new_value = type_変換(user_input)
                if new_value > 0:  # Basic validation, adjust as needed
                    self.settings[setting_key] = new_value
                    self.show_toast(f"⚙️ {setting_key.replace('_', ' ').title()} updated to {new_value}")
                else:
                    self.show_toast("Value must be positive.")
            except ValueError:
                self.show_toast("Invalid input. Please enter a number.")

    def export_alerts(self):
        """Export alerts to a file."""
        default_export_file = "crypto_alerts_export.json"
        file_name = self.get_input("Enter export file name:", default_export_file)
        if not file_name:
            return

        if not file_name.endswith(".json"):
            file_name += ".json"

        try:
            with open(file_name, 'w') as f:
                json.dump(self.alerts, f, indent=4)
            self.show_toast(f"📤 Alerts exported to {file_name}")
            subprocess.run(["termux-share", file_name])  # Optionally share the file
        except Exception as e:
            self.show_toast(f"Export failed: {str(e)}")

    def import_alerts(self):
        """Import alerts from a file."""
        default_import_file = "crypto_alerts_export.json"  # Suggest default export name for import
        file_name = self.get_input("Enter import file name:", default_import_file)
        if not file_name:
            return

        if not os.path.exists(file_name):
            self.show_toast("File not found.")
            return

        try:
            with open(file_name, 'r') as f:
                imported_alerts = json.load(f)
                if isinstance(imported_alerts, list):  # Validate if it's a list of alerts
                    self.alerts = imported_alerts  # Replace current alerts with imported ones
                    self.save_alerts()  # Save immediately
                    self.show_toast(f"📥 Alerts imported from {file_name}")
                else:
                    self.show_toast("Invalid alert file format.")
        except json.JSONDecodeError:
            self.show_toast("Invalid JSON file.")
        except Exception as e:
            self.show_toast(f"Import failed: {str(e)}")

    def check_alert_condition(self, alert, price):
        """Check if alert condition is met."""
        if alert["condition"] == "above":
            return price > alert["price"]
        return price < alert["price"]

    def handle_triggered_alert(self, alert, price):
        """Handle alert trigger with repeat capability."""
        alert_name = alert['name']
        quote = alert.get('quote', '')
        message = f"🚨 ALERT! {alert_name} price is {alert['condition']} {alert['price']} {quote} (Current: {price:.2f})"

        # Send notification and play sound every time the condition is met
        self.send_notification(message)
        threading.Thread(target=self.play_sound, args=(alert.get('sound_file'),)).start()


    def monitor_alerts(self):
        """Enhanced monitoring with repeated notifications while condition is met"""
        try:
            while True:
                # No snooze check needed anymore

                # Reset triggered alerts for each cycle (no longer needed for repeat, but keep for potential future use)
                self.triggered_alerts = []

                for alert in self.alerts.copy():  # Iterate over a copy to allow modification
                    price = self.get_crypto_price(alert["symbol"])
                    if not price:
                        continue

                    if self.check_alert_condition(alert, price):
                        if alert['symbol'] not in self.currently_alerting:
                            self.currently_alerting.add(alert['symbol']) # Mark as currently alerting
                        self.handle_triggered_alert(alert, price)
                    else:
                        if alert['symbol'] in self.currently_alerting:
                            self.currently_alerting.remove(alert['symbol']) # Condition no longer met, stop alerting

                time.sleep(self.settings["check_interval"])

        except KeyboardInterrupt:
            self.cleanup()

    def cleanup(self):
        """Cleanup resources before exiting."""
        self.show_toast("🛑 Stopping price monitoring...")
        print(f"DEBUG: Monitoring process stopped by KeyboardInterrupt.")
        if os.path.exists(self.pid_file):
            os.remove(self.pid_file)
            print(f"DEBUG: PID file '{self.pid_file}' removed.")
        else:
            print(f"DEBUG: PID file '{self.pid_file}' not found during cleanup.")
        plt.close('all')  # Close any matplotlib figures

    def select_alert(self, prompt_text: str) -> Optional[Dict]:
        """Select an alert from a sheet dialog."""
        if not self.alerts:
            self.show_toast("No alerts available.")
            return None

        alert_options = [f"{i+1}. {alert['name']}" for i, alert in enumerate(self.alerts)]
        choice_str = self.show_sheet_dialog(prompt_text, alert_options)

        if choice_str:
            try:
                alert_index = int(choice_str.split('.')[0]) - 1
                if 0 <= alert_index < len(self.alerts):
                    return self.alerts[alert_index]
            except ValueError:
                self.show_toast("Invalid selection.")
        return None

    def backtest_alert(self):
        """Simulate alert performance over historical data"""
        alert = self.select_alert("Select alert to backtest:")
        if not alert:
            return

        days = int(self.get_input("Backtest days:", str(self.settings["max_history_days"])))  # Use setting as default
        url = (f"https://api.kucoin.com/api/v1/market/candles?"
               f"symbol={alert['symbol']}&type=1hour&startAt={int(time.time()) - (days * 86400)}")

        triggers = 0
        try:
            data = requests.get(url).json()["data"]
            for candle in data:
                price = float(candle[2])
                if (alert["condition"] == "above" and price > alert["price"]) or \
                   (alert["condition"] == "below" and price < alert["price"]):
                    triggers += 1

            self.show_alert_result(
                f"Backtest Results\n{alert['name']}\n"
                f"Triggers: {triggers}\nPeriod: {days} days"
            )
        except Exception as e:
            self.show_toast(f"Backtest failed: {str(e)}")

    def show_price_history(self):
        """Display price chart for selected alert"""
        alert = self.select_alert("Select alert to view history:")
        if not alert:
            return

        days = self.settings["max_history_days"]  # Use setting for history days
        url = (f"https://api.kucoin.com/api/v1/market/candles?"
               f"symbol={alert['symbol']}&type=1day&startAt={int(time.time()) - (days * 86400)}")

        try:
            data = requests.get(url).json()["data"]
            prices = [float(candle[2]) for candle in data]  # Closing prices
            plt.figure(figsize=(8, 4))
            plt.plot(prices)
            plt.title(f"{alert['name']} {days}-Day History")
            plt.xlabel("Days Ago")
            plt.ylabel("Price")
            plt.savefig("price_history.png")
            subprocess.run(["termux-share", "price_history.png"])
            self.show_toast("📈 Price history chart shared.")
        except Exception as e:
            self.show_toast(f"Chart error: {str(e)}")

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
            "-i", app_info_text.strip()
        ])

    def main(self):
        app = TermuxCryptoGUI()
        while True:
            choice = app.show_menu()
            if choice == "➕ Add Alert":
                app.add_alert()
            elif choice == "📋 List Alerts":
                app.list_alerts()
            elif choice == "🗑️ Remove Alert":
                app.remove_alert()
            elif choice == "🔄 Restart Monitoring":
                if os.path.exists(app.pid_file):
                    app.stop_monitoring()  # Stop existing monitoring if running
                    app.start_monitoring_background() # Then start a new one
                else:
                    app.start_monitoring_background() # Start if not running
            elif choice == "⏹️ Stop Monitoring":
                app.stop_monitoring()
            elif choice == "ℹ️ App Info":
                app.show_app_info()
            elif choice == "📈 Price History":
                app.show_price_history()
            elif choice == "📊 Backtest Alert":
                app.backtest_alert()
            elif choice == "⚙️ Settings":
                app.show_settings()
            elif choice == "📤 Export Alerts":
                app.export_alerts()
            elif choice == "📥 Import Alerts":
                app.import_alerts()
            elif choice == "❌ Exit":
                break

        app.show_toast("👋 Goodbye!")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "monitor":
        app = TermuxCryptoGUI()
        app.monitor_alerts()
    else:
        app = TermuxCryptoGUI()
        app.main()
