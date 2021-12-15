# Nutanix Collector VM Right Sizing Analysis.
The purpose of **Nutanix Collector VM Right Sizing Analysis** is to automate and simplify the analysis of [Nutanix Collector](https://collector.nutanix.com/) Excel based exports. This tool gives a visual representation of the configured VM ressources and clear recommendation for VM Right Sizing based on the information contained within the Collector export.

Nutanix Collector is a completly free Windows / Mac or Linux based application that gathers information of connected VMware ESXi and Nutanix environments. In particular Nutanix collector offers the option to gather not only the configured VM ressource information but rather also performance based information for each individual VM. Based on this utilization information recommendations can be made how the assigned ressources can be adjusted to better fit the workload running inside the VM. 

Often VM's are heavily oversized which leads to wasted ressources and unneccessary overhead. Therefore the **Nutanix Collector VM Right Sizing Analysis** Tool enables you to get a good overview of the configured vs consumed ressources in order to derive meaningful insights on the analyzed environment.  

If you are interested, find out more at the [*Nutanix Collector VM Right Sizing Analysis - WebApp](https://share.streamlit.io/mstenke/ntnx-vm_right_sizing/main/app.py) and get started right away.
___

## Built maily with

* [Python](https://www.python.org/)
* [Streamlit](https://streamlit.io/)

## Author

* **Martin Stenke** - reach out on [Linkedin](https://www.linkedin.com/in/mstenke/)

