#!/usr/bin/env python3
"""
Trading Payout Compliance System
Main entry point for validation
"""

import argparse
import sys
import os
from decimal import Decimal
from dotenv import load_dotenv

from src.data_access import SheetsClient, CSVClient, ValidationError
from src.engine import ValidationProcessor
from src.output import JSONFormatter, SheetsWriter


def main():
    """Main execution flow"""
    # Load environment variables
    load_dotenv()

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Trading Payout Compliance Validation System',
        epilog="""
Examples:
  # Simple: Default $100k account
  python main.py trades.csv

  # Specify account size for correct 6% cap calculation
  python main.py trades.csv --account-size 50000

  # Advanced options
  python main.py trades.csv --account 250000 --verbose --output results.json
        """
    )

    parser.add_argument(
        'csv_file',
        help='Path to CSV file containing trade data'
    )

    parser.add_argument(
        '--config',
        help='Path to config CSV file (optional)',
        default=None
    )

    parser.add_argument(
        '--account-size',
        '--account',
        type=float,
        help='Account size in dollars (default: 100000)',
        default=100000.0
    )

    parser.add_argument(
        '--output',
        '-o',
        help='Save JSON results to file',
        default=None
    )

    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()
    
    try:
        # Read CSV file
        if args.verbose:
            print(f"Reading data from CSV: {args.csv_file}")
            print(f"Using account size: ${args.account_size:,.0f}")

        csv_client = CSVClient()
        trades_df, config = csv_client.read_csv(args.csv_file, args.config)

        # Override account size if provided
        if hasattr(config, 'account_size'):
            config.account_size = Decimal(str(args.account_size))

        if args.verbose:
            print(f"Loaded {len(trades_df)} trades from CSV")
            print(f"Configuration: {config}")

        # Convert DataFrame to Trade objects
        trades = csv_client.trades_to_list(trades_df)

        # Initialize validation processor
        processor = ValidationProcessor(config)

        # Run validation
        if args.verbose:
            print("Running validation...")

        results = processor.process(trades)

        # Generate output filename
        import os
        base_name = os.path.splitext(os.path.basename(args.csv_file))[0]
        output_file = f"finished_sheets/{base_name}_analysis.csv"

        # Save results to CSV file automatically
        CSVClient.save_colored_trades_csv(trades_df, results, output_file)

        # Print summary
        decision = results.get('recommendation')
        total_trades = results.get('summary', {}).get('total_trades', 0)
        total_profit = results.get('summary', {}).get('total_profit', 0)

        print("\n" + "="*50)
        print("TRADING PAYOUT COMPLIANCE RESULTS")
        print("="*50)
        print(f"📊 Total Trades: {total_trades}")
        print(f"💰 Capped Payout: ${total_profit:,.2f}")

        if decision == 'APPROVE':
            print("✅ DECISION: APPROVE PAYOUT")
        elif decision == 'REJECT':
            print("❌ DECISION: REJECT PAYOUT")
        else:
            print("⚠️ DECISION: MANUAL REVIEW REQUIRED")

        print(f"📁 Results saved to: {output_file}")

        # Show rule violations summary
        rules = results.get('rules', {})
        violations_found = []
        for rule_key, rule_result in rules.items():
            violations = rule_result.get('violations', [])
            if violations:
                rule_name = {
                    'blue': 'Lot Consistency',
                    'red': 'Profit Consistency',
                    'orange': 'Grid/Stacking',
                    'yellow': 'Martingale'
                }.get(rule_key, rule_key)
                violations_found.append(f"{rule_name}: {len(violations)} violations")

        if violations_found:
            print("\n🚨 VIOLATIONS FOUND:")
            for violation in violations_found:
                print(f"   • {violation}")

        # Save to JSON file if requested
        if args.output:
            JSONFormatter.save_to_file(results, args.output)
            if args.verbose:
                print(f"\nJSON results saved to: {args.output}")

        # Exit with appropriate code
        if decision == 'APPROVE':
            sys.exit(0)
        elif decision == 'REJECT':
            sys.exit(1)
        else:
            sys.exit(2)
    
    except ValidationError as e:
        print(f"\n❌ Validation Error: {e}", file=sys.stderr)
        sys.exit(3)

    except FileNotFoundError as e:
        print(f"\n❌ File Error: {e}", file=sys.stderr)
        sys.exit(4)

    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}", file=sys.stderr)
        if len(sys.argv) > 1 and '--verbose' in sys.argv:
            import traceback
            traceback.print_exc()
        sys.exit(5)


if __name__ == '__main__':
    main()

