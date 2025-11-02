# 🎯 Trading Payout Compliance System - Complete Guide

**One file to rule them all!** Everything you need to know about the automated trading compliance validation system.

---

## 🚀 Quick Start (2 Minutes)

### Option 1: CSV Files (SIMPLE - No Setup!)
```bash
# Install dependencies
pip install -r requirements.txt

# Run with sample data
python main.py --csv sample_trades.csv

# Use your own CSV
python main.py --csv your_trades.csv --output-csv results.csv
```

### Option 2: Web Frontend (SIMPLEST - 2 Minutes)
```bash
# Install and run the web interface
pip install -r requirements.txt
python frontend/run_frontend.py

# Open browser to http://localhost:8501
# Upload CSV → Get instant results!
```

### Option 3: Online Web App (PUBLIC ACCESS - 10 Minutes)
```bash
# Deploy to Streamlit Cloud (FREE!)
1. Push code to GitHub
2. Go to share.streamlit.io
3. Connect repo → Deploy
4. Get public URL instantly!

# Your customers can now access:
# https://your-app-name.streamlit.app
```

### Option 4: Google Sheets (COLLABORATIVE - 5 Minutes)
```bash
# Set up Google credentials (see Google Sheets Setup below)
# Then run:
python main.py --sheet-url "YOUR_GOOGLE_SHEET_URL"
```

---

## 📋 What This System Does

**Automatically validates trading compliance** for payout requests by checking 4 key rules:

| Rule | Color | What It Checks | Severity |
|------|-------|----------------|----------|
| 🟦 **Blue** | Lot Consistency | Trades within 3 min have similar lot sizes | WARNING |
| 🟥 **Red** | Profit Consistency | No single trade >40% of total profit (1-step-algo only) | BREACH |
| 🟧 **Orange** | Grid/Stacking | Max 3 simultaneous trades on same pair | WARNING/BREACH |
| 🟨 **Yellow** | Martingale | No lot size increases >1.5x on overlapping trades | WARNING |

**Output:** Automated decision (APPROVE/REJECT/REVIEW) with detailed reasoning.

---

## 📁 Project Structure

```
payoutcalculations/
├── 📄 UNIFIED_GUIDE.md              # This file - everything you need!
├── 🐍 main.py                       # Main entry point (CLI)
├── 🌐 streamlit_app.py              # Public web app entry point
├── 🖥️ frontend/                     # Local web interface
├── 📄 requirements.txt              # Python dependencies
├── 📄 DEPLOYMENT.md                 # Online deployment guide
├── 📁 .streamlit/                   # Streamlit configuration
├── 📁 src/                          # Source code
│   ├── models/                      # Data models
│   ├── data_access/                 # CSV & Google Sheets integration
│   ├── rules/                       # 4 compliance rules
│   ├── engine/                      # Decision logic
│   └── output/                      # JSON & Sheets output
├── 📁 finished_sheets/              # Your completed analysis results
│   ├── raw_exports/                 # Original MT4/MT5 exports
│   ├── processed_results/           # Color-coded analysis results
│   ├── google_sheets/              # Google Sheets with color coding
│   └── reports/                    # Summary reports
└── 📁 config/                       # Google API credentials (if using Sheets)
```

---

## 🎯 How to Use

### CSV Mode (Recommended for Getting Started)

#### 1. Create Your CSV File
Your CSV needs these **exact columns**:
```csv
ticket,open_time,close_time,pair,direction,lot_size,profit,balance,account_type,account_id
12345,2025-01-15 10:00:00,2025-01-15 11:00:00,EURUSD,BUY,0.5,50.00,5050.00,1-step-algo,ACC-001
```

#### 2. Run Validation
```bash
# Basic validation
python main.py --csv trades.csv

# Save results to CSV
python main.py --csv trades.csv --output-csv results.csv

# Save results to JSON
python main.py --csv trades.csv --output results.json

# Verbose mode (see details)
python main.py --csv trades.csv --verbose
```

#### 3. View Results
- **Console**: JSON output with decision
- **CSV File**: Detailed results table
- **JSON File**: Structured data for integration

