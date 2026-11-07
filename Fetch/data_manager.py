"""Manage Ingested Data: row removal, time filtering, decluttering, and timezone conversion."""
import pandas
import streamlit as st

from fetch.i18n import t
from fetch.utils import csv_bytes, fingerprint, safe_session_get, safe_session_set, session_memo


def prepare_datetime_column(df, date_column):
    """Prepare datetime column with proper conversion and caching for performance"""
    df_copy = df.copy()
    try:
        df_copy[date_column] = pandas.to_datetime(df_copy[date_column])
    except ValueError:
        # Handle GPX UTC inputs
        df_copy[date_column] = pandas.to_datetime(df_copy[date_column], utc=True)
        df_copy[date_column] = df_copy[date_column].dt.tz_convert('UTC')
    except Exception:
        # Coerce errors to NaT for invalid dates
        df_copy[date_column] = pandas.to_datetime(df_copy[date_column], errors='coerce')
    
    # Remove rows with invalid dates
    df_copy = df_copy.dropna(subset=[date_column])
    return df_copy


def detect_datetime_columns_by_source(df):
    """Detect potential datetime columns for each source file"""
    datetime_mapping = {}
    
    if 'SOURCE_FILE' in df.columns:
        for source_file in df['SOURCE_FILE'].unique():
            source_data = df[df['SOURCE_FILE'] == source_file]
            
            # Look for datetime-like column names
            datetime_candidates = []
            for col in source_data.columns:
                if col in ['SOURCE_FILE', 'POINT_COLOR', 'LATITUDE', 'LONGITUDE']:
                    continue
                col_upper = col.upper()
                if any(keyword in col_upper for keyword in ['TIME', 'DATE', 'TIMESTAMP', 'DATETIME']):
                    datetime_candidates.append(col)
            
            # Test each candidate for actual datetime data
            valid_datetime_cols = []
            for col in datetime_candidates:
                try:
                    test_data = source_data[col].dropna().head(10)
                    if len(test_data) > 0:
                        pandas.to_datetime(test_data)
                        valid_datetime_cols.append(col)
                except Exception:
                    continue
            
            datetime_mapping[source_file] = {
                'candidates': datetime_candidates,
                'valid': valid_datetime_cols
            }
    
    return datetime_mapping


def create_unified_datetime_column(df, datetime_mapping):
    """Create a unified UNIFIED_DATETIME column from multiple source columns"""
    df_copy = df.copy()
    df_copy['UNIFIED_DATETIME'] = pandas.NaT
    processed_files = []
    
    for source_file, datetime_col in datetime_mapping.items():
        if datetime_col and datetime_col != 'Skip this file':
            source_mask = df_copy['SOURCE_FILE'] == source_file
            source_data = df_copy.loc[source_mask, datetime_col]
            
            # Try multiple parsing strategies
            converted_dates = None
            strategy_used = None
            
            strategies = [
                ('Standard parsing', lambda x: pandas.to_datetime(x)),
                ('UTC parsing', lambda x: pandas.to_datetime(x, utc=True)),
                ('Inferred format', lambda x: pandas.to_datetime(x, format='mixed')),
                ('Standard format', lambda x: pandas.to_datetime(x, format='%Y-%m-%d %H:%M:%S')),
                ('US format', lambda x: pandas.to_datetime(x, format='%m/%d/%Y %H:%M:%S')),
                ('ISO format', lambda x: pandas.to_datetime(x, format='%Y-%m-%dT%H:%M:%S')),
            ]
            
            for strategy_name, strategy_func in strategies:
                try:
                    converted_dates = strategy_func(source_data)
                    strategy_used = strategy_name
                    break
                except Exception:
                    continue
            
            if converted_dates is not None:
                df_copy.loc[source_mask, 'UNIFIED_DATETIME'] = converted_dates
                processed_files.append(f"{source_file} ({strategy_used})")
            else:
                st.error(f"Could not parse datetime data from {source_file} column {datetime_col}")
    
    if processed_files:
        st.success(f"Successfully processed datetime data from: {', '.join(processed_files)}")
    
    return df_copy


