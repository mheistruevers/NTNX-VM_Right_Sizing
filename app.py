import plotly.express as px  # pip install plotly-express
import plotly.graph_objs as go
import streamlit as st  # pip install streamlit
import custom_functions
import pandas as pd

######################
# Page Config
######################
st.set_page_config(page_title="VM Right Sizing Analyse", page_icon='favicon.ico', layout="wide")
hide_streamlit_style = """
            <style>
            header {visibility: hidden;}
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            table td:nth-child(1) {display: none}
            table th:nth-child(1) {display: none}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 
custom_df = pd.DataFrame() # Initialize Main Dataframe as Empty in order to check whether it has been filled

######################
# Page sections
######################

header_section = st.container() # Description of page & what it is about
content_section = st.container() # Content of page - either error message if wrong excel file or analysis content


######################
# Page content
######################



with st.sidebar:
    st.markdown('# **Upload**')
    uploaded_file = st.sidebar.file_uploader(label="Laden Sie Ihre Excel basierte Collector Auswertung hier hoch.", type=['xlsx'])   

    if uploaded_file is not None:
        try:
            
            df = custom_functions.get_data_from_excel(uploaded_file)
            df_vInfo = custom_functions.get_tabs_df_from_excel(df, "vInfo")
            df_vCPU = custom_functions.get_tabs_df_from_excel(df, "vCPU")
            df_vMemory = custom_functions.get_tabs_df_from_excel(df, "vMemory")
            
            #df_vInfo = 
            #print("test davor")
            #print(df[df['vInfo'])
            #print("test danach")
            st.sidebar.markdown('---')
            st.sidebar.markdown('## **Filter**')

            vCluster_selected = st.sidebar.multiselect(
                "vCluster selektieren:",
                options=sorted(df_vInfo["Cluster_Name"].unique()),
                default=sorted(df_vInfo["Cluster_Name"].unique())
            )
            #options=sorted(df_vInfo["Cluster_Name"].unique()),
            #default=sorted(df_vInfo["Cluster_Name"].unique())

            powerstate_selected = st.sidebar.multiselect(
                "VM Status selektieren:",
                options=sorted(df_vInfo["Power_State"].unique()),
                default=sorted(df_vInfo["Power_State"].unique())
            )

            # Main Calculation for Dataframe which is used for most calculcations based on multiselect selection
            custom_df = custom_functions.get_custom_df_main(df_vInfo, df_vCPU, df_vMemory, vCluster_selected, powerstate_selected)

        except Exception as e:
            content_section.error("FEHLER: Die hochgeladene Excel Datei konnte leider nicht ausgelesen werden.")
            content_section.markdown("**Bitte stellen Sie sicher, dass folgende Tabs mit den jeweiligen Spalten hinterlegt sind:**")
            content_section.markdown("""
                * ***vInfo***
                    * VM Name
                    * Power State
                    * Cluster Name
                    * Host Name
                    * MOID
                * ***vCPU***
                    * vCPUs
                    * Peak %
                    * Average %
                    * Median %
                    * 95thPercentile % (recommended)
                    * MOID
                * ***vMemory***
                    * Size (MiB)
                    * Peak %
                    * Average %
                    * Median %
                    * 95th Percentile % (recommended)
                    * MOID
                """)
            content_section.markdown("---")
            content_section.markdown("Im folgenden die genaue Fehlermeldung für das Troubleshooting:")
            content_section.exception(e)

with header_section:
    st.markdown("<h1 style='text-align: left; color:#034ea2;'>VM Right Sizing Analyse</h1>", unsafe_allow_html=True)
    st.markdown('Ein Hobby-Projekt von [**Martin Stenke**](https://www.linkedin.com/in/mstenke/) zur einfachen Analyse einer Nutanix Collector Auswertung hinsichtlich VM Right Sizing Empfehlungen.')
    st.markdown('***Hinweis:*** Der Nutanix Collector kann neben den zugewiesenen vCPU & vMemory Ressourcen an die VMs ebenfalls die Performance Werte der letzten 7 Tage aus vCenter auslesen und bietet anhand dessen eine Möglichkeit für VM Right-Sizing Empfehlungen. Stellen Sie bitte sicher, dass die Auswertung für einen repräsentativen Zeitraum durchgeführt wurde. Für die ausgeschalteten VMs stehen (abhängig davon wie lange diese bereits ausgeschaltet sind) i.d.R. keine Performance Werte (Peak, Average, Median oder 95th Percentile) zur Verfügung - in diesem Fall werden die provisionierten / zugewiesenen Werte verwendet. Auch werden bei allen Performance basierten Werten 20% zusätzlicher Puffer mit eingerechnet. **Generell ist die Empfehlung sich bei den Performance Werten an den 95th Percentile (95% Prozent) Werten zu orientieren, da diese die tatsächliche Auslastung am besten repräsentieren und nicht durch ggf. kurzzeitige Lastspitzen verfälscht werden.**')
    st.info('***Disclaimer: Hierbei handelt es sich lediglich um ein Hobby Projekt - keine Garantie auf Vollständigkeit oder Korrektheit der Auswertung / Daten.***')
    st.markdown("---")

with content_section: 

    if not custom_df.empty:

        # Generate Overview Dataframes for vCPU & vMemory
        vCPU_overview = custom_functions.generate_vCPU_overview_df(custom_df)
        vMemory_overview = custom_functions.generate_vMemory_overview_df(custom_df)

        # Set bar chart setting to static for both  charts
        bar_chart_config = {'staticPlot': True}
        bar_chart_marker_colors = ['#F36D21', '#034EA2', '#034EA2', '#034EA2', '#B0D235']

        # Generate 2 Main Columns
        column_1, column_2 = st.columns(2)
        with column_1:
            st.markdown("<h4 style='text-align: center; color:#000000; background-color: #F5F5F5;'>vCPU Gesamt-Auswertung:</h4>", unsafe_allow_html=True)
        with column_2:
            st.markdown("<h4 style='text-align: center; color:#000000; background-color: #F5F5F5;'>vMemory Gesamt-Auswertung:</h4>", unsafe_allow_html=True)
        
        # Generate 4 Columns for vCPu & VMemory Overview tables & graphs
        column_1_1, column_2_1, column_3_1, column_4_1 = st.columns(4)
        
        with column_1_1:
            # Unfortunately no vertical center implemented in streamlit yet - therefore the following workaround needed
            st.write('')
            st.write('')
            st.write('')
            st.write('')
            st.write('')
            st.write('')
            st.write('')
            st.table(vCPU_overview)

        with column_2_1:        
            bar_chart_vCPU = px.bar(        
                vCPU_overview,
                x = "",
                y = "vCPU"
            )
            bar_chart_vCPU.update_traces(marker_color=bar_chart_marker_colors) # Nutanix Blue
            st.plotly_chart(bar_chart_vCPU,use_container_width=True, config=bar_chart_config)

        with column_3_1:
            # Unfortunately no vertical center implemented in streamlit yet - therefore the following workaround needed
            st.write('')
            st.write('')
            st.write('')
            st.write('')
            st.write('')
            st.write('')
            st.write('')
            st.table(vMemory_overview)

        with column_4_1:
            bar_chart_vMemory = px.bar(        
                vMemory_overview,
                x = "",
                y = "GiB"
            )
            #bar_chart_vMemory.update_traces(marker_color='#034EA2') # Nutanix Blue
            bar_chart_vMemory.update_traces(marker_color=bar_chart_marker_colors)
            st.plotly_chart(bar_chart_vMemory,use_container_width=True, config=bar_chart_config)

        # Main Section for VM Details
        st.markdown("---")
        st.markdown('#### VM Details:')
        st.markdown("In der folgenden Tabelle können Sie die vCPU & vMemory Details der einzelnen VMs genauer betrachten. Anhand der Filter können Sie bestimmte Spalten ein und oder ausblenden und so verschiedene umfangreiche Ansichten erhalten. Die Spalten lassen sich auf oder absteigend sortieren und rechts neben der Tabelle erscheint beim darüber fahren ein Vergrößern-Symbol um die Tabelle auf Fullscreen zu vergrößern. Zuletzt lässt sich die Tabelle als Excel File speichern. Die Daten in der Tabelle untergliedern sich dabei zum einen in die jeweiligen '%' und daraus berechneten Total Werte für vCPU & Memory '#'.")

        # Generate a Multiselect Filter for Column selection, by default only recommended columns are shown
        vm_detail_columns_to_show = st.multiselect(
            'Wählen Sie die Spalten die angezeigt werden sollen:',
            ["vCPU Peak %", "vCPU Peak #", "vCPU Average %", "vCPU Average #", "vCPU Median %", "vCPU Median #", "vCPU 95th Percentile %", "vCPU 95th Percentile #", "vMemory Peak %", "vMemory Peak #", "vMemory Average %", "vMemory Average #", "vMemory Median %", "vMemory Median #", "vMemory 95th Percentile %", "vMemory 95th Percentile #"],
            ["vCPU 95th Percentile %", "vCPU 95th Percentile #", "vMemory 95th Percentile %", "vMemory 95th Percentile #"])

        # Generate Dataframe to be shown on streamlit website
        output_to_show = custom_functions.generate_results_df_for_output(custom_df,vm_detail_columns_to_show)
        st.dataframe(output_to_show)
        
        # Offer option to save Dataframe as Excel
        df_xlsx = custom_functions.download_as_excel(output_to_show)
        st.download_button(label='⏬ Aktuelle Auswertung herunterladen (Excel Format)',
                                    data= df_xlsx,
                                    file_name= 'VM_Right_Sizing_Analyse.xlsx')


