"""BlueBOLT device communication via CV2 network card (XML over UDP)."""
import asyncio
import logging
import socket
import xml.etree.ElementTree as ET
from typing import Any, Dict, Optional

from .const import DEFAULT_PORT, DEFAULT_TIMEOUT, DEVICE_CLASS_MAP, DEVICE_CONFIG

_LOGGER = logging.getLogger(__name__)


class BlueBoltDevice:
    """Representation of a BlueBOLT device (M4315, F1500, etc.) accessed via CV2."""

    def __init__(
        self,
        host: str,
        mac: str,
        port: int = DEFAULT_PORT,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        """Initialize the BlueBOLT device interface.

        Args:
            host: IP address of the CV2 network card
            mac: CV2 card MAC address (12 hex characters)
            port: UDP port (default 57010)
            timeout: Timeout for UDP communication in seconds
        """
        self.host = host
        self.mac = mac.lower()
        self.port = port
        self.timeout = timeout

        self.cv2_id = self.mac

        # Device info (discovered on connect)
        self.device_class: Optional[str] = None
        self.device_id: Optional[str] = None
        self.device_type: Optional[str] = None
        self.firmware_version: Optional[str] = None

    async def _send_command(
        self, device_class: str, device_id: str, message: str
    ) -> Optional[str]:
        """Send XML command via UDP and receive response.

        Args:
            device_class: Device class (e.g., "cv2", "km4315")
            device_id: Device ID
            message: XML message content (without wrapper)

        Returns:
            XML response string or None if timeout/error
        """
        xml_command = (
            f'<?xml version="1.0" ?>'
            f'<device class="{device_class}" id="{device_id}">{message}</device>'
        )

        loop = asyncio.get_event_loop()
        sock = None

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)

            message_bytes = xml_command.encode("utf-8")
            await loop.run_in_executor(
                None, sock.sendto, message_bytes, (self.host, self.port)
            )
            _LOGGER.debug("Sent to %s:%d: %s", self.host, self.port, xml_command)

            data, _ = await loop.run_in_executor(None, sock.recvfrom, 4096)
            response = data.decode("utf-8")
            _LOGGER.debug("Received from %s:%d: %s", self.host, self.port, response)

            return response

        except socket.timeout:
            _LOGGER.error(
                "Timeout communicating with BlueBOLT CV2 at %s:%d",
                self.host,
                self.port,
            )
            return None
        except Exception as e:
            _LOGGER.error(
                "Error communicating with BlueBOLT CV2 at %s:%d: %s",
                self.host,
                self.port,
                e,
            )
            return None
        finally:
            if sock:
                sock.close()

    async def connect(self) -> bool:
        """Connect to CV2 and discover connected power management device.

        Returns:
            True if CV2 responds and a supported device is discovered
        """
        response = await self._send_command(
            "cv2", self.cv2_id, "<command><sendfamily/></command>"
        )

        if not response:
            return False

        try:
            root = ET.fromstring(response)

            for kids in root.findall(".//kids"):
                device_class = kids.get("class")
                if device_class in DEVICE_CLASS_MAP:
                    device_id_elem = kids.find("k")
                    if device_id_elem is not None and device_id_elem.text:
                        self.device_class = device_class
                        self.device_id = device_id_elem.text
                        self.device_type = DEVICE_CLASS_MAP[device_class]
                        _LOGGER.info(
                            "Discovered %s device: %s (ID: %s)",
                            self.device_type,
                            self.device_class,
                            self.device_id,
                        )
                        return True

            _LOGGER.error("No supported BlueBOLT-enabled device found via CV2")
            return False

        except ET.ParseError as e:
            _LOGGER.error("Failed to parse device discovery XML: %s", e)
            return False

    async def get_device_info(self) -> Dict[str, Any]:
        """Fetch device information from CV2.

        Returns:
            Dictionary with device info (firmware version, etc.)
        """
        if not self.device_id:
            _LOGGER.error("CV2 not initialized - call connect() first")
            return {}

        response = await self._send_command(
            self.device_class, self.device_id, "<command><sendinfo/></command>"
        )

        if not response:
            return {}

        try:
            root = ET.fromstring(response)
            info = {
                "firmware": root.findtext(".//fwver", "Unknown"),
            }
            self.firmware_version = info["firmware"]
            return info
        except ET.ParseError as e:
            _LOGGER.error("Failed to parse device info XML: %s", e)
            return {}

    async def get_status(self) -> Dict[str, Any]:
        """Get complete device status via CV2 (power + outlets).

        Returns:
            Dictionary with voltage, current, power, temperature, outlet states,
            and UPS-specific data (for UPS models)
        """
        if not self.device_id:
            _LOGGER.error("CV2 not initialized - call connect() first")
            return {}

        response = await self._send_command(
            self.device_class, self.device_id, "<command><sendstatus/></command>"
        )

        if not response:
            return {}

        try:
            root = ET.fromstring(response)

            status = {
                "voltage": float(root.findtext(".//voltage", "0")),
                "current": float(root.findtext(".//amperage", "0")),
                "power": float(root.findtext(".//wattage", "0")),
                "apparent_power": float(root.findtext(".//pwrva", "0")),
                "power_factor": float(root.findtext(".//pwrfact", "0")),
                "temperature": float(root.findtext(".//temperature", "0")),
            }

            # UPS-specific sensors (from F1500-UPS)
            if root.find(".//voltageout") is not None:
                status["voltage_out"] = float(root.findtext(".//voltageout", "0"))
            if root.find(".//battlevel") is not None:
                status["battery_level"] = float(root.findtext(".//battlevel", "0"))
            if root.find(".//loadlevel") is not None:
                status["load_level"] = float(root.findtext(".//loadlevel", "0"))
            if root.find(".//pwrcond") is not None:
                status["power_condition"] = int(root.findtext(".//pwrcond", "0"))

            outlets = {}
            for outlet_elem in root.findall(".//outlet"):
                outlet_id = int(outlet_elem.get("id", "0"))
                if outlet_id > 0:
                    outlets[outlet_id] = outlet_elem.text == "1"

            status["outlets"] = outlets
            return status

        except (ET.ParseError, ValueError) as e:
            _LOGGER.error("Failed to parse device status XML: %s", e)
            return {}

    async def set_outlet(self, outlet_id: int, state: bool) -> bool:
        """Control outlet state via CV2.

        Args:
            outlet_id: Outlet number (1-N based on device type)
            state: True to turn on, False to turn off

        Returns:
            True if successful, False otherwise
        """
        if not self.device_id:
            _LOGGER.error("CV2 not initialized - call connect() first")
            return False

        device_config = DEVICE_CONFIG.get(self.device_type, {})
        max_outlets = device_config.get("outlets") or device_config.get("outlet_banks", 8)

        if not 1 <= outlet_id <= max_outlets:
            _LOGGER.error(
                "Invalid outlet ID: %d (must be 1-%d)", outlet_id, max_outlets
            )
            return False

        state_value = "1" if state else "0"
        message = f'<command xid="set_outlet_{outlet_id}"><outlet id="{outlet_id}">{state_value}</outlet></command>'

        response = await self._send_command(self.device_class, self.device_id, message)

        if not response:
            return False

        try:
            root = ET.fromstring(response)
            ack = root.find(f".//ack[@xid='set_outlet_{outlet_id}']")
            return ack is not None
        except ET.ParseError:
            return False