def multi_source_time_filter_config(df):
    """Configure datetime columns for multiple source files"""
    if 'SOURCE_FILE' not in df.columns:
        return None
    
    source_files = df['SOURCE_FILE'].unique()
    st.subheader(t("hdr_multisource_time"))
    st.info(f"You have {len(source_files)} source files. Configure datetime columns for each file:")
    
    datetime_mapping_detected = detect_datetime_columns_by_source(df)
    datetime_column_mapping = {}
    
    for i, source_file in enumerate(source_files):
        st.markdown(f"**File: {source_file}**")
        source_data = df[df['SOURCE_FILE'] == source_file]
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Show sample data
            st.write("Sample data:")
            display_cols = [col for col in source_data.columns if col not in ['POINT_COLOR']][:6]
            st.dataframe(source_data[display_cols].head(2), width="stretch")
        
        with col2:
            # Show detected datetime candidates
            detected_info = datetime_mapping_detected.get(source_file, {})
            if detected_info.get('valid'):
                st.write("Detected datetime columns:")
                for col in detected_info['valid']:
                    st.write(f"✓ {col}")
            elif detected_info.get('candidates'):
                st.write("Potential datetime columns:")
                for col in detected_info['candidates']:
                    st.write(f"? {col}")
            else:
                st.write("No datetime columns detected")
        
        # Column selection
        all_columns = ['Skip this file'] + [col for col in source_data.columns if col not in ['SOURCE_FILE', 'POINT_COLOR']]
        
        # Pre-select the best candidate if available
        default_index = 0
        if detected_info.get('valid'):
            best_candidate = detected_info['valid'][0]
            if best_candidate in all_columns:
                default_index = all_columns.index(best_candidate)
        
        datetime_col = st.selectbox(
            f"Select datetime column for {source_file}",
            options=all_columns,
            index=default_index,
            key=f"datetime_col_{source_file}_{i}"
        )
        
        if datetime_col != 'Skip this file':
            datetime_column_mapping[source_file] = datetime_col
            
            # Test the column
            try:
                test_data = source_data[datetime_col].dropna().head(5)
                if len(test_data) > 0:
                    test_conversion = pandas.to_datetime(test_data)
                    st.success(f"✓ Valid datetime format detected")
                    st.write(f"Sample: {test_conversion.iloc[0]}")
                else:
                    st.warning("No data found in this column")
            except Exception as e:
                st.warning(f"Potential parsing issue: {str(e)[:100]}")
        else:
            st.info("This file will be skipped during time filtering")
        
        st.markdown("---")
    
    return datetime_column_mapping


def display_filter_results(filtered_df, original_df):
    """Display filter results with metrics and sample data"""
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Filtered Records", len(filtered_df))
    with col2:
        st.metric("Original Records", len(original_df))
    with col3:
        if len(original_df) > 0:
            percentage = (len(filtered_df) / len(original_df)) * 100
            st.metric("✅ Retained", f"{percentage:.1f}%")
        else:
            st.metric("✅ Retained", "0%")
    
    # Show sample of results instead of full table
    if len(filtered_df) > 0:
        st.subheader(t("hdr_sample_filtered"))
        # Show first 10 rows with better formatting
        sample_df = filtered_df.head(10)
        st.dataframe(sample_df, width="stretch")
        
        if len(filtered_df) > 10:
            st.info(f"ℹShowing first 10 of {len(filtered_df):,} records")
        
        st.download_button(
            label=t("btn_download_csv"),
            data=csv_bytes(filtered_df, index=False),
            file_name="filtered_data.csv",
            mime="text/csv",
            on_click="ignore",
        )
    else:
        st.warning("⚠️ No records match the selected time range")


