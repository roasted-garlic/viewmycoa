
import os
import logging
import requests
from datetime import datetime
from flask import url_for

logger = logging.getLogger(__name__)

class CraftMyPDFIntegration:
    def __init__(self):
        self.api_key = os.environ.get('CRAFTMYPDF_API_KEY')
        self.base_url = 'https://api.craftmypdf.com/v1'
        
    def fetch_templates(self):
        """Fetch templates from CraftMyPDF API"""
        if not self.api_key:
            logger.error("CraftMyPDF API key not configured")
            return []

        headers = {'X-API-KEY': self.api_key, 'Content-Type': 'application/json'}
        
        try:
            logger.debug("Fetching templates from CraftMyPDF API")
            response = requests.get(f'{self.base_url}/list-templates',
                                  headers=headers,
                                  params={'limit': 300, 'offset': 0},
                                  timeout=30)

            if response.status_code == 200:
                data = response.json()
                templates = data.get('templates', [])
                logger.info(f"Successfully fetched {len(templates)} templates")
                return templates
            else:
                logger.error(f"Failed to fetch templates. Status: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error fetching templates: {str(e)}")
            return []

    def generate_pdf(self, product, label_data):
        """Generate PDF using CraftMyPDF API"""
        try:
            if not self.api_key:
                raise ValueError("API key not configured")

            api_data = {
                "template_id": product.craftmypdf_template_id,
                "export_type": "json",
                "output_file": f"{product.batch_number}.pdf",
                "expiration": 10,
                "data": label_data
            }

            headers = {'X-API-KEY': self.api_key, 'Content-Type': 'application/json'}
            response = requests.post(f'{self.base_url}/create',
                                   json=api_data,
                                   headers=headers,
                                   timeout=30)

            if response.status_code != 200:
                raise Exception(f"API Error (Status {response.status_code}): {response.text}")

            result = response.json()
            if result.get('status') != 'success':
                raise Exception(result.get('message', 'Unknown error'))

            return result.get('file')

        except Exception as e:
            logger.error(f"PDF generation error: {str(e)}")
            raise
