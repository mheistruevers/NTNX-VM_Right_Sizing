import pandas as pd
import numpy as np
from io import BytesIO
import streamlit as st

# Read Excel File
@st.cache(allow_output_mutation=True)
def get_data_from_excel(uploaded_file):
    print("Get Data from Excel Function has been executed")
    df = pd.ExcelFile(uploaded_file, engine="openpyxl")
    st.balloons()
    return df

# Generate Dataframe for each Tab & replace Blank in headers with underscore
def get_tabs_df_from_excel(df,Tab_Name):
    print("Get Tabs from Excel Function has been executed")
    df_temp = pd.read_excel(df, Tab_Name)
    # Blanks in Colum name need to be removed due to known issues with filtering & sorting
    df_temp.columns =[column.replace(" ", "_") for column in df_temp.columns] 
    return df_temp

# Get Peak vCPU Values
def get_vCPU_peak_total_value(df_row):
    if pd.isna(df_row['vCPU_Peak_%']):
        get_total_value = df_row['vCPU_vCPUs'] # if no peak data is available use provisioned vCPU data
    else:
        get_total_value = df_row['vCPU_vCPUs'] * (df_row['vCPU_Peak_%']/100)* 1.2
        if(get_total_value) < 1:
            get_total_value = 1
        if(get_total_value) > df_row['vCPU_vCPUs']:
            get_total_value = df_row['vCPU_vCPUs']
    return np.ceil(get_total_value)

# Get Average vCPU Values
def get_vCPU_average_total_value(df_row):
    if pd.isna(df_row['vCPU_Average_%']):
        get_total_value = df_row['vCPU_vCPUs'] # if no average data is available use provisioned vCPU data
    else:
        get_total_value = df_row['vCPU_vCPUs'] * (df_row['vCPU_Average_%']/100) * 1.2
        if(get_total_value) < 1:
            get_total_value = 1
        if(get_total_value) > df_row['vCPU_vCPUs']:
            get_total_value = df_row['vCPU_vCPUs']
    return np.ceil(get_total_value)

# Get Median vCPU Values
def get_vCPU_median_total_value(df_row):
    if pd.isna(df_row['vCPU_Median_%']):
        get_total_value = df_row['vCPU_vCPUs'] # if no median data is available use provisioned vCPU data
    else:
        get_total_value = df_row['vCPU_vCPUs'] * (df_row['vCPU_Median_%']/100) * 1.2
        if(get_total_value) < 1:
            get_total_value = 1
        if(get_total_value) > df_row['vCPU_vCPUs']:
            get_total_value = df_row['vCPU_vCPUs']
    return np.ceil(get_total_value)

# Get 95th Percentile vCPU Values
def get_vCPU_95_percentile_total_value(df_row):
    if pd.isna(df_row['vCPU_95th_Percentile_%_(recommended)']):
        get_total_value = df_row['vCPU_vCPUs'] # if no 95th percentile data is available use provisioned vCPU data
    else:
        get_total_value = df_row['vCPU_vCPUs'] * (df_row['vCPU_95th_Percentile_%_(recommended)']/100) * 1.2
        if(get_total_value) < 1:
            get_total_value = 1
        if(get_total_value) > df_row['vCPU_vCPUs']:
            get_total_value = df_row['vCPU_vCPUs']
    return np.ceil(get_total_value)

# Get Peak vMemory Values
def get_vMemory_peak_total_value(df_row):
    if pd.isna(df_row['vMemory_Peak_%']):
        get_total_value = df_row['vMemory_Size_(GiB)']       
    else:
        get_total_value = df_row['vMemory_Size_(GiB)'] * (df_row['vMemory_Peak_%']/100) * 1.2
        if(get_total_value) < 1:
            get_total_value = 1
        if(get_total_value) > df_row['vMemory_Size_(GiB)']:
            get_total_value = df_row['vMemory_Size_(GiB)']
    return np.ceil(get_total_value)

# Get Average vMemory Values
def get_vMemory_average_total_value(df_row):
    if pd.isna(df_row['vMemory_Average_%']):
        get_total_value = df_row['vMemory_Size_(GiB)']        
    else:
        get_total_value = df_row['vMemory_Size_(GiB)'] * (df_row['vMemory_Average_%']/100) * 1.2
        if(get_total_value) < 1:
            get_total_value = 1
        if(get_total_value) > df_row['vMemory_Size_(GiB)']:
            get_total_value = df_row['vMemory_Size_(GiB)']
    return np.ceil(get_total_value)