def time_filter(in_df, date_column_or_mapping, fp):
    """Time filter UI for single and multi-source data; returns (filtered_df, fingerprint).

    Datetime parsing and filtering are memoized on the input fingerprint and settings,
    so unrelated reruns don't re-parse or re-filter the dataset.
    """
    st.subheader(t("hdr_time_filter"))
    
    try:
        # Handle multi-source vs single-source scenarios
        if isinstance(date_column_or_mapping, dict):
            # Multi-source: create unified datetime column
            st.info("Processing multi-source data with unified datetime column...")
            prep_key = repr(sorted(date_column_or_mapping.items()))
            df_with_datetime = session_memo(
                "time_prepare", (fp, prep_key),
                lambda: create_unified_datetime_column(in_df, date_column_or_mapping))
            
            # Check if any data was successfully processed
            valid_datetime_count = df_with_datetime['UNIFIED_DATETIME'].notna().sum()
            if valid_datetime_count == 0:
                st.error("No valid datetime records found across all source files")
                return in_df, fp
            
            date_column = 'UNIFIED_DATETIME'
            st.success(f"Created unified datetime column with {valid_datetime_count:,} valid records")
            
        else:
            # Single source: use existing logic
            prep_key = repr(date_column_or_mapping)
            df_with_datetime = session_memo(
                "time_prepare", (fp, prep_key),
                lambda: prepare_datetime_column(in_df, date_column_or_mapping))
            date_column = date_column_or_mapping
            
            if len(df_with_datetime) == 0:
                st.error("No valid datetime records found in the selected column")
                return in_df, fp
        
        # Data range info
        min_date = df_with_datetime[date_column].min()
        max_date = df_with_datetime[date_column].max()
        total_span = max_date - min_date
        
        # Info panel
        st.subheader(t("hdr_time_range_info"))
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Earliest Record", min_date.strftime("%Y-%m-%d %H:%M"))
        with col2:
            st.metric("Latest Record", max_date.strftime("%Y-%m-%d %H:%M"))
        with col3:
            st.metric("Total Span", f"{total_span.days} days")
        
        # Quick filters
        st.subheader(t("hdr_quick_filters"))
        st.info(f"Preset ranges are calculated from your data's latest record: {max_date.strftime('%Y-%m-%d %H:%M')}")
        
        _qf_en = ["All Data", "Last 24 Hours", "Last Week", "Last Month", "Custom Range"]
        _qf_tr = [t("qf_all_data"), t("qf_24h"), t("qf_week"), t("qf_month"), t("qf_custom")]
        _qf_sel = st.radio(t("lbl_quick_filter"), _qf_tr, horizontal=True, key="time_filter_quick")
        quick_filter = _qf_en[_qf_tr.index(_qf_sel)]
        
        # Set date range based on selection (relative to dataset's max_date)
        if quick_filter == "All Data":
            start_dt, end_dt = min_date, max_date
        elif quick_filter == "Last 24 Hours":
            end_dt = max_date
            start_dt = max_date - pandas.Timedelta(days=1)
            start_dt = max(start_dt, min_date)  # Don't go before dataset start
        elif quick_filter == "Last Week":
            end_dt = max_date
            start_dt = max_date - pandas.Timedelta(weeks=1)
            start_dt = max(start_dt, min_date)  # Don't go before dataset start
        elif quick_filter == "Last Month":
            end_dt = max_date
            start_dt = max_date - pandas.Timedelta(days=30)
            start_dt = max(start_dt, min_date)  # Don't go before dataset start
        
        # Show selected date range for preset filters
        if quick_filter != "Custom Range":
            st.success(f"Selected range: {start_dt.strftime('%Y-%m-%d %H:%M')} to {end_dt.strftime('%Y-%m-%d %H:%M')}")
            if start_dt == min_date and quick_filter != "All Data":
                st.info("Note: Range limited to dataset start date")
        
        else:  # Custom Range
            st.subheader("Custom Date Range")
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Start Date & Time**")
                start_date = st.date_input(
                    "Start Date", 
                    value=min_date.date(),
                    min_value=min_date.date(),
                    max_value=max_date.date(),
                    key="time_filter_start_date"
                )
                start_time = st.time_input(
                    "Start Time",
                    value=min_date.time(),
                    key="time_filter_start_time"
                )
                start_dt = pandas.Timestamp.combine(start_date, start_time)
            with col2:
                st.write("**End Date & Time**")
                end_date = st.date_input(
                    "End Date", 
                    value=max_date.date(),
                    min_value=min_date.date(),
                    max_value=max_date.date(),
                    key="time_filter_end_date"
                )
                end_time = st.time_input(
                    "End Time",
                    value=max_date.time(),
                    key="time_filter_end_time"
                )
                end_dt = pandas.Timestamp.combine(end_date, end_time)
            
            # Validation for custom range
            if start_dt >= end_dt:
                st.error("❌ Start date must be before end date")
                return in_df, fp
        
        # Apply filter
        out_fp = fingerprint(fp, "time", prep_key, start_dt, end_dt)
        filtered_df = session_memo("time_filter", out_fp, lambda: df_with_datetime[
            (df_with_datetime[date_column] >= start_dt) &
            (df_with_datetime[date_column] <= end_dt)
        ])
        
        # Display results
        st.subheader(t("hdr_filter_results"))
        display_filter_results(filtered_df, df_with_datetime)
        
        return filtered_df, out_fp

    except Exception as e:
        st.error(f"❌ Error processing time filter: {str(e)}")
        st.error("Please ensure the selected column contains valid date/time data. Remove any non-date addons such as UTC+3")
        return in_df, fp



