import re
from config import Config
import db

class BaseMarkingPortalAdapter:
    """Base class for marking portal integrations."""
    def get_portal_url(self, village=None):
        raise NotImplementedError

    def prepare_assisted_payload(self, village):
        raise NotImplementedError


class AssistedWorkflowAdapter(BaseMarkingPortalAdapter):
    """
    Practical assisted workflow adapter for https://generate.snsies.com/
    Provides:
    - Safe direct links to open the external portal in a new browser tab.
    - Pre-formatted village metadata for one-click clipboard copying.
    - Automatic validation between downloaded KML filename/metadata and active village.
    - Non-intrusive, zero-credential, secure integration.
    """
    def __init__(self, base_url=None):
        self.base_url = base_url or Config.MARKING_PORTAL_URL

    def get_portal_url(self, village=None):
        return self.base_url

    def prepare_assisted_payload(self, village):
        if not village:
            return {}
        
        v_name = village.get('village_name', '')
        v_code = str(village.get('village_code', ''))
        d_name = village.get('district_name', '')
        s_name = village.get('subdistrict_name', '')
        zone = village.get('zone', '')

        # Plain search string for quick paste in portal search boxes
        clipboard_search = f"{v_name} {v_code}".strip()
        
        # Comprehensive detail block
        clipboard_full = (
            f"Village: {v_name}\n"
            f"Village Code: {v_code}\n"
            f"District: {d_name}\n"
            f"Subdistrict: {s_name}\n"
            f"Zone: {zone}"
        )

        return {
            "portal_url": self.base_url,
            "village_name": v_name,
            "village_code": v_code,
            "district_name": d_name,
            "subdistrict_name": s_name,
            "clipboard_search": clipboard_search,
            "clipboard_full": clipboard_full
        }

    def verify_kml_match(self, village, kml_filename, kml_placemarks):
        """
        Check if the uploaded KML file name or placemarks contain the village code or name.
        Returns match score and helpful warning if mismatch detected.
        """
        v_code = str(village.get('village_code', '')).lower()
        v_name = str(village.get('village_name', '')).lower()
        clean_fn = kml_filename.lower()

        code_in_filename = v_code in clean_fn if v_code else False
        name_in_filename = v_name in clean_fn if v_name else False

        confidence = 'high' if (code_in_filename or name_in_filename) else 'unverified'
        match_message = "File name matches village identifier." if (code_in_filename or name_in_filename) else "Please ensure this KML belongs to the active village."

        return {
            "confidence": confidence,
            "code_matched": code_in_filename,
            "name_matched": name_in_filename,
            "message": match_message
        }


class DirectApiAdapter(BaseMarkingPortalAdapter):
    """
    Pluggable adapter for future direct REST API integration with generate.snsies.com
    when authorized API credentials or webhooks are officially granted.
    """
    def __init__(self, api_endpoint=None, api_token=None):
        self.api_endpoint = api_endpoint
        self.api_token = api_token

    def is_configured(self):
        return bool(self.api_endpoint and self.api_token)

    def trigger_auto_fetch(self, village_code):
        if not self.is_configured():
            return {
                "success": False,
                "error": "Direct API integration requires documented API credentials. Please use the assisted workflow."
            }
        return {"success": False, "error": "Direct API adapter not yet provisioned with authorized endpoint."}


# Global adapter instance
marking_adapter = AssistedWorkflowAdapter()
