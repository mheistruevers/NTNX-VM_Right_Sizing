import plotly.express as px  # pip install plotly-express
import plotly.graph_objs as go
import streamlit as st  # pip install streamlit
import custom_functions
import pandas as pd
import numpy as np
import warnings

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
warnings.simplefilter("ignore") # Ignore openpyxl Excile File Warning while reading (no default style)

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
            # load excel, filter our relevant tabs and columns, merge all in one dataframe
            main_df = custom_functions.get_data_from_excel(uploaded_file)

            st.sidebar.markdown('---')
            st.sidebar.markdown('## **Filter**')

            vCluster_selected = st.sidebar.multiselect(
                "vCluster selektieren:",
                options=sorted(main_df["Cluster Name"].unique()),
                default=sorted(main_df["Cluster Name"].unique())
            )

            powerstate_selected = st.sidebar.multiselect(
                "VM Status selektieren:",
                options=sorted(main_df["Power State"].unique()),
                default=sorted(main_df["Power State"].unique())
            )

            # Apply Multiselect Filter to dataframe
            custom_df = main_df.query("`Cluster Name`==@vCluster_selected").query("`Power State`==@powerstate_selected")

        except Exception as e:
            content_section.error("##### FEHLER: Die hochgeladene Excel Datei konnte leider nicht ausgelesen werden.")
            content_section.markdown("**Bitte stellen Sie sicher, dass folgende Tabs mit den jeweiligen Spalten hinterlegt sind:**")
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

with header_section:
    st.markdown("<h1 style='text-align: left; color:#034ea2;'>VM Right Sizing Analyse</h1>", unsafe_allow_html=True)
    st.markdown('Ein Hobby-Projekt von [**Martin Stenke**](https://www.linkedin.com/in/mstenke/) zur einfachen Analyse einer Nutanix Collector Auswertung hinsichtlich VM Right Sizing Empfehlungen.')
    st.markdown('***Hinweis:*** Der Nutanix Collector kann neben den zugewiesenen vCPU & vMemory Ressourcen an die VMs ebenfalls die Performance Werte der letzten 7 Tage in 30 Minuten Intervallen aus vCenter/Prism auslesen und bietet anhand dessen eine Möglichkeit für VM Right-Sizing Empfehlungen. Stellen Sie bitte sicher, dass die Auswertung für einen repräsentativen Zeitraum durchgeführt wurde. Für die ausgeschalteten VMs stehen (abhängig davon wie lange diese bereits ausgeschaltet sind) i.d.R. keine Performance Werte (Peak, Average, Median oder 95th Percentile) zur Verfügung - in diesem Fall werden die provisionierten / zugewiesenen Werte verwendet. Auch werden bei allen Performance basierten Werten 20% zusätzlicher Puffer mit eingerechnet. **Generell ist die Empfehlung sich bei den Performance Werten an den 95th Percentile Werten zu orientieren, da diese die tatsächliche Auslastung am besten repräsentieren und nicht durch ggf. kurzzeitige Lastspitzen verfälscht werden.**')
    st.info('***Disclaimer: Hierbei handelt es sich lediglich um ein Hobby Projekt - keine Garantie auf Vollständigkeit oder Korrektheit der Auswertung / Daten.***')
    st.markdown("---")