# ---------------------------------------------------------------------------------------------
# Declutter (time-interval averaging)
# ---------------------------------------------------------------------------------------------
# Offset classes work across pandas versions (string aliases like "T"/"H"/"M"/"A" were removed in pandas 3).
TIME_INTERVALS = {
    "🟢 Minute": pandas.offsets.Minute,
    "🔵 Hour": pandas.offsets.Hour,
    "🟡 Day": pandas.offsets.Day,
    "🟠 Week": lambda n: pandas.offsets.Week(n, weekday=6),  # same as "W" (weeks ending Sunday)
    "🔴 Month": pandas.offsets.MonthEnd,
    "🟤 Year": pandas.offsets.YearEnd,
}


def _declutter(in_df: pandas.DataFrame, date_column: str, interval: str, count: int) -> pandas.DataFrame:
    df_copy = in_df[[date_column, 'LATITUDE', 'LONGITUDE']].copy()
    df_copy[date_column] = pandas.to_datetime(df_copy[date_column])
    df_copy['LATITUDE'] = pandas.to_numeric(df_copy['LATITUDE'], errors='coerce')
    df_copy['LONGITUDE'] = pandas.to_numeric(df_copy['LONGITUDE'], errors='coerce')
    declutter_data = df_copy.set_index(date_column).resample(TIME_INTERVALS[interval](int(count))).agg({
        'LATITUDE': 'mean',
        'LONGITUDE': 'mean'
    })
    declutter_data = declutter_data[declutter_data['LATITUDE'].notna()]
    return declutter_data.reset_index()


def declutterer(in_df, date_column, fp):
    """Declutter UI; returns (df, fingerprint). Resampling is memoized on input and settings."""
    st.subheader(t("hdr_declutter"))

    try:
        if 'LATITUDE' not in in_df.columns or 'LONGITUDE' not in in_df.columns:
            st.error("❌ LATITUDE and LONGITUDE columns are required for decluttering")
            return in_df, fp
        if date_column in ('LATITUDE', 'LONGITUDE'):
            st.error("❌ Choose a date/time column for grouping (not a coordinate column).")
            return in_df, fp

        total_records = len(in_df)
        st.info(f"Processing {total_records:,} records for decluttering")

        col1, col2 = st.columns([1, 2])
        with col1:
            count_of_time = st.number_input(
                "Interval Count",
                min_value=1,
                max_value=60,
                value=1,
                help="Number of time units to group together"
            )
        with col2:
            choose_interval = st.selectbox(
                "Time Unit",
                options=list(TIME_INTERVALS.keys()),
                help="Time period for grouping locations"
            )

        interval_name = choose_interval.split(" ", 1)[1]  # Remove emoji
        st.info(f"Grouping locations every **{count_of_time} {interval_name.lower()}{'s' if count_of_time > 1 else ''}**")

        out_fp = fingerprint(fp, "declutter", date_column, choose_interval, int(count_of_time))
        with st.spinner("Processing declutter operation..."):
            declutter_data = session_memo(
                "declutter", out_fp,
                lambda: _declutter(in_df, date_column, choose_interval, int(count_of_time)))

        final_count = len(declutter_data)
        reduction_pct = ((total_records - final_count) / total_records) * 100 if total_records > 0 else 0

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Original Records", f"{total_records:,}")
        with col2:
            st.metric("Averaged Locations", f"{final_count:,}")
        with col3:
            st.metric("Reduction", f"{reduction_pct:.1f}%")

        if final_count > 0:
            st.success(f"✅ Successfully consolidated {total_records:,} records into {final_count:,} averaged locations")
        else:
            st.warning("⚠️ No data remains after decluttering. Try a larger time interval.")
            return in_df, fp

        return declutter_data, out_fp

    except Exception as e:
        st.error(f"❌ Error during decluttering: {str(e)}")
        st.error("Please ensure the selected column contains valid date/time data.Remove any non-date addons such as UTC+3")
        return in_df, fp


