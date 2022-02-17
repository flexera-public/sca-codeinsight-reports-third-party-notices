# sca-codeinsight-reports-third-party-notices

The `sca-codeinsight-reports-third-party-notices` repository is a example report for Revenera's Code Insight product. This report allows a user to get a quick high level summary of the inventory items within a project. This report will take into account any child projects (recursively).

This repository utilizes the following via CDN for the creation of the report artifacts.

-  [Bootstrap](https://getbootstrap.com/)

## Prerequisites

**Code Insight Release Requirements**

|Repository Tag | Minimum Code Insight Release |
|--|--|
|1.0.x |2022R1 |

**Repository Cloning**

This repository should be cloned directly into the **$CODEINSIGHT_INSTALLDIR/custom_report_scripts** directory. If no prior custom reports has been installed, this directory will need to be created prior to cloning.

**Submodule Repositories**

This repository contains two submodule repositories for code that is used across multiple projects.  There are two options for cloning this repository and ensuring that the required submodules are also installed.

Clone the report repository use the recursive option to automatically pull in the required submodules

	git clone --recursive

 Alternatively clone the report repository and then clone the submodules separately by entering the cloned directory and then pulling down the necessary submodules code via   

	git submodule init

	git submodule update

**Python Requirements**

The required python modules can be installed with the use of the [requirements.txt](requirements.txt) file which can be loaded via.

	pip install -r requirements.txt

**Data Services Requirement**

The execution of this report will require external network access in order to obtain the specific notice information for each item within the project invenetory.  The specific URLs required in addition to the default URLs for standard Code Insight usage are:
- https://login.flexera.com 
- https://sca-api.revenera.com 

## Configuration and Report Registration
 
For registration, as well as data services purposes, the file **server_properties.json** should be created and located in the **$CODEINSIGHT_INSTALLDIR/custom_report_scripts/** directory.  This file contains a json with information required to register the report within Code Insight.   The file can be populated as shown here:

>     {
>         "core.server.url": "FQDN or IP Addess for Code Insight server" ,
>         "core.server.token" : "Admin authorization token from Code Insight",
>     }

The value for core.server.url is also used within [create_report.py](create_report.py) for any project or inventory based links back to the Code Insight server within a generated report.

If the common **server_properties.json** files is not used then the information the the following files will need to be updated:

[registration.py](registration.py)  -  Update the **baseURL** and **adminAuthToken** values. These settings allow the report itself to be registered on the Code Insight server.

[create_report.py](create_report.py)  -  Update the **baseURL** value. This URL is used for links within the reports.

Report option default values can also be specified in [registration.py](registration.py) within the reportOptions dictionaries.



### Registering the Report

Prior to being able to call the script directly from within Code Insight it must be registered. The [registration.py](registration.py) file can be used to directly register the report once the contents of this repository have been added to the custom_report_script folder at the base Code Insight installation directory.

To register this report:

	python registration.py -reg

To unregister this report:
	
	python registration.py -unreg

To update this report configuration:
	
	python registration.py -update

## Usage

This report is executed directly from within Revenera's Code Insight product. From the project reports tab of each Code Insight project it is possible to *generate* the **Third Party Notices** via the Custom Report Framework.

The following report options can be set once the report generation has been initiated:

- Including child projects (True/False) - Determine if child project data will be included or not.
- Replace Existing Notices Text Field Value (True/False) - Replace existing "Notices Text" field with gathered notices if already populated

The Code Insight Custom Report Framework will provide the following to the custom report when initiated:

- Project ID
- Report ID
- Authorization Token

For this example report these three items are passed on to a batch or sh file which will in turn execute a python script. This script will then:

- Collect data for the report via REST API using the Project ID and Authorization Token
- Take this collected data and generate the following:
  - An html version of the third party notices file
  - A text version of the third party notices file
- The html file will be marked as the *"viewable"* file
- A zip file will be created containing all files which will be the *"downloadable"* file.
- Create a zip file with the viewable file and the downloadable file
- Upload this combined zip file to Code Insight via REST API
- Delete the report artifacts that were created as the script ran

## License

[MIT](LICENSE)