# Get Median vMemory Values
def get_vMemory_median_total_value(df_row):
    if pd.isna(df_row['vMemory_Median_%']):
        get_total_value = df_row['vMemory_Size_(GiB)']        
    else:
        get_total_value = df_row['vMemory_Size_(GiB)'] * (df_row['vMemory_Median_%']/100) * 1.2
        if(get_total_value) < 1:
            get_total_value = 1
        if(get_total_value) > df_row['vMemory_Size_(GiB)']:
            get_total_value = df_row['vMemory_Size_(GiB)']
    return np.ceil(get_total_value)

# Get 95th Percentile vMemory Values
def get_vMemory_95_percentile_total_value(df_row):
    if pd.isna(df_row['vMemory_95th_Percentile_%_(recommended)']):
        get_total_value = df_row['vMemory_Size_(GiB)']        
    else:
        get_total_value = df_row['vMemory_Size_(GiB)'] * (df_row['vMemory_95th_Percentile_%_(recommended)']/100) * 1.2
        if(get_total_value) < 1:
            get_total_value = 1
        if(get_total_value) > df_row['vMemory_Size_(GiB)']:
            get_total_value = df_row['vMemory_Size_(GiB)']
    return np.ceil(get_total_value)


# Generate custom main dataframe
def get_custom_df_main(df_vInfo, df_vCPU, df_vMemory, vCluster_selected, powerstate_selected):
    
    # Reduce vInfo DF only to needed columns
    df_vinfo_reduced = df_vInfo[["VM_Name","Power_State","Cluster_Name","Host_Name","MOID"]].query("Cluster_Name==@vCluster_selected").query("Power_State==@powerstate_selected")

    # select vCPU & vMemory columns 
    df_vCPU_reduced = df_vCPU[["vCPUs","Peak_%","Average_%","Median_%","95th_Percentile_%_(recommended)","MOID"]] 
    df_vMemory_reduced = df_vMemory[["Size_(MiB)","Peak_%","Average_%","Median_%","95th_Percentile_%_(recommended)","MOID"]]
    #df_vMemory_reduced["Size_(MiB)"] = df_vMemory_reduced["Size_(MiB)"] / 1024 # Umrechnen von MiB in GiB
    df_vMemory_reduced.loc[:,"Size_(MiB)"] = df_vMemory_reduced["Size_(MiB)"] / 1024 # Umrechnen von MiB in GiB
    df_vMemory_reduced.rename(columns={'Size_(MiB)': 'Size_(GiB)'}, inplace=True) # Spalte umbenennen

    # Add cloumn suffix due to duplicate names from vcpu and vmemory    
    df_vCPU_reduced.columns = 'vCPU_' + df_vCPU_reduced.columns.values    
    df_vMemory_reduced.columns = 'vMemory_' + df_vMemory_reduced.columns.values

    # calculate vcpu custom values for peak, average, median and 95th percentile
    df_vCPU_reduced = df_vCPU_reduced.astype({"vCPU_vCPUs": int})
    df_vCPU_reduced.loc[:,'vCPU_Peak_Total'] = df_vCPU_reduced.apply(get_vCPU_peak_total_value, axis=1).astype(int)
    df_vCPU_reduced.loc[:,'vCPU_Average_Total'] = df_vCPU_reduced.apply(get_vCPU_average_total_value, axis=1).astype(int)
    df_vCPU_reduced.loc[:,'vCPU_Median_Total'] = df_vCPU_reduced.apply(get_vCPU_median_total_value, axis=1).astype(int)
    df_vCPU_reduced.loc[:,'vCPU_95th_Percentile_%_Total'] = df_vCPU_reduced.apply(get_vCPU_95_percentile_total_value, axis=1).astype(int)

    # calculate vmemory custom values for peak, average, median and 95th percentile
    df_vMemory_reduced = df_vMemory_reduced.astype({"vMemory_Size_(GiB)": int})
    df_vMemory_reduced.loc[:,'vMemory_Peak_Total'] = df_vMemory_reduced.apply(get_vMemory_peak_total_value, axis=1).astype(int)
    df_vMemory_reduced.loc[:,'vMemory_Average_Total'] = df_vMemory_reduced.apply(get_vMemory_average_total_value, axis=1).astype(int)
    df_vMemory_reduced.loc[:,'vMemory_Median_Total'] = df_vMemory_reduced.apply(get_vMemory_median_total_value, axis=1).astype(int)
    df_vMemory_reduced.loc[:,'vMemory_95th_Percentile_%_Total'] = df_vMemory_reduced.apply(get_vMemory_95_percentile_total_value, axis=1).astype(int)

    # 5. Merge DFs and create large main df as basis for calculations
    df_vinfo_vcpu_merged = df_vinfo_reduced.merge(df_vCPU_reduced, left_on="MOID", right_on="vCPU_MOID", how="left")
    df_vinfo_vcpu_vRAM_merged = df_vinfo_vcpu_merged.merge(df_vMemory_reduced, left_on="MOID", right_on="vMemory_MOID", how="left")

    return df_vinfo_vcpu_vRAM_merged