# ---------------------------------------------------------------------------------------------
# Timezone conversion
# ---------------------------------------------------------------------------------------------
COMMON_TIMEZONES = [
    'UTC', 'US/Eastern', 'US/Central', 'US/Mountain', 'US/Pacific', 'US/Alaska', 'US/Hawaii',
    'Europe/London', 'Europe/Paris', 'Europe/Berlin', 'Asia/Tokyo', 'Asia/Shanghai',
    'Australia/Sydney', 'Australia/Melbourne',
]
TZ_STATE_KEY = "_fetch_tz_conversion"


def detect_datetime_columns(df: pandas.DataFrame) -> list:
    """Columns whose first non-null value parses as a date/time, or that already have a datetime dtype."""
    datetime_columns = []
    for col in df.columns:
        if pandas.api.types.is_datetime64_any_dtype(df[col]):
            datetime_columns.append(col)
        elif not pandas.api.types.is_numeric_dtype(df[col]) and not pandas.api.types.is_bool_dtype(df[col]):
            try:
                sample_values = df[col].dropna().head(5)
                if len(sample_values) > 0:
                    pandas.to_datetime(sample_values.iloc[0])
                    datetime_columns.append(col)
            except Exception:
                pass
    return datetime_columns


def _convert_timezone(df: pandas.DataFrame, settings: dict) -> pandas.DataFrame:
    column = settings['column']
    dt_series = pandas.to_datetime(df[column])
    if settings['method'] == "Timezone Conversion":
        source_tz = settings['source_tz']
        if source_tz == 'Auto-detect':
            # If no timezone info, assume UTC
            if dt_series.dt.tz is None:
                dt_series = dt_series.dt.tz_localize('UTC')
        elif dt_series.dt.tz is None:
            dt_series = dt_series.dt.tz_localize(source_tz)
        else:
            dt_series = dt_series.dt.tz_convert(source_tz)
        converted_series = dt_series.dt.tz_convert(settings['target_tz'])
    else:  # Hourly Offset
        if dt_series.dt.tz is not None:
            dt_series = dt_series.dt.tz_localize(None)
        converted_series = dt_series + pandas.Timedelta(hours=settings['hour_offset'])
    return df.assign(**{column: converted_series})


def _describe_tz(settings: dict) -> str:
    if settings['method'] == "Timezone Conversion":
        return f"{settings['column']} from {settings['source_tz']} to {settings['target_tz']}"
    return f"{settings['hour_offset']:+.1f} hour offset to {settings['column']}"


def _preview_conversion(df: pandas.DataFrame, settings: dict):
    sample_data = df[settings['column']].dropna().head(3)
    if len(sample_data) == 0:
        st.warning("No valid datetime values found in selected column")
        return
    st.write("**Sample Conversion Preview:**")
    preview_results = []
    for original_value in sample_data:
        try:
            converted = _convert_timezone(pandas.DataFrame({settings['column']: [original_value]}), settings)
            row = {'Original': str(original_value)}
            if settings['method'] == "Hourly Offset":
                row['Hour Offset'] = f"{settings['hour_offset']:+.1f} hours"
            row['Converted'] = str(converted[settings['column']].iloc[0])
            preview_results.append(row)
        except Exception as e:
            preview_results.append({'Original': str(original_value), 'Error': str(e), 'Converted': 'Error'})
    st.dataframe(pandas.DataFrame(preview_results), width="stretch")