---

### Google Sheets Mode (For Teams)

#### 1. Set Up Google Sheets API
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project → Enable Google Sheets API
3. Create service account → Download JSON key
4. Save as `config/service_account.json`
5. Share your sheet with service account email

#### 2. Prepare Your Sheet
Create two tabs:

**"Trades" Tab** (Required):
| ticket | open_time | close_time | pair | direction | lot_size | profit | balance | account_type | account_id |
|--------|-----------|------------|------|-----------|----------|--------|---------|--------------|------------|
| 12345 | 2025-01-15 10:00:00 | 2025-01-15 11:00:00 | EURUSD | BUY | 0.5 | 50.00 | 5050.00 | 1-step-algo | ACC-001 |

**"Config" Tab** (Optional):
| Parameter | Value |
|-----------|-------|
| blue_time_window | 180 |
| blue_lot_tolerance | 0.10 |
| red_profit_threshold | 0.40 |

#### 3. Run Validation
```bash
python main.py --sheet-url "YOUR_SHEET_URL"
```

#### 4. View Results
- **Console**: JSON output
- **Google Sheet**: New "Results" tab with formatted summary
- **Optional**: "Colored Trades" tab with violation highlighting

---

## 🎨 Color-Coded Output

### CSV Files
When you use `--colored-trades`, your CSV gets 3 new columns:
- `violation_type` - Which rule was broken
- `violation_details` - Specific violation info  
- `rule_status` - PASS/WARNING/BREACH

### Google Sheets
When you use `--colored-sheets`, you get:
- **"Results" Tab**: Colored cells showing rule status
- **"Colored Trades" Tab**: All trades with row highlighting

**Color Meanings:**
- 🟢 **Green**: PASS/APPROVE (no issues)
- 🟡 **Yellow**: WARNING/REVIEW (minor violations)
- 🔴 **Red**: BREACH/REJECT (major violations)

---

## 📊 Sample Output

### Console Output
```json
{
  "trader_id": "ACC-001",
  "account_id": "ACC-001", 
  "account_type": "1-step-algo",
  "recommendation": "APPROVE",
  "decision_reason": "All compliance rules passed",
  "rules": {
    "blue": {"status": "PASS", "violation_count": 0},
    "red": {"status": "PASS", "violation_count": 0},
    "orange": {"status": "PASS", "violation_count": 0},
    "yellow": {"status": "PASS", "violation_count": 0}
  },
  "summary": {
    "total_trades": 47,
    "total_profit": 2500.00,
    "breach_count": 0,
    "warning_count": 0,
    "pass_count": 4
  }
}
```

### Decision Logic
| Condition | Decision | Action |
|-----------|----------|--------|
| All rules PASS | ✅ **APPROVE** | Auto-approve payout |
| Red Rule FAIL | ❌ **REJECT** | Single trade >40% profit - deny payout |
| Orange Rule BREACH (5+ grid) | ❌ **REJECT** | Excessive grid trading - deny payout |
| Blue/Yellow only (WARNING) | ⚠️ **REVIEW** | Manual review, possible deduction |

---

## 🔧 Configuration

### Default Settings
```python
blue_time_window = 180          # 3 minutes
blue_lot_tolerance = 0.10       # 10%
red_profit_threshold = 0.40     # 40%
orange_simultaneous_trades = 3  # minimum for grid detection
yellow_lot_multiplier = 1.5     # 1.5x lot increase
```

### Custom Configuration
**CSV Mode**: Create `config.csv`:
```csv
Parameter,Value
blue_time_window,300
red_profit_threshold,0.35
```

**Google Sheets Mode**: Add "Config" tab to your sheet.

---

## 🚀 Advanced Features

### MT4/MT5 Format Support
The system automatically detects and converts MT4/MT5 export format:
- Tab-separated values
- Column mapping (Position → ticket, Time → open_time, etc.)
- Automatic close_time detection
- Filters out empty rows

