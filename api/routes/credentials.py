"""Credentials management routes for streaming services."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import httpx
import base64
import re
from html.parser import HTMLParser

from ..dependencies import get_client


class AuxRadioHTMLParser(HTMLParser):
    """Parse aux radio station HTML table."""

    def __init__(self):
        super().__init__()
        self.stations = []
        self.current_row_id = None
        self.current_tag = None
        self.current_data = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag == 'tr' and 'id' in attrs_dict:
            row_id = attrs_dict['id']
            if row_id.startswith('AuxRadio_'):
                self.current_row_id = row_id.replace('AuxRadio_', '')

        if tag == 'td' and self.current_row_id:
            self.current_tag = 'td'

    def handle_endtag(self, tag):
        if tag == 'tr' and self.current_row_id:
            if len(self.current_data) >= 2:
                self.stations.append({
                    'id': self.current_row_id,
                    'call_sign': self.current_data[0].strip(),
                    'name': self.current_data[1].strip(),
                    'description': '',
                    'stream_url': '',
                    'image_url': ''
                })
            self.current_row_id = None
            self.current_data = []

        if tag == 'td':
            self.current_tag = None

    def handle_data(self, data):
        if self.current_tag == 'td' and self.current_row_id:
            self.current_data.append(data)

router = APIRouter()


class ServiceInfo(BaseModel):
    """Information about a streaming service."""
    name: str
    descrip: str
    signup_url: str
    service_message: str
    is_excluded: bool
    limit_type: str
    limit: int
    supports_upload_download: bool
    supports_aux_radio: bool
    supports_lat_lon: bool
    supports_exclusion: bool


class AccountInfo(BaseModel):
    """Account information for a service."""
    account_id: str
    username: str
    password: str  # Will be base64 encoded
    status: Optional[str] = None
    check_download: bool = False
    check_upload: bool = False


class AddAccountRequest(BaseModel):
    """Request to add an account."""
    service_name: str
    username: str
    password: str
    upload: bool = False
    download: bool = False


class EditAccountRequest(BaseModel):
    """Request to edit an account."""
    account_id: str
    username: str
    password: str
    upload: bool = False
    download: bool = False


class DeleteAccountRequest(BaseModel):
    """Request to delete an account."""
    account_id: str


class ExcludeServiceRequest(BaseModel):
    """Request to enable/disable a service."""
    service_name: str
    excluded: bool


class LocationRequest(BaseModel):
    """Request to set location for TuneIn Radio."""
    latitude: float
    longitude: float


# Service definitions from the HTML
SERVICES = [
    {
        "name": "AmazonCloud",
        "descrip": "Amazon Cloud Drive",
        "signup_url": "http://www.amazon.com/clouddrive/",
        "service_message": "Free or Premium accounts supported",
        "is_excluded": False,
        "limit_type": "Fixed",
        "limit": 1,
        "supports_upload_download": True,
        "supports_aux_radio": False,
        "supports_lat_lon": False,
        "supports_exclusion": True
    },
    {
        "name": "LastFM",
        "descrip": "Last.fm",
        "signup_url": "https://www.last.fm",
        "service_message": "Paid subscription required",
        "is_excluded": False,
        "limit_type": "Fixed",
        "limit": 1,
        "supports_upload_download": False,
        "supports_aux_radio": False,
        "supports_lat_lon": False,
        "supports_exclusion": True
    },
    {
        "name": "Pandora",
        "descrip": "Pandora Internet Radio",
        "signup_url": "http://www.Pandora.com/",
        "service_message": "Free or Premium accounts supported",
        "is_excluded": False,
        "limit_type": "NoLimit",
        "limit": 32767,
        "supports_upload_download": False,
        "supports_aux_radio": False,
        "supports_lat_lon": False,
        "supports_exclusion": True
    },
    {
        "name": "Rhapsody",
        "descrip": "Rhapsody",
        "signup_url": "http://www.Rhapsody.com/nuvo",
        "service_message": "Paid subscription required",
        "is_excluded": True,
        "limit_type": "NoLimit",
        "limit": 32767,
        "supports_upload_download": False,
        "supports_aux_radio": False,
        "supports_lat_lon": False,
        "supports_exclusion": True
    },
    {
        "name": "Sirius",
        "descrip": "SiriusXM Internet Radio",
        "signup_url": "http://www.Sirius.com/",
        "service_message": "Paid internet radio subscription required",
        "is_excluded": True,
        "limit_type": "NoLimit",
        "limit": 32767,
        "supports_upload_download": False,
        "supports_aux_radio": False,
        "supports_lat_lon": False,
        "supports_exclusion": True
    },
    {
        "name": "Slacker",
        "descrip": "Slacker Radio",
        "signup_url": "www.slacker.com",
        "service_message": "Slacker",
        "is_excluded": True,
        "limit_type": "NoLimit",
        "limit": 32767,
        "supports_upload_download": False,
        "supports_aux_radio": False,
        "supports_lat_lon": False,
        "supports_exclusion": True
    },
    {
        "name": "Spotify",
        "descrip": "Spotify",
        "signup_url": "http://www.spotify.com/",
        "service_message": "Premium account required",
        "is_excluded": False,
        "limit_type": "NoLimit",
        "limit": 32767,
        "supports_upload_download": False,
        "supports_aux_radio": False,
        "supports_lat_lon": False,
        "supports_exclusion": True
    },
    {
        "name": "RadioTime",
        "descrip": "TuneIn Radio",
        "signup_url": "http://www.TuneIn.com/",
        "service_message": "Account only required to browse your online presets",
        "is_excluded": False,
        "limit_type": "Fixed",
        "limit": 1,
        "supports_upload_download": False,
        "supports_aux_radio": True,
        "supports_lat_lon": True,
        "supports_exclusion": True
    }
]


@router.get("/services", response_model=List[ServiceInfo])
async def get_services():
    """Get list of available streaming services."""
    return [ServiceInfo(**service) for service in SERVICES]


@router.get("/services/{service_name}/accounts")
async def get_accounts(service_name: str, client = Depends(get_client)):
    """Get accounts for a specific service."""
    device_ip = client.host

    try:
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            url = f"http://{device_ip}/Config/sv.aspx"
            params = {
                "x": "1",
                "action": "getAccountsList",
                "name": service_name
            }

            print(f"[Credentials] Fetching accounts for {service_name} from {device_ip}")
            print(f"[Credentials] URL: {url} with params: {params}")

            response = await http_client.get(url, params=params)

            print(f"[Credentials] Response status for {service_name}: {response.status_code}")

            if response.status_code == 403:
                print(f"[Credentials] 403 Forbidden - Device may require authentication or session")
                raise HTTPException(
                    status_code=503,
                    detail=f"Device returned 403 Forbidden - may require authentication"
                )

            if response.status_code == 404:
                print(f"[Credentials] 404 Not Found - Endpoint may not exist")
                raise HTTPException(
                    status_code=404,
                    detail=f"Service endpoint not found on device"
                )

            response.raise_for_status()

            # The response is HTML with account table
            html_content = response.text
            print(f"[Credentials] Successfully fetched {len(html_content)} bytes for {service_name}")

            return {"html": html_content, "service": service_name}

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except httpx.TimeoutException as e:
        print(f"[Credentials] Timeout fetching accounts for {service_name}: {e}")
        raise HTTPException(
            status_code=504,
            detail=f"Request timeout connecting to device at {device_ip}"
        )
    except httpx.ConnectError as e:
        print(f"[Credentials] Connection error for {service_name}: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Failed to connect to device at {device_ip}"
        )
    except httpx.HTTPError as e:
        print(f"[Credentials] HTTP error for {service_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch accounts: {str(e)}"
        )
    except Exception as e:
        print(f"[Credentials] Unexpected error for {service_name}: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@router.post("/accounts/add")
async def add_account(request: AddAccountRequest, client = Depends(get_client)):
    """Add a new account for a service."""
    device_ip = client.host

    # Base64 encode credentials
    username_b64 = base64.b64encode(request.username.encode()).decode()
    password_b64 = base64.b64encode(request.password.encode()).decode()

    # Build upload/download flags
    ud = ""
    if request.download:
        ud += "D"
    if request.upload:
        ud += "U"

    try:
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            response = await http_client.get(
                f"http://{device_ip}/Config/sv.aspx",
                params={
                    "x": "1",
                    "action": "addAccount",
                    "name": request.service_name,
                    "id": username_b64,
                    "pswd": password_b64,
                    "ud": ud
                }
            )
            response.raise_for_status()

            # Response is error message if failed, empty if success
            result = response.text.strip()
            if result:
                raise HTTPException(status_code=400, detail=result)

            return {"message": "Account added successfully"}

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add account: {str(e)}"
        )


@router.post("/accounts/edit")
async def edit_account(request: EditAccountRequest, client = Depends(get_client)):
    """Edit an existing account."""
    device_ip = client.host

    # Base64 encode credentials
    username_b64 = base64.b64encode(request.username.encode()).decode()
    password_b64 = base64.b64encode(request.password.encode()).decode()

    # Build upload/download flags
    ud = ""
    if request.download:
        ud += "D"
    if request.upload:
        ud += "U"

    try:
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            response = await http_client.get(
                f"http://{device_ip}/Config/sv.aspx",
                params={
                    "x": "1",
                    "action": "editAccount",
                    "name": request.account_id,
                    "id": username_b64,
                    "pswd": password_b64,
                    "ud": ud
                }
            )
            response.raise_for_status()

            # Response is error message if failed, empty if success
            result = response.text.strip()
            if result:
                raise HTTPException(status_code=400, detail=result)

            return {"message": "Account updated successfully"}

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to edit account: {str(e)}"
        )


@router.post("/accounts/delete")
async def delete_account(request: DeleteAccountRequest, client = Depends(get_client)):
    """Delete an account."""
    device_ip = client.host

    try:
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            response = await http_client.get(
                f"http://{device_ip}/Config/sv.aspx",
                params={
                    "x": "1",
                    "action": "removeAccount",
                    "name": request.account_id
                }
            )
            response.raise_for_status()

            return {"message": "Account deleted successfully"}

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete account: {str(e)}"
        )


@router.post("/services/exclude")
async def exclude_service(request: ExcludeServiceRequest, client = Depends(get_client)):
    """Enable or disable a service."""
    device_ip = client.host

    # Value format: +ServiceName to exclude, -ServiceName to include
    value = f"%2B{request.service_name}" if request.excluded else f"-{request.service_name}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            response = await http_client.get(
                f"http://{device_ip}/Config/sv.aspx",
                params={
                    "spa": "1",
                    "cat": "ACCOUNT",
                    "name": "EXCLUDED",
                    "value": value
                }
            )
            response.raise_for_status()

            return {"message": f"Service {'disabled' if request.excluded else 'enabled'} successfully"}

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update service: {str(e)}"
        )


@router.post("/location")
async def set_location(request: LocationRequest, client = Depends(get_client)):
    """Set latitude/longitude for TuneIn Radio local stations."""
    device_ip = client.host

    try:
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            # Set latitude
            await http_client.get(
                f"http://{device_ip}/Config/sv.aspx",
                params={
                    "x": "1",
                    "cat": "LOCATION",
                    "name": "LATITUDE",
                    "value": str(request.latitude)
                }
            )

            # Set longitude
            await http_client.get(
                f"http://{device_ip}/Config/sv.aspx",
                params={
                    "x": "1",
                    "cat": "LOCATION",
                    "name": "LONGITUDE",
                    "value": str(request.longitude)
                }
            )

            return {"message": "Location updated successfully"}

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to set location: {str(e)}"
        )


# Aux Radio Stations

class AuxRadioStation(BaseModel):
    """Additional TuneIn Radio station."""
    id: str
    call_sign: str
    name: str
    description: str
    stream_url: str
    image_url: str


class AddAuxRadioRequest(BaseModel):
    """Request to add aux radio station."""
    call_sign: str
    name: str
    description: str
    stream_url: str
    image_url: str


class EditAuxRadioRequest(BaseModel):
    """Request to edit aux radio station."""
    station_id: str
    call_sign: str
    name: str
    description: str
    stream_url: str
    image_url: str


class DeleteAuxRadioRequest(BaseModel):
    """Request to delete aux radio station."""
    station_id: str


@router.get("/aux-radio/stations", response_model=List[AuxRadioStation])
async def get_aux_radio_stations(client = Depends(get_client)):
    """Get list of additional TuneIn Radio stations."""
    device_ip = client.host

    url = f"http://{device_ip}/Config/sv.aspx"
    params = {
        "x": "1",
        "action": "getAuxRadioList"
    }

    print(f"[AuxRadio] Fetching aux radio stations from {device_ip}")
    print(f"[AuxRadio] URL: {url} with params: {params}")

    try:
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            response = await http_client.get(url, params=params)

            print(f"[AuxRadio] Response status: {response.status_code}")

            if response.status_code == 403:
                print(f"[AuxRadio] 403 Forbidden - Device may require authentication")
                raise HTTPException(
                    status_code=503,
                    detail=f"Device returned 403 Forbidden - may require authentication"
                )

            if response.status_code == 404:
                print(f"[AuxRadio] 404 Not Found - Endpoint may not exist")
                raise HTTPException(
                    status_code=404,
                    detail=f"Aux radio endpoint not found on device"
                )

            response.raise_for_status()

            # Parse HTML response
            html_content = response.text
            print(f"[AuxRadio] Successfully fetched {len(html_content)} bytes")

            parser = AuxRadioHTMLParser()
            parser.feed(html_content)

            print(f"[AuxRadio] Parsed {len(parser.stations)} stations")

            return [AuxRadioStation(**station) for station in parser.stations]

    except HTTPException:
        raise
    except httpx.TimeoutException as e:
        print(f"[AuxRadio] Timeout: {e}")
        raise HTTPException(
            status_code=504,
            detail=f"Request timeout connecting to device at {device_ip}"
        )
    except httpx.ConnectError as e:
        print(f"[AuxRadio] Connection error: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Failed to connect to device at {device_ip}"
        )
    except httpx.HTTPError as e:
        print(f"[AuxRadio] HTTP error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch aux radio stations: {str(e)}"
        )
    except Exception as e:
        print(f"[AuxRadio] Unexpected error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error fetching aux radio stations: {str(e)}"
        )


@router.post("/aux-radio/add")
async def add_aux_radio_station(request: AddAuxRadioRequest, client = Depends(get_client)):
    """Add a new TuneIn Radio station."""
    device_ip = client.host

    # Base64 encode fields
    call_sign_b64 = base64.b64encode(request.call_sign.encode()).decode()
    name_b64 = base64.b64encode(request.name.encode()).decode()
    desc_b64 = base64.b64encode(request.description.encode()).decode()
    url_b64 = base64.b64encode(request.stream_url.encode()).decode()
    img_b64 = base64.b64encode(request.image_url.encode()).decode()

    url = f"http://{device_ip}/Config/auxRadioEditDlg.aspx"
    params = {
        "x": "1",
        "action": "saveEntry",
        "id": "",
        "callSign": call_sign_b64,
        "name": name_b64,
        "desc": desc_b64,
        "playUrl": url_b64,
        "img": img_b64
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            response = await http_client.get(url, params=params)
            response.raise_for_status()

            # Response is error message if failed, empty if success
            result = response.text.strip()
            if result:
                raise HTTPException(status_code=400, detail=result)

            return {"message": "Station added successfully"}

    except httpx.TimeoutException as e:
        raise HTTPException(
            status_code=504,
            detail=f"Timeout connecting to device at {device_ip}"
        )
    except httpx.ConnectError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Could not connect to device at {device_ip}. Is the device web interface running?"
        )
    except HTTPException:
        raise
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add station: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@router.post("/aux-radio/edit")
async def edit_aux_radio_station(request: EditAuxRadioRequest, client = Depends(get_client)):
    """Edit an existing TuneIn Radio station."""
    device_ip = client.host

    # Base64 encode fields
    call_sign_b64 = base64.b64encode(request.call_sign.encode()).decode()
    name_b64 = base64.b64encode(request.name.encode()).decode()
    desc_b64 = base64.b64encode(request.description.encode()).decode()
    url_b64 = base64.b64encode(request.stream_url.encode()).decode()
    img_b64 = base64.b64encode(request.image_url.encode()).decode()

    try:
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            response = await http_client.get(
                f"http://{device_ip}/Config/auxRadioEditDlg.aspx",
                params={
                    "x": "1",
                    "action": "saveEntry",
                    "id": request.station_id,
                    "callSign": call_sign_b64,
                    "name": name_b64,
                    "desc": desc_b64,
                    "playUrl": url_b64,
                    "img": img_b64
                }
            )
            response.raise_for_status()

            # Response is error message if failed, empty if success
            result = response.text.strip()
            if result:
                raise HTTPException(status_code=400, detail=result)

            return {"message": "Station updated successfully"}

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to edit station: {str(e)}"
        )


@router.post("/aux-radio/delete")
async def delete_aux_radio_station(request: DeleteAuxRadioRequest, client = Depends(get_client)):
    """Delete a TuneIn Radio station."""
    device_ip = client.host

    try:
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            response = await http_client.get(
                f"http://{device_ip}/Config/sv.aspx",
                params={
                    "x": "1",
                    "action": "delAuxRadioStation",
                    "value": request.station_id
                }
            )
            response.raise_for_status()

            return {"message": "Station deleted successfully"}

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete station: {str(e)}"
        )


@router.get("/radio-lookup/{call_sign}")
async def lookup_radio_station(call_sign: str):
    """Look up radio station info from Radio Browser API."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            # Try searching by name first
            response = await http_client.get(
                f"https://de1.api.radio-browser.info/json/stations/byname/{call_sign}",
                params={"limit": 10}
            )
            response.raise_for_status()
            stations = response.json()

            if not stations:
                # Try searching by tag
                response = await http_client.get(
                    f"https://de1.api.radio-browser.info/json/stations/bytag/{call_sign}",
                    params={"limit": 10}
                )
                response.raise_for_status()
                stations = response.json()

            # Format results
            results = []
            for station in stations:
                results.append({
                    "call_sign": station.get("name", ""),
                    "name": station.get("name", ""),
                    "description": f"{station.get('country', '')} - {station.get('tags', '')}".strip(" -"),
                    "stream_url": station.get("url_resolved") or station.get("url", ""),
                    "image_url": station.get("favicon", "")
                })

            return results

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to lookup station: {str(e)}"
        )