def timezone_conversion(in_df, fp, dataset_key):
    """Timezone conversion UI; an applied conversion persists until cleared or new data is loaded."""
    st.subheader(t("hdr_timezone"))
    applied = safe_session_get(TZ_STATE_KEY)
    if applied and applied.get('dataset') != dataset_key:
        applied = None
        safe_session_set(TZ_STATE_KEY, None)

    datetime_columns = session_memo("tz_detect", fp, lambda: detect_datetime_columns(in_df))
    if not datetime_columns:
        st.info("No datetime columns detected in the data. Upload data with datetime information to use timezone conversion.")
    else:
        st.info("Convert datetime columns using timezone names (with daylight savings) or simple hourly offsets.")
        tz_column = st.selectbox(
            "Select DateTime Column to Convert",
            options=datetime_columns,
            help="Choose the datetime column you want to convert to a different timezone"
        )
        _cm_en = ["Timezone Conversion", "Hourly Offset"]
        _cm_tr = [t("conv_timezone"), t("conv_offset")]
        _cm_sel = st.radio(
            t("lbl_conversion_method"),
            options=_cm_tr,
            help="Choose between timezone-aware conversion (handles DST) or simple hourly offset"
        )
        settings = {'column': tz_column, 'method': _cm_en[_cm_tr.index(_cm_sel)], 'dataset': dataset_key}
        if settings['method'] == "Timezone Conversion":
            col1, col2 = st.columns(2)
            with col1:
                settings['source_tz'] = st.selectbox(
                    "Source Timezone",
                    options=['Auto-detect'] + COMMON_TIMEZONES,
                    help="Current timezone of the data. Auto-detect will try to determine automatically."
                )
            with col2:
                settings['target_tz'] = st.selectbox(
                    "Convert to Timezone",
                    options=COMMON_TIMEZONES,
                    index=1,  # Default to US/Eastern
                    help="Target timezone for conversion"
                )
        else:
            st.info("💡 Positive values add hours (e.g., +3 for 3 hours ahead), negative values subtract hours (e.g., -5 for 5 hours behind)")
            settings['hour_offset'] = st.number_input(
                "Hour Offset",
                min_value=-12.0,
                max_value=14.0,
                value=0.0,
                step=0.5,
                help="Number of hours to add (+) or subtract (-) from the datetime. Supports half-hour increments."
            )

        if st.button(t("btn_preview_conversion")):
            try:
                _preview_conversion(in_df, settings)
            except Exception as e:
                st.error(f"Error during conversion preview: {str(e)}")

        if st.button(t("btn_apply_conversion"), type="primary"):
            applied = settings
            safe_session_set(TZ_STATE_KEY, settings)

    if not applied:
        return in_df, fp
    if applied['column'] not in in_df.columns:
        st.warning(f"Timezone conversion of {applied['column']} is not applied: the column is no longer present.")
        return in_df, fp
    out_fp = fingerprint(fp, "tz", sorted(applied.items()))
    try:
        with st.spinner("Converting datetime..."):
            converted = session_memo("tz_convert", out_fp, lambda: _convert_timezone(in_df, applied))
    except Exception as e:
        st.error(f"Error during conversion: {str(e)}")
        return in_df, fp
    st.success(f"✅ Applied conversion: {_describe_tz(applied)}")
    st.button("Clear timezone conversion", on_click=safe_session_set, args=(TZ_STATE_KEY, None))
    return converted, out_fp


# ---------------------------------------------------------------------------------------------
# Manage Ingested Data panel
# ---------------------------------------------------------------------------------------------
TIME_MAPPING_KEY = "_fetch_time_mapping"


def _review_tab(df, fp):
    st.subheader(t("hdr_review_data"))
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Records", f"{len(df):,}")
    with col2:
        st.metric("Columns", len(df.columns))
    with col3:
        if 'SOURCE_FILE' in df.columns:
            st.metric("Source Files", df['SOURCE_FILE'].nunique())
        else:
            st.metric("Source Files", 1)

    st.subheader(t("hdr_header_cleaning"))
    lines_t0_remove = st.slider(
        label="Number of Rows to Remove from Start",
        min_value=0,
        max_value=10,
        value=0,
        help="Remove header rows or unwanted data from the beginning of your dataset. First remaining row should contain 'Latitude' and 'Longitude' data."
    )
    if lines_t0_remove > 0:
        st.info(f"ℹRemoving the first {lines_t0_remove} row{'s' if lines_t0_remove > 1 else ''} from the dataset")

    st.subheader(t("hdr_data_preview"))
    display_data = df.iloc[lines_t0_remove:] if lines_t0_remove > 0 else df
    if len(display_data) > 0:
        st.dataframe(display_data.head(10), width="stretch")
        if len(display_data) > 10:
            st.info(f"ℹShowing first 10 rows of {len(display_data):,} total records")
        if st.checkbox(t("chk_show_col_info"), value=False):
            st.dataframe(session_memo("column_info", fingerprint(fp, lines_t0_remove),
                                      lambda: _column_info(display_data)), width="stretch")
    else:
        st.warning("⚠️ No data available to preview")

    if lines_t0_remove > 0:
        st.success(f"✅ Applied row removal: {lines_t0_remove} rows removed from dataset")
        return display_data, fingerprint(fp, "rows", lines_t0_remove)
    return df, fp


