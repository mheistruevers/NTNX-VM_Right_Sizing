import pandas as pd
import numpy as np
from io import BytesIO
import streamlit as st

# Generate Dataframe from Excel and make neccessary adjustment for easy consumption later on
@st.cache
def get_data_from_excel(uploaded_file):

    df = pd.ExcelFile(uploaded_file, engine="openpyxl")

    # Columns to Read from Excel file
    vInfo_cols_to_use = ["VM Name","Power State","Cluster Name","MOID"]
    vCPU_cols_to_use = ["vCPUs","Peak %","Average %","Median %","95th Percentile % (recommended)","MOID"]
    vMemory_cols_to_use = ["Size (MiB)","Peak %","Average %","Median %","95th Percentile % (recommended)","MOID"]

    # Create df for each tab with only relevant columns
    df_vInfo = df.parse('vInfo', usecols=vInfo_cols_to_use)
    df_vCPU = df.parse('vCPU', usecols=vCPU_cols_to_use)
    df_vMemory = df.parse('vMemory', usecols=vMemory_cols_to_use)

    # Rename columns to make it shorter
    df_vCPU.rename(columns={'95th Percentile % (recommended)': '95th Percentile %'}, inplace=True)
    df_vMemory.rename(columns={'95th Percentile % (recommended)': '95th Percentile %'}, inplace=True)
    
    # Calculate from MiB to GiB & rename column
    df_vMemory.loc[:,"Size (MiB)"] = df_vMemory["Size (MiB)"] / 1024 # Use GiB instead of MiB
    df_vMemory.rename(columns={'Size (MiB)': 'Size (GiB)'}, inplace=True) # Rename Column

    # Add prefix to vCPU & vMemory columns from each tab as names are identical and would cause duplicate columns during merge
    df_vCPU.columns = 'vCPU ' + df_vCPU.columns.values    
    df_vCPU.rename(columns={'vCPU vCPUs': 'vCPUs'}, inplace=True)
    df_vMemory.columns = 'vMemory ' + df_vMemory.columns.values

    # Add / Generate Total Columns from vCPU performance percentage data
    df_vCPU['vCPUs'] = df_vCPU['vCPUs'].astype(int)
    df_vCPU.loc[:,'vCPU Peak #'] = df_vCPU.apply(lambda row: get_vCPU_total_values(row, 'vCPU Peak %'), axis=1).astype(int)
    df_vCPU.loc[:,'vCPU Average #'] = df_vCPU.apply(lambda row: get_vCPU_total_values(row, 'vCPU Average %'), axis=1).astype(int)
    df_vCPU.loc[:,'vCPU Median #'] = df_vCPU.apply(lambda row: get_vCPU_total_values(row, 'vCPU Median %'), axis=1).astype(int)
    df_vCPU.loc[:,'vCPU 95th Percentile #'] = df_vCPU.apply(lambda row: get_vCPU_total_values(row, 'vCPU 95th Percentile %'), axis=1).astype(int)

    # Add / Generate Total Columns from vMemory performance percentage data
    df_vMemory.loc[:,'vMemory Peak #'] = df_vMemory.apply(lambda row: get_vMemory_total_values(row, 'vMemory Peak %'), axis=1)
    df_vMemory.loc[:,'vMemory Average #'] = df_vMemory.apply(lambda row: get_vMemory_total_values(row, 'vMemory Average %'), axis=1)
    df_vMemory.loc[:,'vMemory Median #'] = df_vMemory.apply(lambda row: get_vMemory_total_values(row, 'vMemory Median %'), axis=1)
    df_vMemory.loc[:,'vMemory 95th Percentile #'] = df_vMemory.apply(lambda row: get_vMemory_total_values(row, 'vMemory 95th Percentile %'), axis=1)

    df_vinfo_vcpu_merged = pd.merge(df_vInfo, df_vCPU, left_on="MOID", right_on="vCPU MOID", how="left")
    main_df = pd.merge(df_vinfo_vcpu_merged, df_vMemory, left_on="MOID", right_on="vMemory MOID", how="left")
    main_df.drop(['MOID','vCPU MOID','vMemory MOID'], axis=1, inplace=True) # Drop no lomnger needed columns after merge

    # Change column order to be more logic & easier to read
    main_df = main_df[['VM Name', 'Power State', 'Cluster Name', 'vCPUs', 'vCPU Peak %', 'vCPU Peak #', 'vCPU Average %', 'vCPU Average #', 'vCPU Median %', 'vCPU Median #', 'vCPU 95th Percentile %', 'vCPU 95th Percentile #', 'vMemory Size (GiB)', 'vMemory Peak %', 'vMemory Peak #', 'vMemory Average %', 'vMemory Average #', 'vMemory Median %', 'vMemory Median #', 'vMemory 95th Percentile %', 'vMemory 95th Percentile #']]

    return main_df

