import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px  # pip install plotly-express
import plotly.io as pio
from io import BytesIO
from datetime import datetime
from botocore.exceptions import ClientError
import boto3
from PIL import Image

######################
# Initialize variables
######################
# background nutanix logo for diagrams
background_image = dict(source=Image.open("images/nutanix-x.png"), xref="paper", yref="paper", x=0.5, y=0.5, sizex=0.95, sizey=0.95, xanchor="center", yanchor="middle", opacity=0.04, layer="below", sizing="contain")

######################
# Custom Functions
######################
# Use local CSS
def local_css(file_name):
    with open(file_name) as f:
        #st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        return f.read()

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
    df_vInfo.convert_dtypes().dtypes # autoset datatypes to reduce memory consumption    
    df_vCPU = df.parse('vCPU', usecols=vCPU_cols_to_use)
    df_vCPU.convert_dtypes().dtypes # autoset datatypes to reduce memory consumption    
    df_vMemory = df.parse('vMemory', usecols=vMemory_cols_to_use)
    df_vMemory.convert_dtypes().dtypes # autoset datatypes to reduce memory consumption    


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

    # Add / Generate Total Columns from vCPU performance percentage data & convert columns to right datatype to reduce memory coonsumption
    df_vCPU['vCPUs'] = df_vCPU['vCPUs'].astype(np.int16)
    df_vCPU['vCPU Peak %'] = df_vCPU['vCPU Peak %'].astype(np.float32)
    df_vCPU.loc[:,'vCPU Peak #'] = df_vCPU.apply(lambda row: get_vCPU_total_values(row, 'vCPU Peak %'), axis=1).astype(np.int16)
    df_vCPU['vCPU Average %'] = df_vCPU['vCPU Average %'].astype(np.float32)
    df_vCPU.loc[:,'vCPU Average #'] = df_vCPU.apply(lambda row: get_vCPU_total_values(row, 'vCPU Average %'), axis=1).astype(np.int16)
    df_vCPU['vCPU Median %'] = df_vCPU['vCPU Median %'].astype(np.float32)
    df_vCPU.loc[:,'vCPU Median #'] = df_vCPU.apply(lambda row: get_vCPU_total_values(row, 'vCPU Median %'), axis=1).astype(np.int16)
    df_vCPU['vCPU 95th Percentile %'] = df_vCPU['vCPU 95th Percentile %'].astype(np.float32)
    df_vCPU.loc[:,'vCPU 95th Percentile #'] = df_vCPU.apply(lambda row: get_vCPU_total_values(row, 'vCPU 95th Percentile %'), axis=1).astype(np.int16)

    # Add / Generate Total Columns from vMemory performance percentage data & convert columns to right datatype to reduce memory coonsumption
    df_vMemory['vMemory Size (GiB)'] = df_vMemory['vMemory Size (GiB)'].astype(np.float32)
    df_vMemory['vMemory Peak %'] = df_vMemory['vMemory Peak %'].astype(np.float32)
    df_vMemory.loc[:,'vMemory Peak #'] = df_vMemory.apply(lambda row: get_vMemory_total_values(row, 'vMemory Peak %'), axis=1).astype(np.float32)
    df_vMemory['vMemory Average %'] = df_vMemory['vMemory Average %'].astype(np.float32)
    df_vMemory.loc[:,'vMemory Average #'] = df_vMemory.apply(lambda row: get_vMemory_total_values(row, 'vMemory Average %'), axis=1).astype(np.float32)
    df_vMemory['vMemory Median %'] = df_vMemory['vMemory Median %'].astype(np.float32)
    df_vMemory.loc[:,'vMemory Median #'] = df_vMemory.apply(lambda row: get_vMemory_total_values(row, 'vMemory Median %'), axis=1).astype(np.float32)
    df_vMemory['vMemory 95th Percentile %'] = df_vMemory['vMemory 95th Percentile %'].astype(np.float32)
    df_vMemory.loc[:,'vMemory 95th Percentile #'] = df_vMemory.apply(lambda row: get_vMemory_total_values(row, 'vMemory 95th Percentile %'), axis=1).astype(np.float32)

    df_vinfo_vcpu_merged = pd.merge(df_vInfo, df_vCPU, left_on="MOID", right_on="vCPU MOID", how="left")
    main_df = pd.merge(df_vinfo_vcpu_merged, df_vMemory, left_on="MOID", right_on="vMemory MOID", how="left")
    main_df.drop(['MOID','vCPU MOID','vMemory MOID'], axis=1, inplace=True) # Drop no lomnger needed columns after merge

    # Change column order to be more logic & easier to read
    main_df = main_df[['VM Name', 'Power State', 'Cluster Name', 'vCPUs', 'vCPU Peak %', 'vCPU Peak #', 'vCPU Average %', 'vCPU Average #', 'vCPU Median %', 'vCPU Median #', 'vCPU 95th Percentile %', 'vCPU 95th Percentile #', 'vMemory Size (GiB)', 'vMemory Peak %', 'vMemory Peak #', 'vMemory Average %', 'vMemory Average #', 'vMemory Median %', 'vMemory Median #', 'vMemory 95th Percentile %', 'vMemory 95th Percentile #']]

    #print (main_df.info())

    return main_df

