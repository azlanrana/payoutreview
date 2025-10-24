"""JSON output formatter"""

import json
from typing import Dict, Any


class JSONFormatter:
    """Formats validation results as JSON"""
    
    @staticmethod
    def format(results: Dict[str, Any], pretty: bool = True) -> str:
        """
        Format results as JSON string

        Args:
            results: Validation results dictionary
            pretty: If True, format with indentation

        Returns:
            JSON string
        """
        # Create a copy for formatting
        formatted_results = dict(results)

        # Add profit cap information to the top level for easy access
        if 'profit_calculation' in results:
            pc = results['profit_calculation']
            formatted_results['payout_amount'] = pc['capped_total_profit']
            formatted_results['cap_applied'] = pc['cap_applied']

        if pretty:
            return json.dumps(formatted_results, indent=2, ensure_ascii=False)
        else:
            return json.dumps(formatted_results, ensure_ascii=False)
    
    @staticmethod
    def save_to_file(results: Dict[str, Any], filepath: str) -> None:
        """
        Save results to JSON file
        
        Args:
            results: Validation results dictionary
            filepath: Path to output file
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

