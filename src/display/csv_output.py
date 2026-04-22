import csv
import logging
from pathlib import Path
from typing import List
from datetime import datetime
from src.models.data_models import ScoredCandidate
from src.config.config import config

logger = logging.getLogger(__name__)


class CSVOutput:
    """スコア付き候補をCSV形式で出力するクラス"""
    
    def __init__(self):
        self.config = config
        self.output_dir = config.processed_data_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export_candidates(self, candidates: List[ScoredCandidate], filename: str = None) -> Path:
        """
        候補一覧をCSVファイルに出力
        
        Args:
            candidates: ScoredCandidate のリスト
            filename: 出力ファイル名（Noneの場合は自動生成）
        
        Returns:
            出力ファイルのパス
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"candidates_{self.config.active_category}_{timestamp}.csv"
        
        output_path = self.output_dir / filename
        
        # 出力列の定義
        fieldnames = [
            'candidate_id',
            'item_id',
            'sold_30d',
            'sold_90d',
            'active_count',
            'median_price_usd',
            'avg_price_usd',
            'min_price_usd',
            'max_price_usd',
            'domestic_min_price_jpy',
            'domestic_median_price_jpy',
            'estimated_profit_jpy',
            'estimated_profit_rate',
            'str',
            'candidate_score',
            'decision_status',
            'calculated_at'
        ]
        
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for candidate in candidates:
                    writer.writerow({
                        'candidate_id': candidate.candidate_id,
                        'item_id': candidate.item_id,
                        'sold_30d': candidate.sold_30d,
                        'sold_90d': candidate.sold_90d,
                        'active_count': candidate.active_count,
                        'median_price_usd': candidate.median_price_usd,
                        'avg_price_usd': candidate.avg_price_usd,
                        'min_price_usd': candidate.min_price_usd,
                        'max_price_usd': candidate.max_price_usd,
                        'domestic_min_price_jpy': candidate.domestic_min_price_jpy,
                        'domestic_median_price_jpy': candidate.domestic_median_price_jpy,
                        'estimated_profit_jpy': candidate.estimated_profit_jpy,
                        'estimated_profit_rate': candidate.estimated_profit_rate,
                        'str': candidate.str,
                        'candidate_score': candidate.candidate_score,
                        'decision_status': candidate.decision_status.value,
                        'calculated_at': candidate.calculated_at.isoformat()
                    })
            
            logger.info(f"Exported {len(candidates)} candidates to {output_path}")
            return output_path
        
        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")
            raise
    
    def export_raw_data(self, data: List[dict], filename: str) -> Path:
        """
        生データをCSVファイルに出力
        
        Args:
            data: 出力対象のデータリスト
            filename: 出力ファイル名
        
        Returns:
            出力ファイルのパス
        """
        output_path = self.output_dir / filename
        
        if not data:
            logger.warning("No data to export")
            return output_path
        
        try:
            fieldnames = data[0].keys()
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            
            logger.info(f"Exported {len(data)} records to {output_path}")
            return output_path
        
        except Exception as e:
            logger.error(f"Error exporting raw data: {e}")
            raise
