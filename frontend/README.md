# Trading Compliance Validator - Web Frontend

A simple web interface for the Trading Payout Compliance System built with Streamlit.

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the frontend:**
   ```bash
   # From the project root
   python frontend/run_frontend.py

   # Or directly with streamlit
   cd frontend
   streamlit run app.py
   ```

3. **Open your browser** to `http://localhost:8501`

## 📋 How to Use

1. **Upload CSV**: Drag and drop or select your trading history CSV file
2. **Configure**: Set your account size (defaults to $100,000)
3. **Validate**: Click "🔍 Validate Trades" to run compliance analysis
4. **Review Results**: See the approval decision and detailed violation report
5. **Download**: Get your processed CSV with compliance analysis

## 📊 What You Get

- **Automated Decision**: APPROVE/REJECT/REVIEW based on compliance rules
- **Rule Analysis**: Detailed breakdown of violations by rule type
- **Color-Coded Results**: Easy-to-read violation highlighting
- **Processed CSV**: Your data with added compliance columns

## 🔧 Configuration

The frontend uses the same validation engine as the command-line version. Configure your account size in the sidebar to ensure correct payout cap calculations (6% of account size).

## 🛠️ Development

The frontend is built with:
- **Streamlit**: Web framework
- **Pandas**: Data processing
- **Existing validation engine**: Your core compliance logic

All validation logic is shared with the CLI version, ensuring consistency.
