'''
Copyright 2021 Flexera Software LLC
See LICENSE.TXT for full license text
SPDX-License-Identifier: MIT

Author : sgeary  
Created On : Thu Dec 16 2021
File : report_data.py
'''
import logging
from collections import OrderedDict
import time

import CodeInsight_RESTAPIs.project.get_child_projects
import CodeInsight_RESTAPIs.project.get_project_inventory
import CodeInsight_RESTAPIs.license.license_lookup
import CodeInsight_RESTAPIs.project.get_project_information

import common_licenses

logger = logging.getLogger(__name__)

#-------------------------------------------------------------------#
def gather_data_for_report(baseURL, projectID, authToken, reportName, reportOptions):
    logger.info("Entering gather_data_for_report")

    # Parse report options
    includeChildProjects = reportOptions["includeChildProjects"]  # True/False
    includeComponentVersions = reportOptions["includeComponentVersions"]  # True/False

    projectList = [] # List to hold parent/child details for report
    inventoryData = {}  # Create a dictionary containing the inventory data using inventoryID as keys
    commonNotices = {}
    emptyNotices = ["", "N/A"]

    # Get the list of parent/child projects start at the base project
    projectHierarchy = CodeInsight_RESTAPIs.project.get_child_projects.get_child_projects_recursively(baseURL, projectID, authToken)

    # Create a list of project data sorted by the project name at each level for report display  
    # Add details for the parent node
    nodeDetails = {}
    nodeDetails["parent"] = "#"  # The root node
    nodeDetails["projectName"] = projectHierarchy["name"]
    nodeDetails["projectID"] = projectHierarchy["id"]
    nodeDetails["projectLink"] = baseURL + "/codeinsight/FNCI#myprojectdetails/?id=" + str(projectHierarchy["id"]) + "&tab=projectInventory"

    projectList.append(nodeDetails)

    if includeChildProjects:
        projectList = create_project_hierarchy(projectHierarchy, projectHierarchy["id"], projectList, baseURL)
    else:
        logger.debug("Child hierarchy disabled")

    applicationDetails = determine_application_details(baseURL, projectHierarchy["name"], projectID, authToken)
    applicationNameVersion = applicationDetails["applicationNameVersion"]

    #  Gather the details for each project and summerize the data
    for project in projectList:
        projectID = project["projectID"]
        projectName = project["projectName"]

        # Get project information with rollup summary data
        logger.info("    Get inventory for %s" %projectName)

        try:
            projectDetails= CodeInsight_RESTAPIs.project.get_project_inventory.get_project_inventory_details_without_vulnerabilities(baseURL, projectID, authToken)
        except:
            logger.error("    No Project Information Returned for %s!" %projectName)
            print("No Project Information Returned for %s." %projectName)
            break
        
        # Cycle through the inventory to get the required data
        for inventoryItem in projectDetails["inventoryItems"]:
            componentVersionId = inventoryItem["componentVersionId"]

            # Is this a component?
            if inventoryItem["type"] != "Component":
                continue

            inventoryID = inventoryItem["id"]
            componentName = inventoryItem["componentName"]

            # Will the version numbers for the components be displayed in the report?
            if includeComponentVersions:
                componentVersionName = inventoryItem["componentVersionName"]
                
                if componentVersionName == "N/A":
                    componentVersionName = ""
            else:
                componentVersionName = ""

            logger.debug("        Processing license details for '%s - %s  (%s)'" %(componentName, componentVersionName, inventoryID))
            
            componentVersionId = inventoryItem["componentVersionId"]
            selectedLicenseSPDXIdentifier = inventoryItem["selectedLicenseSPDXIdentifier"]
            selectedLicenseId = str(inventoryItem["selectedLicenseId"])
            url = inventoryItem["url"]  # TODO Which URL should be used
            componentUrl = inventoryItem["componentUrl"]
            noticesText = inventoryItem["noticesText"]
            selectedLicenseName = inventoryItem["selectedLicenseName"]
            selectedLicenseUrl = inventoryItem["selectedLicenseUrl"]

            # Clean up license details for report
            if selectedLicenseName == "I don't know":
                selectedLicenseName = "Unknown"

            if selectedLicenseSPDXIdentifier == "I don't know":
                selectedLicenseSPDXIdentifier = "Unknown"

            # Collect the standard license text details if required
            if selectedLicenseId in common_licenses.commonLicenses.keys():
                isCommonLicense = True

                if selectedLicenseId in commonNotices:
                    logger.info("            License details already available for %s" %commonNotices[selectedLicenseId]["commonLicenseName"])

                else:
                    commonNotices[selectedLicenseId] = gather_common_license_details(baseURL, selectedLicenseId, authToken)
                    logger.info("            Collected License details for %s" %commonNotices[selectedLicenseId]["commonLicenseName"])

            elif selectedLicenseId == "-1":
                logger.warning("            The license was not selected for this inventory item")
                isCommonLicense = False

            else:
                # This is not a license where the templatize text will be used
                isCommonLicense = False


            # Manage the information to be displayed in the report itself for license text
            if isCommonLicense:
                # Since this is a common licnese the stock text will be used
                noticesText = ""
                # TODO   Add a check into invnentory history to see if field was every modified by a user
            else:
                if noticesText in emptyNotices:
                    logger.warning("    Not a specific common license and no gathered license data")
                    noticesText = "*** Notices text not available.  Manual review required. ***"
                else:
                    logger.info("    Notices have been found within the Notices Text field so use those")


            # Store the data for the inventory item for reporting
            inventoryData[inventoryID] = {
                "componentName" : componentName,
                "componentVersionName" : componentVersionName,
                "componentVersionId" : componentVersionId,
                "selectedLicenseName": selectedLicenseName,
                "selectedLicenseSPDXIdentifier" : selectedLicenseSPDXIdentifier,
                "selectedLicenseId" : selectedLicenseId,
                "selectedLicenseUrl" : selectedLicenseUrl,
                "isCommonLicense" : isCommonLicense,
                "componentUrl" : componentUrl,
                "noticesText" : noticesText
            }

    logger.debug("Total number of components within inventory: %s" %len(inventoryData)) 
     

    # Sort the dictionary based on the component name and version
    sortedInventoryItems = OrderedDict( sorted(inventoryData.items(), key=lambda x: (x[1]["componentName"], x[1]["componentVersionName"]) ))
    sortedcommonNotices = OrderedDict( sorted(commonNotices.items(), key=lambda x: (x[1]["commonLicenseName"] )))
  
    # Build up the data to return for the
    reportData = {}
    reportData["projectName"] = projectHierarchy["name"]
    reportData["applicationNameVersion"] = applicationNameVersion
    reportData["reportName"] = reportName
    reportData["projectList"] = projectList
    reportData["inventoryData"] = sortedInventoryItems
    reportData["commonNotices"] = sortedcommonNotices

    logger.info("Exiting gather_data_for_report")

    return reportData



