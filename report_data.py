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

from datetime import datetime # TODO Remove after temp inventory testing

import CodeInsight_RESTAPIs.project.get_child_projects
import CodeInsight_RESTAPIs.project.get_project_inventory
import CodeInsight_RESTAPIs.license.license_lookup
import CodeInsight_RESTAPIs.inventory.update_inventory
import API_license_text
import common_licenses

logger = logging.getLogger(__name__)



#-------------------------------------------------------------------#
def gather_data_for_report(baseURL, projectID, authToken, reportName, reportOptions):
    logger.info("Entering gather_data_for_report")

    # Parse report options
    includeChildProjects = reportOptions["includeChildProjects"]  # True/False
    generateReport = reportOptions["generateReport"]  # True/False
    overrideExistingNoticesText = reportOptions["overrideExistingNoticesText"]  # True/False

    projectList = [] # List to hold parent/child details for report
    inventoryData = {}  # Create a dictionary containing the inventory data using inventoryID as keys
    componentVersionLicenses = {}
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
            inventoryID = inventoryItem["id"]
            componentName = inventoryItem["componentName"]
            componentVersionName = inventoryItem["componentVersionName"]

            logger.debug("        Processing license details for '%s - %s  (%s)'" %(componentName, componentVersionName, inventoryID))
            
            componentVersionId = inventoryItem["componentVersionId"]
            selectedLicenseSPDXIdentifier = inventoryItem["selectedLicenseSPDXIdentifier"]
            selectedLicenseId = str(inventoryItem["selectedLicenseId"])
            url = inventoryItem["url"]
            componentUrl = inventoryItem["componentUrl"]
            noticesText = inventoryItem["noticesText"]
            selectedLicenseName = inventoryItem["selectedLicenseName"]
            selectedLicenseUrl = inventoryItem["selectedLicenseUrl"]

            # TODO Which URL should be used
            if componentVersionId != "N/A":
                componentVersionLicenses[componentVersionId] = selectedLicenseId

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

    logger.debug("Total number of components within inventory: %s" %len(componentVersionLicenses))
    
    # With the full inventory list (including child projects) get gathered notices for each item in a bulk call
    licenseTextData = API_license_text.get_license_text(componentVersionLicenses)
    # TODO Check for any issues while collecting the notices
    
    # Try to determine what licenes were gathererd for each invnetory item
    gatheredNotices = determine_licenses(licenseTextData)

    logger.debug("Total number of collected notices obtained: %s" %len(gatheredNotices))

    # Update each inventory notice text for the report with the gathered notices or the template notices
    for inventoryID in inventoryData:
        componentName = inventoryData[inventoryID]["componentName"]
        componentVersionName = inventoryData[inventoryID]["componentVersionName"]
        logger.debug("Processing notices for '%s - %s  (%s)'" %(componentName, componentVersionName, inventoryID))
        componentVersionId = inventoryData[inventoryID]["componentVersionId"]
        isCommonLicense = inventoryData[inventoryID]["isCommonLicense"]
        selectedLicenseSPDXIdentifier = inventoryData[inventoryID]["selectedLicenseSPDXIdentifier"]
        selectedLicenseId = inventoryData[inventoryID]["selectedLicenseId"]
        originalNoticesText = inventoryData[inventoryID]["noticesText"]

        # Determine if the the Notices Text needs to be updated
        if isCommonLicense:
            logger.info("    Component has common license")
            # Is there information already there than should be used?
            if originalNoticesText in emptyNotices:
                logger.info("        Using stock/template license text")
                updateNoticesText = commonNotices[selectedLicenseId]["reportNoticeText"]
            else:
                # Since there is custom data make sure to use it and not consider it a common license
                logger.info("        Using existing license text")
                updateNoticesText = originalNoticesText
                inventoryData[inventoryID]["isCommonLicense"] = False

        elif componentVersionId in gatheredNotices: 
            # Replace any data that is already there
            logger.info("    Component has gathered license text")

            if overrideExistingNoticesText or originalNoticesText in emptyNotices:
                logger.info("        Using license text obtained during collection process")
                # Update the notices with the gathered license text
                componentNotices = gatheredNotices[componentVersionId] # This returns a list of notices 

                # Is there a key for the license that was selected?
                if selectedLicenseSPDXIdentifier in componentNotices:
                    logger.info("            License match for selected within gathered notices")
                    updateNoticesText = componentNotices[selectedLicenseSPDXIdentifier]
                else:
                    logger.info("            Unable to find specific match.  Add all collected notices text")
                    # Update the notices will all possible license text that was found
                    updateNoticesText = ""
                    for SPDXIdendifier in componentNotices:
                        updateNoticesText += componentNotices[SPDXIdendifier]
                        updateNoticesText += "\n\n======================================================\n\n"

                logger.info("        Update the notices field for the inventory item")
                if originalNoticesText != updateNoticesText:
                    CodeInsight_RESTAPIs.inventory.update_inventory.update_inventory_notices_text(inventoryID, updateNoticesText, baseURL, authToken)
                    # TODO what if not analsyst does this?
                    # print and log message if non analsyst
                else:
                    logger.info("        Existing notices text is the same as the gathered text.  Inventory item not updated")

            else:
                # Keep the data the same as it was
                updateNoticesText = originalNoticesText

        else:
            # Not a specific stock license and no information was collected
            # Is there information already there that should be used?
            if originalNoticesText in emptyNotices:
                logger.warning("    Not a specific common license and no gathered license data")
                updateNoticesText = "*** Notices text not available.  Manual review required. ***"
            else:
                # Since there is custom data make sure to use it and not consider it a common license
                logger.info("    Notices have been found within the Notices Text field so use those")
                updateNoticesText = originalNoticesText



        # Update the notices information for the inventory item based on the outcome above
        inventoryData[inventoryID]["noticesText"] = updateNoticesText


    # Sort the dictionary based on the component name and version
    sortedInventoryItems = OrderedDict( sorted(inventoryData.items(), key=lambda x: (x[1]["componentName"], x[1]["componentVersionName"]) ))
    sortedcommonNotices = OrderedDict( sorted(commonNotices.items(), key=lambda x: (x[1]["commonLicenseName"] )))
  
    # Build up the data to return for the
    reportData = {}
    reportData["projectName"] = projectHierarchy["name"]
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

#-----------------------------------------------#
def determine_licenses(licenseTextResults):
    logger.debug("        Entering determine_licenses.")

    inidicators_MIT = ["Permission is hereby granted, free of charge"]
    inidicators_Apache_20 = ["http://www.apache.org/licenses/LICENSE-2.0"]
    inidicators_LGPL_21_or_later = ["GNU Lesser General Public License (LGPL), version 2.1 or later'"]

    licenseData = {}
    # Cycle thru each row to create a dict per license 
    for versionID, licenseText  in licenseTextResults:
        licenseType = "unknown"

        for indicator in inidicators_MIT:
            if indicator in licenseText:
                licenseType="MIT"

        for indicator in inidicators_Apache_20:
            if indicator in licenseText:
                licenseType="Apache-2.0"
        


        if versionID in licenseData:
            licenseData[versionID][licenseType] = licenseText
        else:
            licenseData[versionID] = {}
            licenseData[versionID][licenseType] = licenseText

    logger.info("Exiting get_licese_text")

    return licenseData