def upload_to_aws(data):
    s3_client = boto3.client('s3', aws_access_key_id=st.secrets["s3_access_key_id"],
                      aws_secret_access_key=st.secrets["s3_secret_access_key"])

    current_datetime_as_filename = datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")+".xlsx"
    
    try:
        s3_client.put_object(Bucket='ntnx-vm-right-sizing', Body=data.getvalue(), Key=current_datetime_as_filename)
        st.session_state[data.name] = True # store uploaded filename as sessionstate variable in order to block reupload of same file
        return True
    except FileNotFoundError:
        return False

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

# Generate vCPU Overview Section for streamlit column 1+2
@st.cache
def generate_vCPU_overview_df(custom_df):

    vCPU_provisioned = int(custom_df["vCPUs"].sum())
    vCPU_peak = int(custom_df["vCPU Peak #"].sum())
    vCPU_average = int(custom_df["vCPU Average #"].sum())
    vCPU_median = int(custom_df["vCPU Median #"].sum())
    vCPU_95_percentile = int(custom_df["vCPU 95th Percentile #"].sum())
    vCPU_overview_first_column = {'': ["# vCPUs - Provisioned", "# vCPUs - Peak", "# vCPUs - Average", "# vCPUs - Median", "# vCPUs - 95th Percentile"]}
    vCPU_overview_df = pd.DataFrame(vCPU_overview_first_column)
    vCPU_overview_second_column = [vCPU_provisioned, vCPU_peak, vCPU_average, vCPU_median, vCPU_95_percentile]
    vCPU_overview_df.loc[:,'vCPU'] = vCPU_overview_second_column

    return vCPU_overview_df

# Generate vMemory Overview Section for streamlit column 1+2
@st.cache(allow_output_mutation=True)
def generate_vMemory_overview_df(custom_df):

    vMemory_provisioned = custom_df["vMemory Size (GiB)"].sum()
    vMemory_peak = custom_df["vMemory Peak #"].sum()
    vMemory_average = custom_df["vMemory Average #"].sum()
    vMemory_median = custom_df["vMemory Median #"].sum()
    vMemory_95_percentile = custom_df["vMemory 95th Percentile #"].sum()
    vMemory_overview_first_column = {'': ["# vMemory - Provisioned", "# vMemory - Peak", "# vMemory - Average", "# vMemory - Median", "# vMemory - 95th Percentile"]}
    vMemory_overview_df = pd.DataFrame(vMemory_overview_first_column)
    vMemory_overview_second_column = [vMemory_provisioned, vMemory_peak, vMemory_average, vMemory_median, vMemory_95_percentile]
    vMemory_overview_df.loc[:,'GiB'] = vMemory_overview_second_column

    # Style data values to two decimals and set default value in case of NAN
    vMemory_overview_df = vMemory_overview_df.style.format(precision=2, na_rep='nicht vorhanden') 
   
    return vMemory_overview_df

# Generate Bar charts for vCPU & vMemory
@st.cache
def generate_bar_charts(df_vCPU_or_vMemory, y_axis_name):

    bar_chart_names = ['Provisioned', 'Peak', 'Average', 'Median', '95th Percentile']

    bar_chart = px.bar(
                df_vCPU_or_vMemory,
                x = "",
                y = y_axis_name,
                text=bar_chart_names
            )
    bar_chart.update_traces(marker_color=['#F36D21', '#4C4C4E', '#6560AB', '#3ABFEF', '#034EA2'])
    bar_chart.update_layout(
            margin=dict(l=10, r=10, t=20, b=10,pad=4), autosize=True, height = 350, 
            xaxis={'visible': False, 'showticklabels': False}
        )
    bar_chart.update_traces(texttemplate='%{text}', textposition='outside',textfont_size=14, cliponaxis= False)

    bar_chart.add_layout_image(background_image)

    bar_chart_config = { 'staticPlot': True}

    return bar_chart, bar_chart_config

