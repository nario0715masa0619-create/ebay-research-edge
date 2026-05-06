"""
Scraping integration module for multi-source data collection.
Supports: Scrape.do, Diffbot, Octoparse
"""

import os
import requests
import csv
from dotenv import load_dotenv
from datetime import datetime
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

load_dotenv()

class ScrapeDoClient:
    """Scrape.do API クライアント"""
    def __init__(self):
        self.api_key = os.getenv('SCRAPEDO_API_KEY')
        self.base_url = 'https://api.scrape.do'
    
    def scrape(self, url: str, **kwargs) -> Dict:
        """
        URL をスクレイピング
        
        Args:
            url: ターゲット URL
            **kwargs: JavaScript, proxy など
        
        Returns:
            {'status': 200, 'content': html_content}
        """
        params = {
            'token': self.api_key,  # ← 修正：apikey → token
            'url': url,
            'render': kwargs.get('render_js', 'true'),
        }
        try:
            resp = requests.get(self.base_url, params=params, timeout=30)
            if resp.status_code == 200:
                logger.info(f'✓ Scrape.do: {url[:50]}... fetched ({len(resp.text)} bytes)')
                return {'status': 200, 'content': resp.text}
            else:
                logger.error(f'Scrape.do error: {resp.status_code}')
                return {'status': resp.status_code, 'error': resp.text}
        except Exception as e:
            logger.error(f'Scrape.do request failed: {e}')
            return {'status': 0, 'error': str(e)}

class DiffbotClient:
    """Diffbot API クライアント"""
    def __init__(self):
        self.api_token = os.getenv('DIFFBOT_API_TOKEN')
        self.base_url = 'https://api.diffbot.com/v3/extract'
    
    def extract(self, url: str) -> Dict:
        """
        ページから構造化データを抽出
        
        Args:
            url: ターゲット URL
        
        Returns:
            {'objects': [...], 'status': 'success'}
        """
        params = {'token': self.api_token, 'url': url}
        try:
            resp = requests.get(self.base_url, params=params, timeout=30)
            data = resp.json()
            logger.info(f'✓ Diffbot: {url[:50]}... extracted')
            return data
        except Exception as e:
            logger.error(f'Diffbot request failed: {e}')
            return {'error': str(e)}

class OctoparseHelper:
    """Octoparse タスク実行ヘルパー（ローカル）"""
    def __init__(self):
        self.api_key = os.getenv('OCTOPARSE_API_KEY')
    
    def export_task_csv(self, task_name: str, output_file: str) -> bool:
        """
        Octoparse タスクの結果を CSV エクスポート（手動実行後）
        """
        logger.info(f'Octoparse: Please run task「{task_name}」→ Export CSV → {output_file}')
        return True

# ファクトリー
class ScrapingFactory:
    @staticmethod
    def get_client(service: str):
        if service == 'scrapedo':
            return ScrapeDoClient()
        elif service == 'diffbot':
            return DiffbotClient()
        elif service == 'octoparse':
            return OctoparseHelper()
        else:
            raise ValueError(f'Unknown service: {service}')
