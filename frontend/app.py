"""Trading Compliance Validator - Web Frontend"""

import streamlit as st
import pandas as pd
from .validation_wrapper import validate_trades_csv, get_csv_download_content, get_validation_summary


def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="Trading Compliance Validator",
        page_icon="📊",
        layout="wide"
    )

    # Title and description
    st.title("🎯 Trading Payout Compliance System")
    st.markdown("""
    Upload your trading history CSV file to get automated compliance validation.
    The system will check for rule violations and provide an approval decision.
    """)

    # Sidebar with configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        account_size = st.number_input(
            "Account Size ($)",
            value=100000,
            min_value=1000,
            step=1000,
            help="Used for calculating the 6% payout cap"
        )

        st.markdown("---")
        st.markdown("""
        **Required CSV Columns:**
        - ticket, open_time, close_time, pair, direction
        - lot_size, profit, balance, account_type, account_id
        """)

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📤 Upload Your Trading Data")

        # File uploader
        uploaded_file = st.file_uploader(
            "Choose a CSV file",
            type=['csv'],
            help="Upload your trading history in CSV format"
        )

        # Validate button
        validate_button = st.button(
            "🔍 Validate Trades",
            type="primary",
            disabled=uploaded_file is None,
            use_container_width=True
        )

    with col2:
        st.subheader("📋 Validation Rules")

        # Rule descriptions
        rules = {
            "🟦 **Blue Rule**": "Lot Consistency - Trades within 3 minutes should have similar lot sizes",
            "🟥 **Red Rule**": "Profit Consistency - No single day's profit > 40% of total capped profit",
            "🟧 **Orange Rule**": "Grid Trading - Max 3 simultaneous trades on same pair",
            "🟨 **Yellow Rule**": "Martingale - No lot size increases > 1.5x on overlapping trades"
        }

        for rule_name, description in rules.items():
            with st.expander(rule_name):
                st.write(description)

    # Process uploaded file
    if uploaded_file and validate_button:
        with st.spinner("🔄 Analyzing your trading data..."):
            try:
                # Validate the trades
                results, processed_df = validate_trades_csv(uploaded_file, account_size)

                # Store results in session state for download
                st.session_state['validation_results'] = results
                st.session_state['processed_df'] = processed_df
                st.session_state['account_size'] = account_size

                # Display results
                display_validation_results(results, processed_df)

            except Exception as e:
                st.error(f"❌ Validation failed: {str(e)}")
                st.info("Please check that your CSV file has the required columns and format.")

    # Show download section if results exist
    if 'validation_results' in st.session_state:
        display_download_section()


def display_validation_results(results: dict, processed_df: pd.DataFrame):
    """Display the validation results in a user-friendly format"""

    # Get summary
    summary = get_validation_summary(results)

    # Decision banner
    decision = summary['decision']
    if decision == 'APPROVE':
        st.success("✅ **PAYOUT APPROVED** - All compliance rules passed!")
    elif decision == 'REJECT':
        st.error("❌ **PAYOUT REJECTED** - Critical violations found!")
    else:
        st.warning("⚠️ **MANUAL REVIEW REQUIRED** - Warnings detected")

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Trades", summary['total_trades'])

    with col2:
        profit_color = "inverse" if summary['cap_applied'] else "normal"
        st.metric(
            "Capped Payout",
            f"${summary['total_profit']:,.2f}",
            delta="CAP APPLIED" if summary['cap_applied'] else None,
            delta_color=profit_color
        )

    with col3:
        st.metric("Breaches", summary['breach_count'])

    with col4:
        st.metric("Warnings", summary['warning_count'])

    # Detailed results
    with st.expander("📊 Detailed Analysis", expanded=True):
        # Rule status overview
        rules = results.get('rules', {})
        rule_status_data = []

        for rule_key, rule_result in rules.items():
            rule_name = {
                'blue': 'Lot Consistency',
                'red': 'Profit Consistency',
                'orange': 'Grid Trading',
                'yellow': 'Martingale'
            }.get(rule_key, rule_key.title())

            status = rule_result.get('status', 'UNKNOWN')
            violations = rule_result.get('violation_count', 0)

            rule_status_data.append({
                'Rule': rule_name,
                'Status': status,
                'Violations': violations
            })

        if rule_status_data:
            st.table(pd.DataFrame(rule_status_data))

    # Show violations if any exist
    total_violations = summary['breach_count'] + summary['warning_count']
    if total_violations > 0:
        with st.expander("🚨 Violations Found", expanded=True):
            # Filter rows with violations
            violations_df = processed_df[processed_df['violation_type'] != ''].copy()

            if not violations_df.empty:
                # Color code the status column
                def color_status(val):
                    if val == 'BREACH':
                        return 'background-color: #ffebee; color: #c62828'
                    elif val == 'WARNING':
                        return 'background-color: #fff3e0; color: #ef6c00'
                    else:
                        return 'background-color: #e8f5e8; color: #2e7d32'

                styled_df = violations_df[['ticket', 'pair', 'direction', 'lot_size', 'profit', 'violation_type', 'rule_status']].style.applymap(
                    color_status, subset=['rule_status']
                )

                st.dataframe(styled_df, use_container_width=True)

                # Show violation details
                for _, row in violations_df.iterrows():
                    if row['violation_details']:
                        st.write(f"**Ticket {row['ticket']}:** {row['violation_details']}")


def display_download_section():
    """Display the download section for processed results"""

    st.markdown("---")
    st.subheader("📥 Download Processed Results")

    # Prepare CSV content
    processed_df = st.session_state['processed_df']
    csv_content, filename = get_csv_download_content(processed_df, "compliance_analysis")

    # Download button
    st.download_button(
        label="📊 Download Analysis CSV",
        data=csv_content,
        file_name=filename,
        mime="text/csv",
        help="Download your trading data with compliance analysis and violation details"
    )

    st.info("""
    **The downloaded CSV includes:**
    - All original trade data
    - `violation_type`: Which rules were violated
    - `violation_details`: Specific violation information
    - `rule_status`: PASS/WARNING/BREACH status
    """)


if __name__ == "__main__":
    main()