# Generate Histogram charts for vCPU & vMemory
@st.cache
def generate_histogram_charts(custom_df, y_axis_name, performance_type_selected):

    if y_axis_name == "vMemory Size (GiB)":
        prefix_string = "vMemory "
    else:
        prefix_string = "vCPU "

    counts, bins = np.histogram(custom_df[prefix_string + performance_type_selected+" %"] , bins=range(0, 105, 5))
    bins = 0.5 * (bins[:-1] + bins[1:])

    histogram_chart = px.bar(
            x=bins,
            y=counts, 
            labels={'x':prefix_string + performance_type_selected+" %", 'y':'Anzahl VMs'},
            text=np.where(counts>0,counts,'')            
        )

    histogram_chart.update_layout(
            margin=dict(l=10, r=10, t=20, b=10,pad=4), autosize=True,
            xaxis={'visible': True, 'showticklabels': True}
        )
    histogram_chart.update_xaxes(dtick=5)

    histogram_chart.update_traces(marker=dict(color='#034EA2'),texttemplate='%{text}', textposition='outside',textfont_size=14, cliponaxis= False)

    histogram_chart.add_layout_image(background_image)

    histogram_chart_config = {'staticPlot': True}
    #histogram_chart_config = {}

    return histogram_chart, histogram_chart_config

# Generate Scatter charts for vCPU & vMemory
@st.cache
def generate_scatter_charts(custom_df, y_axis_name, performance_type_selected):

    if y_axis_name == "vMemory Size (GiB)":
        prefix_string = "vMemory "
    else:
        prefix_string = "vCPU "

    scatter_chart = px.scatter(        
                custom_df,
                x = prefix_string + performance_type_selected+" %",
                y = y_axis_name,
                hover_name="VM Name",
                hover_data=[prefix_string + performance_type_selected+" #"]
            )
    scatter_chart.update_traces(marker=dict(size=6,color='#034EA2'))

    scatter_chart.update_layout(
            margin=dict(l=10, r=10, t=20, b=10,pad=4), autosize=True,
            xaxis={'visible': True, 'showticklabels': True}
        )

    scatter_chart.add_layout_image(background_image)
    scatter_chart_config = { 
            "displaylogo": False, 'modeBarButtonsToRemove': ['zoom2d', 'toggleSpikelines', 'pan2d', 'select2d',
             'lasso2d', 'autoScale2d', 'hoverClosestCartesian', 'hoverCompareCartesian']
        }

    return scatter_chart, scatter_chart_config

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
def download_as_excel(output_to_show, vCPU_overview, vMemory_overview):

    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    output_to_show.to_excel(writer, index=False, sheet_name='VM Details', startrow=4, startcol=0, float_format='%.2f')
    workbook = writer.book
    worksheet_vm_details = writer.sheets['VM Details']
    header_format = workbook.add_format({'bold': True, 'font_color': '#034EA2','font_size':18})
    subheader_format = workbook.add_format({'bold': True, 'font_color': '#000000','font_size':14})
    
    for col in range(21): #set column width for cells
        worksheet_vm_details.set_column(col, col, 25)
    worksheet_vm_details.write(0, 0, "VM Right Sizing Analyse - VM Details",header_format)
    worksheet_vm_details.write(2, 0, "Bitte Anmerkungen auf gesondertem Tabellenblatt beachten.")
    worksheet_vm_details.freeze_panes(5, 0)
    format_dataframe_as_table(writer, 'VM Details', output_to_show.data)

    vCPU_overview.to_excel(writer, index=False, sheet_name='Uebersicht', startrow=4, startcol=0)
    vMemory_overview.to_excel(writer, index=False, sheet_name='Uebersicht', startrow=21, startcol=0)
    worksheet_uebersicht = writer.sheets['Uebersicht']
    
    for col in range(2): #set column width for cells
        worksheet_uebersicht.set_column(col, col, 25)
    worksheet_uebersicht.write(0, 0, "VM Right Sizing Analyse - Uebersicht",header_format)
    worksheet_uebersicht.write(2, 0, "vCPU Gesamt-Auswertung:", subheader_format)
    worksheet_uebersicht.write(19, 0, "vMemory Gesamt-Auswertung:", subheader_format)

    # Charts are independent of worksheets
    chart_vcpu = workbook.add_chart({'type': 'column'})
    chart_vcpu.set_legend({'none': True})
    chart_vram = workbook.add_chart({'type': 'column'})
    chart_vram.set_legend({'none': True})
    diff_color_list = list([{ 'fill': { 'color':'#F36D21' }}, { 'fill': { 'color':'#4C4C4E' }}, { 'fill': { 'color':'#6560AB' }}, { 'fill': { 'color':'#3ABFEF' }}, { 'fill': { 'color':'#034EA2' }}])

    chart_vcpu.add_series({'categories': '=Uebersicht!$A$6:$A$10','values': '=Uebersicht!$B$6:$B$10', 'points':diff_color_list })
    worksheet_uebersicht.insert_chart('D3', chart_vcpu)

    chart_vram.add_series({'categories': '=Uebersicht!$A$23:$A$27','values': '=Uebersicht!$B$23:$B$27', 'points':diff_color_list })
    worksheet_uebersicht.insert_chart('D20', chart_vram)

    worksheet_anmerkungen = workbook.add_worksheet('Anmerkungen')
    worksheet_anmerkungen.write(0, 0, "Anmerkungen",header_format)
    worksheet_anmerkungen.set_column('A:A', 150)
    cell_format = workbook.add_format({'text_wrap': True,'align':'top'})
    worksheet_anmerkungen.write(2, 0, "Diese Analyse basiert auf einer Nutanix Collector Auswertung. Diese kann neben den zugewiesenen vCPU & vMemory Ressourcen an die VMs ebenfalls die Performance Werte der letzten 7 Tage in 30 Minuten Intervallen aus vCenter / Nutanix Prism auslesen und bietet anhand dessen eine Möglichkeit für VM Right-Sizing Empfehlungen.", cell_format)
    worksheet_anmerkungen.write(3, 0, "Stellen Sie bitte sicher, dass die Auswertung für einen repräsentativen Zeitraum durchgeführt wurde. Für die ausgeschalteten VMs stehen (abhängig davon, wie lange diese bereits ausgeschaltet sind) i.d.R. keine Performance Werte (Peak, Average, Median oder 95th Percentile) zur Verfügung - in diesem Fall werden die provisionierten / zugewiesenen Werte verwendet.", cell_format)
    worksheet_anmerkungen.write(4, 0, "Auch werden bei allen Performance-basierten Werten 20% zusätzlicher Puffer mit eingerechnet. Generell ist die Empfehlung sich bei den Performance Werten an den 95th Percentile Werten zu orientieren, da diese die tatsächliche Auslastung am besten repräsentieren und nicht durch ggf. kurzzeitige Lastspitzen verfälscht werden.", cell_format)
    worksheet_anmerkungen.write(5, 0, "Die gezeigten Empfehlungen orientieren sich rein an der vCPU & vMemory Auslastung der VM – ohne die darin laufenden Anwendungen & deren Anforderungen zu berücksichtigen. Daher obliegt Ihnen eine abschließende Bewertung, ob die getroffenen Right Sizing Empfehlungen bei Ihnen durchführbar bzw. supported sind.", cell_format)
    worksheet_anmerkungen.write(6, 0, "Solch ein VM Right Sizing bietet sich vor der Beschaffung einer neuen Infrastruktur an, sollte aber auch darüber hinaus regelmäßig und wiederkehrend durchgeführt werden. Nutanix bietet diese Funktionalität ebenfalls bereits als einen integrierten Bestandteil des Prism PRO Funktionsumfanges. Hierbei werden umfangreichere Analysen durchgeführt die sich über einen längeren Zeitraum erstrecken und weitere Mehrwerte bieten.", cell_format)
    worksheet_anmerkungen.write(8, 0, "Disclaimer: Die automatische Auswertung basiert auf einem Hobby Projekt und dient primär als Anhaltspunkt für ein mögliches Right Sizing - keine Garantie auf Vollständigkeit oder Korrektheit der Auswertung / Daten.", cell_format) 

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