# Generate vCPU Overview Section for streamlit column 1+2
def generate_vCPU_overview_df(custom_df):

    vCPU_provisioned = int(custom_df["vCPU_vCPUs"].sum())
    vCPU_peak = int(custom_df["vCPU_Peak_Total"].sum())
    vCPU_average = int(custom_df["vCPU_Average_Total"].sum())
    vCPU_median = int(custom_df["vCPU_Median_Total"].sum())
    vCPU_95_percentile = int(custom_df["vCPU_95th_Percentile_%_Total"].sum())
    vCPU_overview_first_column = {'': ["# vCPUs (provisioned)", "# vCPUs (Peak)", "# vCPUs (Average)", "# vCPUs (Median)", "# vCPUs (95th Percentile)"]}
    vCPU_overview_df = pd.DataFrame(vCPU_overview_first_column)
    vCPU_overview_second_column = [vCPU_provisioned, vCPU_peak, vCPU_average, vCPU_median, vCPU_95_percentile]
    vCPU_overview_df['vCPU'] = vCPU_overview_second_column
    return vCPU_overview_df

# Generate vMemory Overview Section for streamlit column 1+2
def generate_vMemory_overview_df(custom_df):

    vMemory_provisioned = int(custom_df["vMemory_Size_(GiB)"].sum())
    vMemory_peak = int(custom_df["vMemory_Peak_Total"].sum())
    vMemory_average = int(custom_df["vMemory_Average_Total"].sum())
    vMemory_median = int(custom_df["vMemory_Median_Total"].sum())
    vMemory_95_percentile = int(custom_df["vMemory_95th_Percentile_%_Total"].sum())
    vMemory_overview_first_column = {'': ["# vMemory (provisioned)", "# vMemory (Peak)", "# vMemory (Average)", "# vMemory (Median)", "# vMemory (95th Percentile)"]}
    vMemory_overview_df = pd.DataFrame(vMemory_overview_first_column)
    vMemory_overview_second_column = [vMemory_provisioned, vMemory_peak, vMemory_average, vMemory_median, vMemory_95_percentile]
    vMemory_overview_df['GiB'] = vMemory_overview_second_column
    return vMemory_overview_df