### Multiple Output Formats
```bash
# Console only
python main.py --csv trades.csv

# Save to CSV
python main.py --csv trades.csv --output-csv results.csv

# Save to JSON
python main.py --csv trades.csv --output results.json

# Google Sheets with colors
python main.py --sheet-url "..." --colored-sheets

# All outputs together
python main.py --csv trades.csv --output results.json --colored-trades highlighted.csv
```

### Exit Codes
| Code | Meaning |
|------|---------|
| 0 | APPROVE - Payout approved |
| 1 | REJECT - Payout rejected (breach) |
| 2 | REVIEW - Manual review required (warnings) |
| 3 | Validation error (bad data) |
| 4 | File not found error |
| 5 | Unexpected error |

---

## 🐛 Troubleshooting

### Common Errors

**"ModuleNotFoundError"**
```bash
# Solution: Install dependencies
pip install -r requirements.txt
```

**"CSV file not found"**
```bash
# Check file exists
ls -la trades.csv
# Use absolute path
python main.py --csv /full/path/to/trades.csv
```

**"Missing required fields"**
- Check your CSV has all 10 columns with exact names
- Column names must be: `ticket,open_time,close_time,pair,direction,lot_size,profit,balance,account_type,account_id`

**"close_time must be after open_time"**
- Use format: `YYYY-MM-DD HH:MM:SS`
- Example: `2025-01-15 10:00:00`

**"Google service account credentials not found"**
- Ensure `config/service_account.json` exists
- Check the file path is correct

**"Failed to access Google Sheet"**
- Verify sheet URL is correct
- Ensure sheet is shared with service account email
- Grant "Editor" permissions

---

## 📈 Performance & Limits

- **Processing Time**: < 10 seconds for 1000+ trades
- **Algorithm Complexity**: O(n) for most rules
- **Memory Efficient**: Processes trades in-memory
- **Scalable**: Can handle large datasets

---

## 🔒 Security

- **Service account credentials** never committed to git
- Trade data is **read-only**, never stored permanently
- Results written back to trader's own sheet
- Minimal API scopes (read/write sheets only)

---

## 🎯 When to Use Each Method

### Use Web Frontend When:
- ✅ **Simplest option** - Just upload and download!
- ✅ Need instant visual feedback
- ✅ Non-technical users
- ✅ Quick validation without setup
- ✅ Working offline (local server)

### Use CSV When:
- ✅ Testing locally
- ✅ Quick one-off validations
- ✅ No team collaboration needed
- ✅ Want simplest setup
- ✅ Working offline

### Use Google Sheets When:
- ✅ Team needs access
- ✅ Want automatic result updates
- ✅ Building automated workflows
- ✅ Need shared visibility
- ✅ Integrating with other systems

**Pro Tip:** Use CSV for development/testing, Google Sheets for production!

---

## 📚 Quick Reference

### Essential Commands
```bash
# 🌐 ONLINE WEB APP (Public Access!)
# 1. Push to GitHub
# 2. Deploy: share.streamlit.io
# Result: https://your-app.streamlit.app

# 🖥️ LOCAL WEB FRONTEND
python frontend/run_frontend.py  # Then upload CSV in browser

# 🖥️ PUBLIC WEB APP (Local test)
streamlit run streamlit_app.py   # Test before deploying

# Test with sample data (CLI)
python main.py --csv sample_trades.csv

# Your own data
python main.py --csv trades.csv --output-csv results.csv

# Google Sheets
python main.py --sheet-url "YOUR_SHEET_URL"
```

### File Formats
- **CSV Input**: Standard CSV with 10 required columns
- **MT4/MT5**: Automatically detected and converted
- **JSON Output**: Structured validation results
- **CSV Output**: Detailed results table with violation highlighting

---

## 🎉 Success!

**You now have everything you need to:**
1. ✅ Validate trading compliance automatically
2. ✅ Get clear APPROVE/REJECT/REVIEW decisions
3. ✅ Use either CSV files or Google Sheets
4. ✅ See color-coded violation highlighting
5. ✅ Customize rule thresholds
6. ✅ Integrate with your workflow

**Ready to start?** Run: `python main.py --csv sample_trades.csv`

---

**Version**: 1.0.0  
**Status**: ✅ Production Ready  
**Last Updated**: October 20, 2025