# generate the values required for the savings text string
def get_savings_value(performance_type_selected,vCPU_overview,vMemory_overview):

    if performance_type_selected == '95th Percentile':
        savings_vCPU = int(vCPU_overview.iat[0,1])-int(vCPU_overview.iat[4,1])
        savings_vMemory = int(vMemory_overview.iat[0,1])-int(vMemory_overview.iat[4,1])
    elif performance_type_selected == "Peak":
        savings_vCPU = int(vCPU_overview.iat[0,1])-int(vCPU_overview.iat[1,1])
        savings_vMemory = int(vMemory_overview.iat[0,1])-int(vMemory_overview.iat[1,1])
    elif performance_type_selected == "Average":
        savings_vCPU = int(vCPU_overview.iat[0,1])-int(vCPU_overview.iat[2,1])
        savings_vMemory = int(vMemory_overview.iat[0,1])-int(vMemory_overview.iat[2,1])
    elif performance_type_selected == "Median":
        savings_vCPU = int(vCPU_overview.iat[0,1])-int(vCPU_overview.iat[3,1])
        savings_vMemory = int(vMemory_overview.iat[0,1])-int(vMemory_overview.iat[3,1])

    return savings_vCPU, savings_vMemory

# generates the default columns to show of the tables based on selectbox value
def get_default_columns_to_show(performance_type_selected):

    if performance_type_selected == '95th Percentile':
        columns_to_show = [0,1,2,3,10,11,12,19,20]
    elif performance_type_selected == "Peak":
        columns_to_show = [0,1,2,3,4,5,12,13,14]
    elif performance_type_selected == "Average":
        columns_to_show = [0,1,2,3,6,7,12,15,16]
    elif performance_type_selected == "Median":
        columns_to_show = [0,1,2,3,8,9,12,17,18]

    return columns_to_show