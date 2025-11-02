# 🎯 Trading Payout Compliance System

**Automated trading compliance validation made simple.** Upload your trading data and get instant payout approval decisions.

---

## 🚀 Quick Start

### 🎯 **Simplest Option: Web Upload**
```bash
pip install -r requirements.txt
python frontend/run_frontend.py
# Open http://localhost:8501 → Upload CSV → Get Results!
```

### 🌐 **Public Web App (Share with Customers)**
1. Push to GitHub
2. Deploy on [share.streamlit.io](https://share.streamlit.io)
3. Get public URL instantly!

### 📊 **Command Line**
```bash
python main.py --csv your_trades.csv --output-csv results.csv
```

---

## 📋 What It Does

**Validates trading compliance** by checking 4 key rules:

| Rule | What It Checks | Action |
|------|----------------|--------|
| 🟦 **Blue** | Lot sizes consistent within 3 minutes | Warning |
| 🟥 **Red** | No single trade >40% of total profit | Reject |
| 🟧 **Orange** | Max 3 simultaneous trades per pair | Warning/Reject |
| 🟨 **Yellow** | No excessive lot size increases | Warning |

**Result:** APPROVE ✅ / REJECT ❌ / REVIEW ⚠️

---

## 📁 Files You Need

```
payoutcalculations/
├── main.py                       # Command line tool
├── streamlit_app.py              # Public web app
├── frontend/                     # Local web interface
├── requirements.txt              # Install with: pip install -r requirements.txt
└── src/                          # Core validation engine
```

---

## 📊 CSV Format Required

Your trading data CSV must have these columns:
```csv
ticket,open_time,close_time,pair,direction,lot_size,profit,balance,account_type,account_id
```

**Supported:** MT4/MT5 exports (automatically converted)

---

## 🎯 Usage Options

| Method | Best For | Setup Time | Access |
|--------|----------|------------|--------|
| **Web Upload** | Quick validation | 2 minutes | Local browser |
| **Public Web App** | Share with customers | 10 minutes | Public URL |
| **Command Line** | Batch processing | 2 minutes | Local terminal |
| **Google Sheets** | Team collaboration | 5 minutes | Shared sheets |

## 🎨 Results

**Color-coded decisions:**
- 🟢 **APPROVE** - All rules passed
- 🟡 **REVIEW** - Minor warnings found
- 🔴 **REJECT** - Critical violations found

**Download processed CSV** with violation details!

---

## ⚙️ Configuration

**Default 6% account cap** - automatically calculated based on account size.

**Customizable rules:**
- Time windows (default: 3 minutes)
- Profit thresholds (default: 40%)
- Lot size tolerances (default: 10%)

---

## 🎯 When to Use Each Method

### **Web Upload** (Simplest)
- ✅ Quick one-off validations
- ✅ Visual results instantly
- ✅ No technical setup needed

### **Public Web App** (Shareable)
- ✅ Send link to customers
- ✅ No installation required
- ✅ Works on any device

### **Command Line** (Batch)
- ✅ Process multiple files
- ✅ Integrate with scripts
- ✅ Automated workflows

### **Google Sheets** (Teams)
- ✅ Real-time collaboration
- ✅ Shared visibility
- ✅ Automatic updates

---

## 🎉 Ready to Start!

**Your trading compliance system is ready.** Choose your preferred method:

### **Quick Test:**
```bash
pip install -r requirements.txt
python frontend/run_frontend.py
# Open http://localhost:8501
```

### **Go Public:**
1. Push to GitHub
2. Deploy on [share.streamlit.io](https://share.streamlit.io)
3. Share the URL with customers!

---

## 💡 Key Benefits

- **⚡ Fast** - Process thousands of trades in seconds
- **🎯 Accurate** - 4 comprehensive compliance rules
- **🔒 Secure** - No data stored, read-only processing
- **📱 Accessible** - Web interface works everywhere
- **🔧 Flexible** - Multiple usage options

---

**Need help?** Check `DEPLOYMENT.md` for detailed deployment instructions.

**Happy trading compliance!** 🚀
