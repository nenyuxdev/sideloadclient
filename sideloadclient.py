import os
import sys
import subprocess

def get_bin_path(tool_name):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    if sys.platform.startswith("win"):
        ext = ".exe"
        platform_dir = "windows"
    elif sys.platform == "darwin":
        ext = ""
        platform_dir = "mac"
    else:
        ext = ""
        platform_dir = "linux"
    
    path = os.path.join(base_path, platform_dir, tool_name + ext)
    return path if os.path.exists(path) else tool_name

ADB = get_bin_path("adb")
FASTBOOT = get_bin_path("fastboot")

def main():
    if len(sys.argv) < 3:
        print("Usage: python sideloadclient.py <action> <file>")
        print("Actions: sideload | fastboot")
        sys.exit(1)

    action = sys.argv[1].lower()
    file_path = sys.argv[2]

    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)

    adb_result = subprocess.run([ADB, "devices"], capture_output=True, text=True)
    adb_lines = adb_result.stdout.strip().split("\n")[1:]

    normal_devices = []
    sideload_devices = []
    for line in adb_lines:
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 2:
            serial, state = parts[0], parts[1]
            if state == "device":
                normal_devices.append(serial)
            elif state == "sideload":
                sideload_devices.append(serial)

    fb_result = subprocess.run([FASTBOOT, "devices"], capture_output=True, text=True)
    fb_lines = [line.strip() for line in (fb_result.stdout + fb_result.stderr).splitlines() if line.strip()]
    fastboot_devices = []
    for line in fb_lines:
        parts = line.split()
        if parts:
            fastboot_devices.append(parts[0])

    if action == "sideload":
        if sideload_devices:
            print(f"Target device in sideload mode: {sideload_devices[0]}")
        elif normal_devices:
            print(f"ADB device detected: {normal_devices[0]}")
            choice = input("Reboot device to sideload mode? (y/n): ").strip().lower()
            if choice == "y":
                subprocess.run([ADB, "reboot", "sideload"], capture_output=True)
                print("Rebooting to sideload... Run the command again once ready.")
                sys.exit(0)
            else:
                print("Error: Device must be in sideload mode.")
                sys.exit(1)
        elif fastboot_devices:
            print(f"Fastboot device detected: {fastboot_devices[0]}")
            choice = input("Reboot device to recovery mode? (y/n): ").strip().lower()
            if choice == "y":
                subprocess.run([FASTBOOT, "reboot", "recovery"], capture_output=True)
                print("Rebooting to recovery... Run the command again once ready.")
                sys.exit(0)
            else:
                print("Error: Device must be in sideload mode.")
                sys.exit(1)
        else:
            print("Error: No device detected.")
            sys.exit(1)

        print(f"Flashing {file_path} via sideload...")
        process = subprocess.Popen([ADB, "sideload", file_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        for line in process.stdout:
            line_str = line.strip()
            if "(~" in line_str and "%)" in line_str:
                try:
                    percent_str = line_str.split("(~")[1].split("%)")[0]
                    percent = int(percent_str)
                    bar_len = 30
                    filled = int(bar_len * percent / 100)
                    bar = "█" * filled + "░" * (bar_len - filled)
                    sys.stdout.write(f"\r[{bar}] {percent}%")
                    sys.stdout.flush()
                except ValueError:
                    sys.stdout.write(line)
            elif "Total xfer:" in line_str:
                bar = "█" * 30
                sys.stdout.write(f"\r[{bar}] 100%\n")
                sys.stdout.flush()
            else:
                if line_str:
                    sys.stdout.write(line_str + "\n")
                    sys.stdout.flush()
                
        process.wait()

        if process.returncode != 0:
            print("\nSideload failed.")
            sys.exit(1)

    elif action == "fastboot":
        if fastboot_devices:
            device = fastboot_devices[0]
            print(f"Target device: {device}")
        elif normal_devices:
            print(f"ADB device detected: {normal_devices[0]}")
            choice = input("Reboot device to fastboot mode? (y/n): ").strip().lower()
            if choice == "y":
                subprocess.run([ADB, "reboot", "bootloader"], capture_output=True)
                print("Rebooting to fastboot... Run the command again once ready.")
                sys.exit(0)
            else:
                print("Error: Device must be in fastboot mode.")
                sys.exit(1)
        elif sideload_devices:
            print(f"Device in sideload mode detected: {sideload_devices[0]}")
            choice = input("Reboot device to fastboot mode? (y/n): ").strip().lower()
            if choice == "y":
                subprocess.run([ADB, "reboot", "bootloader"], capture_output=True)
                print("Rebooting to fastboot... Run the command again once ready.")
                sys.exit(0)
            else:
                print("Error: Device must be in fastboot mode.")
                sys.exit(1)
        else:
            print("Error: No Fastboot device detected.")
            sys.exit(1)

        slot_result = subprocess.run([FASTBOOT, "getvar", "current-slot"], capture_output=True, text=True)
        slot_output = slot_result.stdout + slot_result.stderr
        active_slot = ""
        for line in slot_output.split("\n"):
            if "current-slot:" in line:
                val = line.split(":")[-1].strip().lower()
                if val in ["a", "b"]:
                    active_slot = val

        file_name = os.path.basename(file_path).lower()
        if "vendor_boot" in file_name or "vendor-boot" in file_name:
            base_part = "vendor_boot"
        elif "init_boot" in file_name or "init-boot" in file_name:
            base_part = "init_boot"
        elif "dtbo" in file_name:
            base_part = "dtbo"
        elif "dtb" in file_name:
            base_part = "dtb"
        elif "recovery" in file_name:
            base_part = "recovery"
        elif "vbmeta" in file_name:
            base_part = "vbmeta"
        else:
            base_part = "boot"

        if active_slot:
            partition = f"{base_part}_{active_slot}"
            print(f"Active slot detected ({active_slot}). Flashing to {partition}...")
        else:
            partition = base_part
            print(f"No A/B slots detected. Flashing to normal {partition} partition...")

        print(f"Flashing {file_path} to {partition} via fastboot...")
        cmd = [FASTBOOT, "flash", partition, file_path]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        bar_len = 30
        bar = "█" * bar_len

        for line in process.stdout:
            line_str = line.strip()
            if "Sending" in line_str:
                sys.stdout.write(f"\r[{bar}] Sending 100%")
                sys.stdout.flush()
            elif "Writing" in line_str:
                sys.stdout.write(f"\r[{bar}] Writing 100%\n")
                sys.stdout.flush()
            elif "Finished" in line_str or "OKAY" in line_str:
                pass
            else:
                if line_str:
                    print(f"\n  {line_str}")
                    sys.stdout.flush()
                
        process.wait()

        if process.returncode != 0:
            print("\nFlash failed.")
            sys.exit(1)

    else:
        print(f"Error: Unknown action '{action}'. Use 'sideload' or 'fastboot'.")
        sys.exit(1)

if __name__ == "__main__":
    main()