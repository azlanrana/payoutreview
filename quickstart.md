## 🚀 Quick Start (1 Minute)

The system is designed for simplicity. Just point it to your trading history CSV.

```bash
# Install dependencies once
pip install -r requirements.txt

# Run analysis on your trade history CSV
# (This defaults to a $100,000 account size for the 6% cap)
python main.py your_trades.csv

# To specify a different account size (e.g., $50k)
python main.py your_trades.csv --account-size 50000
```
**That's it!** A detailed analysis report will be automatically generated and saved in the `finished_sheets` folder.

---

## 📋 What This System Does

**Automatically validates trading compliance** for payout requests by checking 4 key rules against a **6% account-based profit cap**.

| Rule | What It Checks | Severity |
|------|----------------|----------|
| 🟦 **Blue** | **Lot Consistency**: Checks if individual trades and "stacked" positions (multiple trades within 3 minutes) fall within a calculated lot size range: `Average Lot x 0.25` to `Average Lot x 2.00`. | WARNING |
| 🟥 **Red** | **Profit Consistency**: No single **day's profit** can contribute more than 40% of the total **capped profit**. Profit is calculated based on the trade's **closing day**. | BREACH |
| 🟧 **Orange** | **Grid/Stacking**: Flags **3 or more** simultaneous trades opened on the same pair and in the same direction. | BREACH |
| 🟨 **Yellow** | **Martingale**: Flags **any lot size increase** on subsequent, overlapping trades on the same pair and direction. No thresholds are used. | WARNING |

**Output:** An automated decision (APPROVE/REJECT/REVIEW) and a detailed CSV report in the `finished_sheets` folder.