# Generate vCPU Values for Peak, Median, Average & 95 Percentile
def get_vCPU_total_values(df_row, compare_value):
    if pd.isna(df_row[compare_value]):
        get_total_value = df_row['vCPUs'] # if no data is available use provisioned vCPU data
    else:
        get_total_value = df_row['vCPUs'] * (df_row[compare_value]/100)* 1.2
        if(get_total_value) < 1:
            get_total_value = 1
        if(get_total_value) > df_row['vCPUs']:
            get_total_value = df_row['vCPUs']
    return np.ceil(get_total_value)

# Generate vMemory Values for Peak, Median, Average & 95 Percentile
def get_vMemory_total_values(df_row, compare_value):
    vMemory_row_value = df_row['vMemory Size (GiB)']
    vMemory_perf_value = df_row[compare_value]
    if pd.isna(vMemory_perf_value):
        get_total_value = vMemory_row_value # if no data is available use provisioned vMemory data
    else:
        get_total_value = vMemory_row_value * (vMemory_perf_value/100)* 1.2
        if np.less(get_total_value, 1):
            if np.less(vMemory_row_value, 1):
                get_total_value = vMemory_row_value
            else:
                get_total_value = 1
        elif np.greater(get_total_value, vMemory_row_value):
            get_total_value = vMemory_row_value
        else:
            get_total_value = np.ceil(get_total_value)
    return get_total_value

# Returns a value rounded up to a specific number of decimal places.
def round_decimals_up(number:float, decimals:int=2):
    if not isinstance(decimals, int):
        raise TypeError("decimal places must be an integer")
    elif decimals < 0:
        raise ValueError("decimal places has to be 0 or more")
    elif decimals == 0:
        return math.ceil(number)
    factor = 10 ** decimals
    return np.ceil(number * factor) / factor

# Generate vCPU Overview Section for streamlit column 1+2
def generate_vCPU_overview_df(custom_df):

    vCPU_provisioned = int(custom_df["vCPUs"].sum())
    vCPU_peak = int(custom_df["vCPU Peak #"].sum())
    vCPU_average = int(custom_df["vCPU Average #"].sum())
    vCPU_median = int(custom_df["vCPU Median #"].sum())
    vCPU_95_percentile = int(custom_df["vCPU 95th Percentile #"].sum())
    vCPU_overview_first_column = {'': ["# vCPUs (provisioned)", "# vCPUs (Peak)", "# vCPUs (Average)", "# vCPUs (Median)", "# vCPUs (95th Percentile)"]}
    vCPU_overview_df = pd.DataFrame(vCPU_overview_first_column)
    vCPU_overview_second_column = [vCPU_provisioned, vCPU_peak, vCPU_average, vCPU_median, vCPU_95_percentile]
    vCPU_overview_df.loc[:,'vCPU'] = vCPU_overview_second_column

    return vCPU_overview_df

# Generate vMemory Overview Section for streamlit column 1+2
def generate_vMemory_overview_df(custom_df):

    vMemory_provisioned = custom_df["vMemory Size (GiB)"].sum()
    vMemory_peak = custom_df["vMemory Peak #"].sum()
    vMemory_average = custom_df["vMemory Average #"].sum()
    vMemory_median = custom_df["vMemory Median #"].sum()
    vMemory_95_percentile = custom_df["vMemory 95th Percentile #"].sum()
    vMemory_overview_first_column = {'': ["# vMemory (provisioned)", "# vMemory (Peak)", "# vMemory (Average)", "# vMemory (Median)", "# vMemory (95th Percentile)"]}
    vMemory_overview_df = pd.DataFrame(vMemory_overview_first_column)
    vMemory_overview_second_column = [vMemory_provisioned, vMemory_peak, vMemory_average, vMemory_median, vMemory_95_percentile]
    vMemory_overview_df.loc[:,'GiB'] = vMemory_overview_second_column

     # Style data values to two decimals and set default value in case of NAN
    vMemory_overview_df = vMemory_overview_df.style.format(precision=2, na_rep='nicht vorhanden') 
   
    return vMemory_overview_df