#----------------------------------------------#
def create_project_hierarchy(project, parentID, projectList, baseURL):
    logger.debug("        Entering create_project_hierarchy.  Parent Id %s" %parentID)

    # Are there more child projects for this project?
    if len(project["childProject"]):

        # Sort by project name of child projects
        for childProject in sorted(project["childProject"], key = lambda i: i['name'] ) :

            nodeDetails = {}
            nodeDetails["projectID"] = childProject["id"]
            nodeDetails["parent"] = parentID
            nodeDetails["projectName"] = childProject["name"]
            nodeDetails["projectLink"] = baseURL + "/codeinsight/FNCI#myprojectdetails/?id=" + str(childProject["id"]) + "&tab=projectInventory"

            projectList.append( nodeDetails )

            create_project_hierarchy(childProject, childProject["id"], projectList, baseURL)

    return projectList

#----------------------------------------------#
def gather_common_license_details(baseURL, selectedLicenseId, authToken):
    logger.debug("        Entering gather_common_license_details.")

    licenseDetails = CodeInsight_RESTAPIs.license.license_lookup.get_license_details(baseURL, selectedLicenseId, authToken)

    stockLicenseDetails= {}
    stockLicenseDetails["commonLicenseName"] = licenseDetails["name"]
    stockLicenseDetails["commonLicenseURL"] = licenseDetails["url"]
    stockLicenseDetails["spdxIdentifier"] = licenseDetails["spdxIdentifier"]
    stockLicenseDetails["reportNoticeText"] = licenseDetails["text"]
    logger.debug("            Adding %s to stock license details" %licenseDetails["name"])

    return stockLicenseDetails


#----------------------------------------------#
def determine_application_details(baseURL, projectName, projectID, authToken):
    logger.debug("Entering determine_application_details.")
    # Create a application name for the report if the custom fields are populated
    # Default values
    applicationName = projectName
    applicationVersion = ""
    applicationPublisher = ""
    applicationDetailsString = ""

    projectInformation = CodeInsight_RESTAPIs.project.get_project_information.get_project_information_summary(baseURL, projectID, authToken)

    # Project level custom fields added in 2022R1
    if "customFields" in projectInformation:
        customFields = projectInformation["customFields"]

        # See if the custom project fields were propulated for this project
        for customField in customFields:

            # Is there the reqired custom field available?
            if customField["fieldLabel"] == "Application Name":
                if customField["value"]:
                    applicationName = customField["value"]

            # Is the custom version field available?
            if customField["fieldLabel"] == "Application Version":
                if customField["value"]:
                    applicationVersion = customField["value"]     

            # Is the custom Publisher field available?
            if customField["fieldLabel"] == "Application Publisher":
                if customField["value"]:
                    applicationPublisher = customField["value"]    



    # Join the custom values to create the application name for the report artifacts
    if applicationName != projectName:
        if applicationVersion != "":
            applicationNameVersion = applicationName + " - " + applicationVersion
        else:
            applicationNameVersion = applicationName
    else:
        applicationNameVersion = projectName

    if applicationPublisher != "":
        applicationDetailsString += "Publisher: " + applicationPublisher + " | "

    # This will either be the project name or the supplied application name
    applicationDetailsString += "Application: " + applicationName + " | "

    if applicationVersion != "":
        applicationDetailsString += "Version: " + applicationVersion
    else:
        # Rip off the  | from the end of the string if the version was not there
        applicationDetailsString = applicationDetailsString[:-3]

    applicationDetails = {}
    applicationDetails["applicationName"] = applicationName
    applicationDetails["applicationVersion"] = applicationVersion
    applicationDetails["applicationPublisher"] = applicationPublisher
    applicationDetails["applicationNameVersion"] = applicationNameVersion
    applicationDetails["applicationDetailsString"] = applicationDetailsString

    logger.info("    applicationDetails: %s" %applicationDetails)

    return applicationDetails