def _column_info(df):
    non_null = df.count()
    return pandas.DataFrame({
        "Column": df.columns,
        "Data Type": [str(dtype) for dtype in df.dtypes],
        "Non-Null Values": [f"{n:,}" for n in non_null],
        "Null Values": [f"{len(df) - n:,}" for n in non_null],
    })


def _time_like_index(columns) -> int:
    """Preselect the first column whose name suggests a date/time, else the first column."""
    return next((i for i, c in enumerate(columns) if any(k in str(c).upper() for k in ('TIME', 'DATE'))), 0)


def _time_tab(df, fp):
    st.subheader(t("hdr_datetime_filter"))
    filterbytime = st.checkbox(t("chk_enable_time_filter"), help="Filter data to a specific date/time range")
    if not filterbytime:
        return df, fp, False
    if 'SOURCE_FILE' in df.columns and df['SOURCE_FILE'].nunique() > 1:
        st.info("Multiple source files detected. Configure datetime columns for each file:")
        datetime_mapping = multi_source_time_filter_config(df)
        applied = safe_session_get(TIME_MAPPING_KEY)
        if datetime_mapping:
            st.subheader(t("hdr_apply_time_filter"))
            if st.button(t("btn_apply_time_filter")):
                applied = dict(datetime_mapping)
                safe_session_set(TIME_MAPPING_KEY, applied)
            elif applied and applied != datetime_mapping:
                st.info("Column selections changed — press the button above to apply them.")
        else:
            st.warning("No files configured for time filtering")
        if applied:
            df, fp = time_filter(df, applied, fp)
        return df, fp, True

    st.info("Select the column containing your date/time data, then choose your filtering options below.")
    datetime_Column = st.selectbox(
        "Select Date/Time Column",
        options=df.columns,
        index=_time_like_index(df.columns),
        help="Choose the column that contains date/time information"
    )
    df, fp = time_filter(df, datetime_Column, fp)
    return df, fp, True


def _declutter_tab(df, fp):
    st.subheader(t("hdr_data_declutter"))
    declutter_dis = st.checkbox(
        "Consolidate Location Points",
        help="Average multiple location points over specified time intervals to reduce data density"
    )
    if not declutter_dis:
        return df, fp, False
    st.info("💡 This feature combines nearby points taken within the same time interval into a single averaged location.")
    datetim_Column = st.selectbox(
        "Choose Date/Time Column",
        options=df.columns,
        index=_time_like_index(df.columns),
        help="Select the column containing date/time data for grouping"
    )
    df, fp = declutterer(df, date_column=datetim_Column, fp=fp)
    return df, fp, True


def manage_ingested_data(df: pandas.DataFrame, fp: str):
    """Render the Manage Ingested Data panel and return (active_df, fingerprint, filters_active).

    Steps run in a fixed order (row removal → time filter → declutter → timezone), and each is
    memoized on its input fingerprint and settings, so reruns triggered elsewhere are cheap.
    """
    dataset_key = fp
    with st.expander("Manage Ingested Data"):
        tabi, tabii, tabiii, tabiv = st.tabs([t("tab_review_ingest"), t("tab_time_filter"), t("tab_declutter"), t("tab_timezone")])
        with tabi:
            df, fp = _review_tab(df, fp)
        with tabii:
            df, fp, time_active = _time_tab(df, fp)
        with tabiii:
            df, fp, declutter_active = _declutter_tab(df, fp)
        with tabiv:
            df, fp = timezone_conversion(df, fp, dataset_key)
    return df, fp, time_active or declutter_active
