[![DOI](https://zenodo.org/badge/828145800.svg)](https://doi.org/10.1111/2041-210X.14436)

This repository contains an update and refactor of the [ecoEye academic software](https://github.com/SAT-Lab-GitHub/ecoEye-open) to support firmware version 4.7.0 for the OpenMV RT1062 and H7PLUS (OPENMV4P) boards.

**ecoEye** is an embedded computer vision camera designed for ecological research and fieldwork. The corresponding scientific publication is available at [https://doi.org/10.1111/2041-210X.14436](https://doi.org/10.1111/2041-210X.14436).

---

### Assembly Instructions

This repository includes original computer-aided design (CAD) and electronic design automation (EDA) files for assembling the ecoEye system using the H7PLUS board. Detailed assembly instructions are available in the [Wiki](https://github.com/SAT-Lab-GitHub/ecoEye-open/wiki).

---

### H7PLUS vs RT1062

We have transitioned from using the H7PLUS to the RT1062 board.  
- The latest version compatible with the H7PLUS is available in the [`h7plus` branch](https://github.com/cdrezen/ecoeye/tree/h7plus).
- The `main` branch now targets the RT1062. It is **not guaranteed** to run on the H7PLUS and does **not support** its built-in IR LEDs.

---

### Configuration

Edit `src/config/settings.py` to configure the device date and other parameters. All configuration options are documented within the file.

---

### Installation

#### Manual Installation

1. Connect the camera or an SD card reader to your computer.
2. Mount the SD card.
3. Copy the entire contents of the `src/` directory into the **root** of the SD card.
4. Unmount the SD card.
5. Restart the camera:
    - Unmount and unplug the device
    - Either press the hardware button on the camera (or press once if it's shut down),
    - Or reconnect the device and start `main.py` via the OpenMV IDE.

#### Linux: Automated Installation and Date Configuration

1. Create a `.env` file with a `DEV_NAME` variable, where `DEV_NAME` matches the device name from `lsblk`. Example:

    ```sh
    DEV_NAME=sda1
    ```

2. Make the `run.sh` script executable and run it:

    ```sh
    chmod +x run.sh
    ./run.sh
    ```

3. Restart the camera as described above after the script completes.
