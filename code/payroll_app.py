"""
payroll_app.py — the weekly payroll, for someone who has never opened a terminal.

Every Friday the office manager at Salt City Coffee exports the week's timesheet
from the point-of-sale system. This page turns it into a paycheck table and the
CSV the online payroll provider imports — without the manager touching pandas.

The app is mostly *assembly*: the roster is loaded from data/, the upload comes
from the page, and one call to `build_payroll` does all the work. What the page
adds is what a manager needs to trust the numbers: totals, a loud warning about
anything the pipeline could not match, the full lineage table, and the download.

Run it:  Run and Debug -> "Streamlit Run: Current File"   (see README Reference #1)
Test it: pytest tests/test_pipeline.py -k app
"""

# --- The page ---------------------------------------------------------------------
#
# No scaffolding. Every function this page needs already exists in the payroll
# package, and every widget it needs you used in Assignment 03. README Step 8 has
# the exact widgets, keys and labels; the tests in tests/test_pipeline.py -k app
# check them.
#
# The shape, in words:
#
#   title and a sentence of instructions
#   roster  <- load_employees()                      (fixed; not uploaded)
#   upload  <- st.file_uploader, key="timesheet"     (returns None until chosen)
#   if there is an upload:
#       timesheet <- load_timesheet(upload)
#       payroll   <- build_payroll(timesheet, roster)   one call does all the work
#       the pay period (payroll_date) as a subheader
#       four st.metric cards in st.columns(4) — totals are .sum() on a Series,
#           counts are len() of a boolean-indexed frame
#       st.warning naming the unmatched employee_ids, or st.success if none
#       st.dataframe(payroll) — the lineage table, raw and computed side by side
#       st.download_button, key="download": payroll_export(payroll).to_csv(index=False)
#
# What the page does NOT do: arithmetic on rows, cleaning, merging. If you find
# yourself writing a loop or an apply here, that logic belongs in the package.

import streamlit as st
from payroll import load_timesheet, load_employees, build_payroll, payroll_export

st.title("Salt City Coffee — Weekly Payroll")

timesheet_file = st.file_uploader("Upload the week's timesheet CSV", type=["csv"])

if timesheet_file is not None:
    timesheet = load_timesheet(timesheet_file)
    employees = load_employees()
    payroll = build_payroll(timesheet, employees)

    payroll_date = payroll['payroll_date'].iloc[0] if 'payroll_date' in payroll.columns and not payroll.empty else "unknown"
    st.write(f"Pay Period: {payroll_date}")
 
    st.metric("Employees paid", payroll.loc[payroll['pay_type'] != "unmatched", 'employee_id'].nunique())
    st.metric("Total hours", round(payroll['hours_worked'].sum(), 2))
    st.metric("Total gross pay", f"${payroll['gross_pay'].sum():,.2f}")
    st.metric("Overtime weeks", payroll[payroll['pay_type'] == "overtime"].shape[0])
    unmatched = payroll[payroll['pay_type'] == "unmatched"]
    if not unmatched.empty:
        unmatched_ids = unmatched['employee_id'].unique()
        st.warning(f"Unmatched employee IDs: {', '.join(unmatched_ids)}")
    else:
        st.success("No unmatched employees found.")

    st.dataframe(payroll)

    export_df = payroll_export(payroll)
    payroll_date = payroll['payroll_date'].iloc[0] if not payroll.empty else "unknown"
    csv = export_df.to_csv(index=False)
    st.download_button(
        label="Download payroll CSV",
        data=csv,
        file_name=f"payroll_{payroll_date}.csv",
        mime="text/csv"
    )
