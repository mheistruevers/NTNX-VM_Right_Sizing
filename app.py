import plotly.express as px  # pip install plotly-express
import plotly.graph_objs as go
import streamlit as st  # pip install streamlit
import custom_functions
import pandas as pd
import numpy as np
from PIL import Image
import warnings
import time
from datetime import date

######################
# Page Config
######################
st.set_page_config(page_title="VM Right Sizing Analyse", page_icon='./style/favicon.ico', layout="wide")
# Use CSS Modifications stored in CSS file            
st.markdown(f"<style>{custom_functions.local_css('style/style.css')}</style>", unsafe_allow_html=True)
warnings.simplefilter("ignore") # Ignore openpyxl Excile File Warning while reading (no default style)

######################
# Initialize variables
######################
custom_df = pd.DataFrame() # Initialize Main Dataframe as Empty in order to check whether it has been filled
filter_form_submitted = False

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
    uploaded_file = st.sidebar.file_uploader(label="Laden Sie Ihre Excel basierte Collector Auswertung hier hoch.", type=['xlsx'], help='Diesen Excel Export können Sie entweder direkt aus der Collector Anwendung heraus erzeugen oder über das Collector Portal mittels "Export as .XLS". ')

    if uploaded_file is not None:
        try:
            # Store excel shortterm in AWS for debugging purposes
            if uploaded_file.name not in st.session_state:
                custom_functions.upload_to_aws(uploaded_file)

            # load excel, filter our relevant tabs and columns, merge all in one dataframe
            main_df = custom_functions.get_data_from_excel(uploaded_file)            
               
            st.sidebar.markdown('## **Filter**')

            vCluster_selected = st.sidebar.multiselect(
                "vCluster:",
                options=sorted(main_df["Cluster Name"].unique()),
                default=sorted(main_df["Cluster Name"].unique()), help='Filtern Sie nach dem gewünschten vClustern.'
            )

            powerstate_selected = st.sidebar.multiselect(
                "VM Status:",
                options=sorted(main_df["Power State"].unique()),
                default="poweredOn", help='Filtern Sie nach den gewünschten PowerStatus (PoweredOn ist die empfohlene Einstellung, da i.d.R. nur hier Performance Daten zur Verfügung stehen).'
            )

            performance_type_selected = st.sidebar.selectbox(
                'Performance Vergleichswerte:', ('95th Percentile','Peak','Average','Median'),
                help='Wählen Sie den zu Vergleichzwecken betrachtenden Performance Typ (95th Percentile ist empfohlen).'
            )

            if uploaded_file.name not in st.session_state:
                slack_string = 'Collector VM Right Sizing: '+str(main_df['Cluster Name'].nunique())+' Cluster, '+str(main_df.shape[0])+' VMs.'
                custom_functions.send_slack_message_and_set_session_state(slack_string,uploaded_file)

            # Apply Multiselect Filter to dataframe
            custom_df = main_df.query("`Cluster Name`==@vCluster_selected").query("`Power State`==@powerstate_selected")            

        except Exception as e:             
            content_section.error("##### FEHLER: Die hochgeladene Excel Datei konnte leider nicht ausgelesen werden.")
            content_section.markdown("**Bitte stellen Sie sicher, dass es sich um eine Nutanix Collector Datei handelt welche folgende Tabs mit den jeweiligen Spalten hinterlegt hat:**")
            content_section.markdown("""
                * ***vInfo***
                    * VM Name
                    * Power State
                    * Cluster Name
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
            st.session_state[uploaded_file.name] = True 
            custom_functions.send_slack_message_and_set_session_state('Collector VM Right Sizing ERROR: '+str(e.args),uploaded_file)

with header_section:
    
    st.markdown("<h1 style='text-align: left; color:#034ea2;'>VM Right Sizing Analyse</h1>", unsafe_allow_html=True)
    st.markdown('Ein Hobby-Projekt von [**Martin Stenke**](https://www.linkedin.com/in/mstenke/) zur einfachen Analyse einer [**Nutanix Collector**](https://collector.nutanix.com/) Auswertung hinsichtlich VM Right Sizing Empfehlungen. (Zuletzt aktualisiert: 21.01.2022)')

    remarks_expander = st.expander(label='Hinweise')
    with remarks_expander:
        st.markdown('Der Nutanix Collector kann (im Gegensatz zu z.B. RVTools) neben den zugewiesenen vCPU & vMemory Ressourcen an die VMs ebenfalls die Performance Werte der letzten 7 Tage in 30 Minuten Intervallen aus vCenter/Prism auslesen und bietet anhand dessen eine Möglichkeit für VM Right-Sizing Empfehlungen. Stellen Sie bitte sicher, dass die Auswertung für einen repräsentativen Zeitraum durchgeführt wurde. Für die ausgeschalteten VMs stehen (abhängig davon wie lange diese bereits ausgeschaltet sind) i.d.R. keine Performance Werte (Peak, Average, Median oder 95th Percentile) zur Verfügung - in diesem Fall werden die provisionierten / zugewiesenen Werte verwendet. Auch werden bei allen Performance basierten Werten 20% zusätzlicher Puffer mit eingerechnet. **Generell ist die Empfehlung sich auf die eingeschalteten VMs zu fokussieren und bei den Performance Werten an den 95th Percentile Werten zu orientieren, da diese die tatsächliche Auslastung am besten repräsentieren und nicht durch ggf. kurzzeitige Lastspitzen verfälscht werden.**')
    
    st.info('***Disclaimer: Hierbei handelt es sich lediglich um ein Hobby Projekt - keine Garantie auf Vollständigkeit oder Korrektheit der Auswertung / Daten.***')
    st.markdown("---")

with content_section: 

    if not custom_df.empty:
        st.success("##### Die folgende Nutanix Collector Auswertung umfasst {}".format(custom_df['Cluster Name'].nunique())+" Cluster und {}".format(custom_df.shape[0])+" VMs.")

        # Generate Overview Dataframes for vCPU & vMemory
        vCPU_overview = custom_functions.generate_vCPU_overview_df(custom_df)
        vMemory_overview = custom_functions.generate_vMemory_overview_df(custom_df)

        # Generate 2 Main Columns
        column_1, column_2 = st.columns(2)
        with column_1:
            st.markdown("<h4 style='text-align: center; color:#000000; background-color: #F5F5F5;'>vCPU Gesamt-Auswertung:</h4>", unsafe_allow_html=True)
        with column_2:
            st.markdown("<h4 style='text-align: center; color:#000000; background-color: #F5F5F5;'>vMemory Gesamt-Auswertung:</h4>", unsafe_allow_html=True)
        
        # Generate 4 Columns for vCPU & VMemory Overview tables & graphs
        column_1_1, column_2_1, column_3_1, column_4_1 = st.columns([1,1.7,1,1.7])
        
        with column_1_1:
            # Unfortunately no vertical center implemented in streamlit yet - therefore the following workaround needed
            st.write('')
            st.table(vCPU_overview)

        with column_2_1:        
            bar_chart_vCPU, vCPU_bar_chart_config = custom_functions.generate_bar_charts(vCPU_overview,"vCPU")
            st.plotly_chart(bar_chart_vCPU,use_container_width=True, config=vCPU_bar_chart_config)

        with column_3_1:
            # Unfortunately no vertical center implemented in streamlit yet - therefore the following workaround needed
            st.write('')
            st.table(vMemory_overview)

        with column_4_1:
            bar_chart_vMemory, vMemory_bar_chart_config = custom_functions.generate_bar_charts(vMemory_overview.data,"GiB")
            st.plotly_chart(bar_chart_vMemory,use_container_width=True, config=vMemory_bar_chart_config)

        # Main Section for VM Details
        savings_vCPU, savings_vMemory = custom_functions.get_savings_value(performance_type_selected,vCPU_overview,vMemory_overview.data)
        st.markdown(f"<h5 style='text-align: center; color:#034EA2;'> In Summe besteht ein mögliches VM Optimierungs-Potenzial von {savings_vCPU} vCPUs und {savings_vMemory} GiB Memory (basierend auf 'Provisioned' vs '{performance_type_selected}' Ressourcen-Bedarf).</h5>", unsafe_allow_html=True)
        st.markdown("<h4 style='text-align: center; color:#000000; background-color: #F5F5F5;'>vCPU & vMemory Auslastungs-Verteilung:</h4><br />", unsafe_allow_html=True)
        st.markdown("Die folgenden Diagramme geben einen Überblick wie sich die einzelnen VMs hinsichtlich Ihrer prozentual verwendeten vs Ihrer zugewiesenen Ressourcen verhalten. **Es steht jeweils ein Diagramm bereit welches die VM Auslastung im Bezug zur Anzahl der VMs setzt und zum anderen im Bezug auf die zugewiesenen Ressourcen.** Erstes Diagramm (*ein sog. Histogram in gruppierten 5% Schritten*) bietet einen Überblick wie die prozentuale Auslastung für alle VMs im Verhältnis aussieht, letzteres Diagramm (*ein sog. Scatter Diagramm*) hingegen erlaubt einen Bezug zwischen zugewiesener Ressourcen und tatsächlicher Nutzung auf einzelner VM Ebene.")

        column_1_2, column_2_2 = st.columns(2)
        with column_1_2:
            st.markdown("<h4 style='text-align: center; color:#034EA2;'>vCPU Diagramme</h4>", unsafe_allow_html=True)

            histogram_chart_vCPU, histogram_chart_vCPU_config = custom_functions.generate_histogram_charts(custom_df, "vCPUs", performance_type_selected)
            st.plotly_chart(histogram_chart_vCPU,use_container_width=True, config=histogram_chart_vCPU_config)

            scatter_chart_vCPU, scatter_chart_vCPU_config = custom_functions.generate_scatter_charts(custom_df, "vCPUs", performance_type_selected)
            st.plotly_chart(scatter_chart_vCPU,use_container_width=True, config=scatter_chart_vCPU_config)

        with column_2_2:
            st.markdown("<h4 style='text-align: center; color:#034EA2;'>vMemory Diagramme</h4>", unsafe_allow_html=True)

            histogram_chart_vMemory, histogram_chart_vMemory_config = custom_functions.generate_histogram_charts(custom_df, "vMemory Size (GiB)", performance_type_selected)
            st.plotly_chart(histogram_chart_vMemory,use_container_width=True, config=histogram_chart_vMemory_config)

            scatter_chart_vMemory, scatter_chart_vMemory_config = custom_functions.generate_scatter_charts(custom_df, "vMemory Size (GiB)", performance_type_selected)
            st.plotly_chart(scatter_chart_vMemory,use_container_width=True, config=scatter_chart_vMemory_config)

        st.markdown("<h4 style='text-align: center; color:#000000; background-color: #F5F5F5;'>VM Details:</h4><br/>", unsafe_allow_html=True)
        st.markdown("In der folgenden Tabelle können Sie die vCPU & vMemory Details der einzelnen VMs genauer betrachten. Anhand der Filter können Sie bestimmte Spalten ein und oder ausblenden und so verschiedene umfangreiche Ansichten erhalten. Die Spalten lassen sich auf oder absteigend sortieren und rechts neben der Tabelle erscheint beim darüber fahren ein Vergrößern-Symbol um die Tabelle auf Fullscreen zu vergrößern. Die Daten in der Tabelle untergliedern sich dabei zum einen in die jeweiligen '%' und daraus berechneten Total Werte für vCPU & Memory '#'. Zuletzt lässt sich die Tabelle als Excel Datei speichern.")

        # Generate a Multiselect Filter for Column selection, by default only recommended columns are shown
        default_columns = custom_functions.get_default_columns_to_show(performance_type_selected)

        vm_detail_columns_to_show = st.multiselect(
            'Wählen Sie die Spalten die angezeigt werden sollen:',
            options=list(custom_df.columns.values),
            default=list(custom_df.iloc[:, default_columns]) # Column index of deafult columns to display
            )

        # Generate Dataframe to be shown on streamlit website
        output_to_show = custom_functions.generate_results_df_for_output(custom_df,vm_detail_columns_to_show)
        
        st.dataframe(output_to_show)

        with st.form(key='download_form'):
            submit = st.form_submit_button('Aktuelle Auswertung als Excel herunterladen?')

        if submit:
            with st.spinner('Download wird vorbereitet...'):
                time.sleep(5)
            st.success('Done!')
            st.download_button(
                label='⏬ Download', data=custom_functions.download_as_excel(output_to_show,vCPU_overview,vMemory_overview), file_name='VM_Right_Sizing_Analyse.xlsx')