# Generate df for output on streamlit dataframe
def generate_results_df_for_output(custom_df, vm_detail_columns_to_show):

    # Drop irrelevant columns
    new_df = custom_df.drop(columns=['Host_Name', 'MOID','vCPU_MOID','vMemory_MOID'])
    
    # Rename columns for easier readability
    new_df.rename(columns={'VM_Name':'VM Name', 'Power_State':'Power State', 'Cluster_Name':'Cluster Name','vCPU_vCPUs': 'vCPUs', 'vCPU_Peak_%': 'vCPU Peak %','vCPU_Average_%':'vCPU Average %','vCPU_Median_%':"vCPU Median %",'vCPU_95th_Percentile_%_(recommended)':'vCPU 95th Percentile %','vCPU_Peak_Total':'vCPU Peak #','vCPU_Average_Total':'vCPU Average #','vCPU_Median_Total':'vCPU Median #','vCPU_95th_Percentile_%_Total':'vCPU 95th Percentile #','vMemory_Size_(GiB)':'vMemory GiB','vMemory_Peak_%':'vMemory Peak %','vMemory_Average_%':'vMemory Average %','vMemory_Median_%':'vMemory Median %', 'vMemory_95th_Percentile_%_(recommended)':'vMemory 95th Percentile %','vMemory_Peak_Total':'vMemory Peak #','vMemory_Average_Total':'vMemory Average #','vMemory_Median_Total':'vMemory Median #','vMemory_95th_Percentile_%_Total':'vMemory 95th Percentile #'}, inplace=True)

    # Change column order to be more logic & easier to read
    new_df = new_df[['VM Name', 'Power State', 'Cluster Name', 'vCPUs', 'vCPU Peak %', 'vCPU Peak #', 'vCPU Average %', 'vCPU Average #', 'vCPU Median %', 'vCPU Median #', 'vCPU 95th Percentile %', 'vCPU 95th Percentile #', 'vMemory GiB', 'vMemory Peak %', 'vMemory Peak #', 'vMemory Average %', 'vMemory Average #', 'vMemory Median %', 'vMemory Median #', 'vMemory 95th Percentile %', 'vMemory 95th Percentile #']]

    # Style data values to two decimals and set default value in case of NAN
    new_df = new_df.style.format(precision=2, na_rep='nicht vorhanden') 

    # drop columns based on multiselect
    new_df.data = drop_columns_based_on_multiselect(new_df.data, vm_detail_columns_to_show)

    return new_df

# drop columns based on multiselect
def drop_columns_based_on_multiselect(new_df, vm_detail_columns_to_show): 
    if 'vCPU Peak %' not in vm_detail_columns_to_show :
        new_df.drop(columns=['vCPU Peak %'], inplace=True)
    if 'vCPU Peak #' not in vm_detail_columns_to_show :
        new_df.drop(columns=['vCPU Peak #'], inplace=True)
    if 'vCPU Average %' not in vm_detail_columns_to_show :
        new_df.drop(columns=['vCPU Average %'], inplace=True)
    if 'vCPU Average #' not in vm_detail_columns_to_show :
        new_df.drop(columns=['vCPU Average #'], inplace=True)
    if 'vCPU Median %' not in vm_detail_columns_to_show :
        new_df.drop(columns=['vCPU Median %'], inplace=True)
    if 'vCPU Median #' not in vm_detail_columns_to_show :
        new_df.drop(columns=['vCPU Median #'], inplace=True)    
    if 'vCPU 95th Percentile %' not in vm_detail_columns_to_show :
        new_df.drop(columns=['vCPU 95th Percentile %'], inplace=True)
    if 'vCPU 95th Percentile #' not in vm_detail_columns_to_show :
        new_df.drop(columns=['vCPU 95th Percentile #'], inplace=True)    
    if 'vMemory Peak %' not in vm_detail_columns_to_show :
        new_df.drop(columns=['vMemory Peak %'], inplace=True)
    if 'vMemory Peak #' not in vm_detail_columns_to_show :
        new_df.drop(columns=['vMemory Peak #'], inplace=True)    
    if 'vMemory Average %' not in vm_detail_columns_to_show :
        new_df.drop(columns=['vMemory Average %'], inplace=True)
    if 'vMemory Average #' not in vm_detail_columns_to_show :
        new_df.drop(columns=['vMemory Average #'], inplace=True)
    if 'vMemory Median %' not in vm_detail_columns_to_show :
        new_df.drop(columns=['vMemory Median %'], inplace=True)
    if 'vMemory Median #' not in vm_detail_columns_to_show :
        new_df.drop(columns=['vMemory Median #'], inplace=True)    
    if 'vMemory 95th Percentile %' not in vm_detail_columns_to_show :
        new_df.drop(columns=['vMemory 95th Percentile %'], inplace=True)
    if 'vMemory 95th Percentile #' not in vm_detail_columns_to_show :
        new_df.drop(columns=['vMemory 95th Percentile #'], inplace=True)
    return new_df

# Download df as excel file
def download_as_excel(output_to_show):
    print("Download as Excel Function has been executed")
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    output_to_show.to_excel(writer, index=False, sheet_name='Sheet1')
    workbook = writer.book
    worksheet = writer.sheets['Sheet1']
    #format1 = workbook.add_format({'num_format': '0,00'})
    #worksheet.set_column('A:A', 20, format1)
    for col in range(25):
        worksheet.set_column(col, col, 25)
    worksheet.freeze_panes(1, 1)
    writer.save()
    processed_data = output.getvalue()
    return processed_data





