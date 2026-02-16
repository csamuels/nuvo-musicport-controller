"""Device information and management endpoints."""

import re
import httpx
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..config import settings

router = APIRouter(prefix="/device", tags=["Device"])


class DeviceStatus(BaseModel):
    """Device status information."""

    download_progress: int
    install_progress: int
    product: str
    branding: str
    label: str
    build: str
    exe: str
    time_stamp: str
    ntp_sync_in_progress: int
    config_crc: str
    amazon_cloud_status: str
    total_storage: str
    available_storage: str


class ServiceEndpoint(BaseModel):
    """Service endpoint information."""

    service_name: str
    endpoint: str


class AccountInfo(BaseModel):
    """Account information for a streaming service."""

    service_name: str
    username: Optional[str] = None
    status: Optional[str] = None
    has_account: bool = False
    login_failed: bool = False
    html_content: str  # Raw HTML for advanced parsing


def parse_js_status(js_content: str) -> Dict[str, Any]:
    """
    Parse JavaScript variable assignment into a dictionary.

    Example: var status = { key : value, ... }
    """
    # Extract the object content between { and }
    match = re.search(r'var\s+status\s*=\s*{([^}]+)}', js_content, re.DOTALL)
    if not match:
        raise ValueError("Could not parse status object")

    obj_content = match.group(1)

    # Parse key-value pairs
    result = {}
    for line in obj_content.split('\n'):
        line = line.strip()
        if not line or line == ',':
            continue

        # Match: key : value
        kv_match = re.match(r'[,\s]*(\w+)\s*:\s*(.+?)(?:,?\s*$)', line)
        if kv_match:
            key = kv_match.group(1)
            value = kv_match.group(2).strip()

            # Remove quotes and trailing comma
            value = value.strip("'\"").rstrip(',').strip()

            # Try to convert to number
            try:
                if '.' in value:
                    value = float(value)
                else:
                    value = int(value)
            except ValueError:
                pass

            result[key] = value

    return result


@router.get("/status", response_model=DeviceStatus)
async def get_device_status():
    """
    Get device status from the MusicPort web interface.

    Fetches system information including:
    - Product model and version
    - Storage information
    - Cloud sync status
    - System timestamps
    """
    url = f"http://{settings.nuvo_host}/Config/getstatus"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, params={
                "_": "1771083968201",
                "x": "15",
                "amazonCloudStatus": "1"
            })
            response.raise_for_status()

            # Parse the JavaScript response
            js_content = response.text
            status_data = parse_js_status(js_content)

            # Map to our model (converting camelCase to snake_case)
            return DeviceStatus(
                download_progress=status_data.get('downloadProgress', -1),
                install_progress=status_data.get('installProgress', -1),
                product=status_data.get('product', 'Unknown'),
                branding=status_data.get('branding', 'Unknown'),
                label=status_data.get('label', 'Unknown'),
                build=status_data.get('build', 'Unknown'),
                exe=status_data.get('exe', 'Unknown'),
                time_stamp=status_data.get('timeStamp', 'Unknown'),
                ntp_sync_in_progress=status_data.get('ntpsyncInProgress', 0),
                config_crc=status_data.get('configCRC', ''),
                amazon_cloud_status=status_data.get('amazonCloudStatus', ''),
                total_storage=str(status_data.get('totalStorage', 'Unknown')),
                available_storage=str(status_data.get('availableStorage', 'Unknown')),
            )

    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"Failed to fetch device status: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing device status: {str(e)}")


@router.get("/services", response_model=List[ServiceEndpoint])
async def get_service_endpoints():
    """
    Get list of available service endpoints from the device.

    Returns a list of streaming services and system endpoints
    available on the MusicPort device.
    """
    # Based on the screenshot, these are the known endpoints
    services = [
        ServiceEndpoint(service_name="AmazonCloud", endpoint="/sv.aspx?_=1771084137918&x=1&action=getAccountsList&name=AmazonCloud"),
        ServiceEndpoint(service_name="LastFM", endpoint="/sv.aspx?_=1771084138191&x=1&action=getAccountsList&name=LastFM"),
        ServiceEndpoint(service_name="Spotify", endpoint="/sv.aspx?_=1771084138408&x=1&action=getAccountsList&name=Spotify"),
        ServiceEndpoint(service_name="Rhapsody", endpoint="/sv.aspx?_=1771084138722&x=1&action=getAccountsList&name=Rhapsody"),
        ServiceEndpoint(service_name="Sirius", endpoint="/sv.aspx?_=1771084139393&x=1&action=getAccountsList&name=Sirius"),
        ServiceEndpoint(service_name="Slacker", endpoint="/sv.aspx?_=1771084139152&x=1&action=getAccountsList&name=Slacker"),
        ServiceEndpoint(service_name="Pandora", endpoint="/sv.aspx?_=1771084139365&x=1&action=getAccountsList&name=Pandora"),
        ServiceEndpoint(service_name="RadioTime", endpoint="/sv.aspx?_=1771084139717&x=1&action=getAccountsList&name=RadioTime"),
        ServiceEndpoint(service_name="NasIist", endpoint="/sv.aspx?_=1771084140032&x=1&action=getNasIist"),
        ServiceEndpoint(service_name="Storage", endpoint="/sv.aspx?_=1771084140143&x=1&action=get&cat=STORAGE&name=SCAN_COUNT"),
        ServiceEndpoint(service_name="ScanProgress", endpoint="/sv.aspx?_=1771084140254&x=1&action=get&cat=STORAGE&name=SCAN_SEARCH"),
        ServiceEndpoint(service_name="AuxRadioList", endpoint="/sv.aspx?_=1771084140369&x=1&action=getAuxRadioList"),
    ]

    return services


@router.get("/accounts/{service_name}", response_model=AccountInfo)
async def get_service_account(service_name: str):
    """
    Get account information for a specific streaming service.

    Args:
        service_name: Name of the service (e.g., 'Pandora', 'Spotify', 'LastFM')

    Returns:
        Account information including status and configuration
    """
    url = f"http://{settings.nuvo_host}/sv.aspx"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, params={
                "_": "1771084139365",
                "x": "1",
                "action": "getAccountsList",
                "name": service_name
            })
            response.raise_for_status()

            html_content = response.text

            # Parse the HTML to extract account info
            has_account = "No credentials are currently configured" not in html_content

            username = None
            status = None
            login_failed = "Login failed" in html_content

            if has_account:
                # Try to extract username from table
                username_match = re.search(r"x-userid='([^']+)'", html_content)
                if username_match:
                    username = username_match.group(1)

                # Extract status
                status_match = re.search(r'<label class="error">([^<]+)</label>', html_content)
                if status_match:
                    status = status_match.group(1)
                elif "Login failed" not in html_content:
                    status = "Connected"

            return AccountInfo(
                service_name=service_name,
                username=username,
                status=status,
                has_account=has_account,
                login_failed=login_failed,
                html_content=html_content
            )

    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"Failed to fetch account info: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing account info: {str(e)}")