# Generate df for output on streamlit dataframe
def generate_results_df_for_output(custom_df, vm_detail_columns_to_show):

    # Style data values to two decimals and set default value in case of NAN
    custom_df = custom_df.style.format(precision=2, na_rep='nicht vorhanden') 

    # drop columns based on multiselect
    custom_df.data = drop_columns_based_on_multiselect(custom_df.data, vm_detail_columns_to_show)

    return custom_df

# drop columns based on multiselect
def drop_columns_based_on_multiselect(new_df, vm_detail_columns_to_show): 

    for column in new_df.columns.values:
        if column not in vm_detail_columns_to_show:
            new_df.drop(columns=column, inplace=True)
    
    return new_df

# Generate dataframe as excel file for downloads
#@st.cache - I do not think cache helps here, as it gets regenerated after a change / download
def download_as_excel(output_to_show):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    output_to_show.to_excel(writer, index=False, sheet_name='Auswertung', startrow=4, startcol=0)
    workbook = writer.book
    worksheet_auswertung = writer.sheets['Auswertung']
    header_format = workbook.add_format({'bold': True, 'font_color': '#034EA2','font_size':18})
    
    for col in range(21): #set column width for cells
        worksheet_auswertung.set_column(col, col, 25)
    worksheet_auswertung.write(0, 0, "VM Right Sizing Analyse (powered by Nutanix Collector)",header_format)
    worksheet_auswertung.write(2, 0, "Bitte Anmerkungen auf gesondertem Tabellenblatt beachten.")
    worksheet_auswertung.freeze_panes(5, 0)
    format_dataframe_as_table(writer, 'Auswertung', output_to_show.data)

    worksheet_anmerkungen = workbook.add_worksheet('Anmerkungen')
    worksheet_anmerkungen.write(0, 0, "Anmerkungen",header_format)
    worksheet_anmerkungen.set_column('A:A', 150)
    cell_format = workbook.add_format({'text_wrap': True,'align':'top'})
    worksheet_anmerkungen.write(2, 0, "Diese Analyse basiert auf einer Nutanix Collector Auswertung. Diese kann neben den zugewiesenen vCPU & vMemory Ressourcen an die VMs ebenfalls die Performance Werte der letzten 7 Tage in 30 Minuten Intervallen aus vCenter / Nutanix Prism auslesen und bietet anhand dessen eine Möglichkeit für VM Right-Sizing Empfehlungen.", cell_format)
    worksheet_anmerkungen.write(3, 0, "Stellen Sie bitte sicher, dass die Auswertung für einen repräsentativen Zeitraum durchgeführt wurde. Für die ausgeschalteten VMs stehen (abhängig davon, wie lange diese bereits ausgeschaltet sind) i.d.R. keine Performance Werte (Peak, Average, Median oder 95th Percentile) zur Verfügung - in diesem Fall werden die provisionierten / zugewiesenen Werte verwendet.", cell_format)
    worksheet_anmerkungen.write(4, 0, "Auch werden bei allen Performance-basierten Werten 20% zusätzlicher Puffer mit eingerechnet. Generell ist die Empfehlung sich bei den Performance Werten an den 95th Percentile Werten zu orientieren, da diese die tatsächliche Auslastung am besten repräsentieren und nicht durch ggf. kurzzeitige Lastspitzen verfälscht werden.", cell_format)
    worksheet_anmerkungen.write(5, 0, "Die gezeigten Empfehlungen orientieren sich rein an der vCPU & vMemory Auslastung der VM – ohne die darin laufenden Anwendungen & deren Anforderungen zu berücksichtigen. Daher obliegt Ihnen eine abschließende Bewertung, ob die getroffenen Right Sizing Empfehlungen bei Ihnen durchführbar bzw. supported sind.", cell_format)
    worksheet_anmerkungen.write(7, 0, "Disclaimer: Die automatische Auswertung basiert auf einem Hobby Projekt und dient primär als Anhaltspunkt für ein mögliches Right Sizing - keine Garantie auf Vollständigkeit oder Korrektheit der Auswertung / Daten.", cell_format)

    writer.save()
    processed_data = output.getvalue()
    return processed_data

# Format dataframe as table in excel
def format_dataframe_as_table(writer, sheet_name, output_to_show):
    outcols = output_to_show.columns
    if len(outcols) > 25:
        raise ValueError('table width out of range for current logic')
    tbl_hdr = [{'header':c} for c in outcols]
    bottom_num = len(output_to_show)+1
    right_letter = chr(65-1+len(outcols))
    tbl_corner = right_letter + str(bottom_num+4)
    worksheet = writer.sheets[sheet_name]
    worksheet.add_table('A5:' + tbl_corner,  {'columns':tbl_hdr})