with content_section: 

    if not custom_df.empty:
        st.success("##### Die folgende Nutanix Collector Auswertung umfasst {}".format(custom_df['Cluster Name'].nunique())+" Cluster und {}".format(custom_df.shape[0])+" VMs.")

        # Generate Overview Dataframes for vCPU & vMemory
        vCPU_overview = custom_functions.generate_vCPU_overview_df(custom_df)
        vMemory_overview = custom_functions.generate_vMemory_overview_df(custom_df)

        # Set bar chart setting to static for both  charts
        bar_chart_config = {'staticPlot': True}
        bar_chart_marker_colors = ['#F36D21', '#4C4C4E', '#6560AB', '#3ABFEF', '#034EA2']

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
            bar_chart_vCPU.update_traces(marker_color=bar_chart_marker_colors)
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
                vMemory_overview.data,
                x = "",
                y = "GiB"
            )
            bar_chart_vMemory.update_traces(marker_color=bar_chart_marker_colors)
            st.plotly_chart(bar_chart_vMemory,use_container_width=True, config=bar_chart_config)

        # Main Section for VM Details
        savings_vCPU = int(vCPU_overview.iat[0,1])-int(vCPU_overview.iat[4,1])
        savings_vMemory = int(vMemory_overview.data.iat[0,1])-int(vMemory_overview.data.iat[4,1])
        st.markdown(f"<h5 style='text-align: center; color:#034EA2;'> In Summe besteht ein mögliches VM Optimierungs-Potenzial von {savings_vCPU} vCPUs und {savings_vMemory} GiB Memory (basierend auf 'provisioned' vs '95th Percentile' Ressourcen-Bedarf).</h5>", unsafe_allow_html=True)
        st.markdown("<h4 style='text-align: center; color:#000000; background-color: #F5F5F5;'>vCPU & vMemory Auslastungs-Verteilung:</h4><br />", unsafe_allow_html=True)
        st.markdown("Die folgenden zwei Diagramme geben einen Überblick wie sich die einzelnen VMs hinsichtlich Ihrer zugewiesenen und tatsächlich verwendeter Ressourcen einsortieren lassen - jeder Punkt repräsentiert dabei eine VM. Das Diagramm ist interaktiv und bietet beim mit der Maus darüber fahren weitergehende Informationen zur der jeweiligen VM.")

        # Generate 2 Columns for vCPu & VMemory Overview tables & graphs
        column_1_2, column_2_2 = st.columns(2)
        with column_1_2:
            scatter_chart_vCPU = px.scatter(        
                custom_df,
                x = "vCPU 95th Percentile %",
                y = "vCPUs",
                hover_name="VM Name",
                hover_data=['vCPU 95th Percentile #']
            )
            scatter_chart_vCPU.update_traces(marker=dict(size=6,color='#034EA2'))
            st.plotly_chart(scatter_chart_vCPU,use_container_width=True)
        with column_2_2:
            scatter_chart_vMemory = px.scatter(        
                custom_df,
                x = "vMemory 95th Percentile %",
                y = "vMemory Size (GiB)",
                hover_name="VM Name",
                hover_data=['vMemory 95th Percentile #']
            )
            scatter_chart_vMemory.update_traces(marker=dict(size=6,color='#034EA2'))
            st.plotly_chart(scatter_chart_vMemory,use_container_width=True)

        st.markdown("<h4 style='text-align: center; color:#000000; background-color: #F5F5F5;'>VM Details:</h4><br/>", unsafe_allow_html=True)
        st.markdown("In der folgenden Tabelle können Sie die vCPU & vMemory Details der einzelnen VMs genauer betrachten. Anhand der Filter können Sie bestimmte Spalten ein und oder ausblenden und so verschiedene umfangreiche Ansichten erhalten. Die Spalten lassen sich auf oder absteigend sortieren und rechts neben der Tabelle erscheint beim darüber fahren ein Vergrößern-Symbol um die Tabelle auf Fullscreen zu vergrößern. Die Daten in der Tabelle untergliedern sich dabei zum einen in die jeweiligen '%' und daraus berechneten Total Werte für vCPU & Memory '#'. Zuletzt lässt sich die Tabelle als Excel Datei speichern.")

        # Generate a Multiselect Filter for Column selection, by default only recommended columns are shown
        vm_detail_columns_to_show = st.multiselect(
            'Wählen Sie die Spalten die angezeigt werden sollen:',
            options=list(custom_df.columns.values),
            default=list(custom_df.iloc[:, [0,1,2,3,10,11,12,19,20]]) # Column index of deafult columns to display
            )

        # Generate Dataframe to be shown on streamlit website
        output_to_show = custom_functions.generate_results_df_for_output(custom_df,vm_detail_columns_to_show)
        st.dataframe(output_to_show)
        
        # Download Section form added in order to avoid reload of download_as_excel function on every filter usage
        form = st.form(key='my-form2')
        submit = form.form_submit_button('Aktuelle Auswertung als Excel herunterladen?')

        if submit:
            st.download_button(
                label='⏬ Download', data=custom_functions.download_as_excel(output_to_show), file_name='VM_Right_Sizing_Analyse.xlsx')