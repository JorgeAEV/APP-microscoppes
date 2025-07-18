import requests
import json
import os
from typing import Optional, Dict, Any

class APIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.timeout = 5  # segundos
    
    def get_system_status(self) -> Optional[Dict[str, Any]]:
        try:
            response = self.session.get(
                f"{self.base_url}/system_status",
                timeout=self.timeout
            )
            return response.json() if response.status_code == 200 else None
        except requests.exceptions.RequestException:
            return None
    
    def get_microscopes(self) -> list:
        try:
            response = self.session.get(
                f"{self.base_url}/microscopes",
                timeout=self.timeout
            )
            return response.json() if response.status_code == 200 else []
        except requests.exceptions.RequestException:
            return []
    
    def add_microscope(self, microscope_id: str) -> bool:
        try:
            response = self.session.post(
                f"{self.base_url}/add_microscope",
                json={"microscope_id": microscope_id},
                timeout=self.timeout
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def get_microscope_config(self, microscope_id: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.session.get(
                f"{self.base_url}/microscope_config/{microscope_id}",
                timeout=self.timeout
            )
            return response.json() if response.status_code == 200 else None
        except requests.exceptions.RequestException:
            return None
    
    def set_led_state(self, microscope_id: str, state: bool) -> bool:
        try:
            response = self.session.post(
                f"{self.base_url}/set_led_state",
                json={
                    "microscope_id": microscope_id,
                    "state": state
                },
                timeout=self.timeout
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def set_led_intensity(self, microscope_id: str, intensity: int) -> bool:
        try:
            response = self.session.post(
                f"{self.base_url}/set_led_intensity",
                json={
                    "microscope_id": microscope_id,
                    "intensity": intensity
                },
                timeout=self.timeout
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def set_led_color(self, microscope_id: str, color: str) -> bool:
        try:
            response = self.session.post(
                f"{self.base_url}/set_led_color",
                json={
                    "microscope_id": microscope_id,
                    "color": color
                },
                timeout=self.timeout
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def capture_image(self, microscope_id: str) -> Optional[bytes]:
        try:
            response = self.session.get(
                f"{self.base_url}/capture_image/{microscope_id}",
                timeout=self.timeout
            )
            return response.content if response.status_code == 200 else None
        except requests.exceptions.RequestException:
            return None
    
    def save_setting(self, key: str, value: Any) -> bool:
        try:
            response = self.session.post(
                f"{self.base_url}/save_setting",
                json={
                    "key": key,
                    "value": value
                },
                timeout=self.timeout
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False