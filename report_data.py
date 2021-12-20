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
import report_license_text


logger = logging.getLogger(__name__)

uniqueLicenseIdentifiers = []
uniqueLicenseIdentifiers.append("MIT")

#-------------------------------------------------------------------#
def gather_data_for_report(baseURL, projectID, authToken, reportName, reportOptions):
    logger.info("Entering gather_data_for_report")

    # Parse report options
    includeChildProjects = reportOptions["includeChildProjects"]  # True/False
    updateNoticesText = reportOptions["updateNoticesText"]  # True/False

    projectList = [] # List to hold parent/child details for report
    inventoryData = {}  # Create a dictionary containing the inventory data using inventoryID as keys
    stockLicenseDetails = {}
    notices = {}
    commonNotices = {}

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

            logger.debug("        Processing license for %s - %s" %(componentName, componentVersionName))
            
            componentVersionId = inventoryItem["componentVersionId"]
            selectedLicenseSPDXIdentifier = inventoryItem["selectedLicenseSPDXIdentifier"]
            selectedLicenseId = inventoryItem["selectedLicenseId"]
            url = inventoryItem["url"]
            componentUrl = inventoryItem["componentUrl"]
            noticesText = inventoryItem["noticesText"]
            asFoundLicenseText = inventoryItem["asFoundLicenseText"]
            selectedLicenseName = inventoryItem["selectedLicenseName"]
            selectedLicenseUrl = inventoryItem["selectedLicenseUrl"]


            # TODO Which URL should be used
       
            # Do we need to update the notices?
            if updateNoticesText:
                print("Update notices for inventory item %s" %inventoryID)
                print("Get information for component version ID  %s" %componentVersionId)

                #TODO only update if it is a unique licenes?  Compare to other text in case there is a copy right?
  
                #noticesText = report_license_text.get_license_text(componentVersionId)

            # What license text should we use?
            if noticesText != "N/A":
                logger.info("            Using notices text field")
                reportNoticeText = noticesText
            elif asFoundLicenseText != "N/A" :   # As found license text is a tuple for some reason?
                print("asFoundLicenseText is %s" %asFoundLicenseText)
                logger.info("            Using as found license text field")
                reportNoticeText = asFoundLicenseText
            else:
                logger.info("            Using as stock license text details")

                # Get the stock license text
                if selectedLicenseId in stockLicenseDetails:
                    logger.debug("        %s already exists in stockLicenseDetails" %selectedLicenseId)
                    reportNoticeText = stockLicenseDetails[selectedLicenseId]["reportNoticeText"] 
                else:
                    licenseDetails = CodeInsight_RESTAPIs.license.license_lookup.get_license_details(baseURL, selectedLicenseId, authToken)
                    
                    stockLicenseDetails[selectedLicenseId] = {}
                    stockLicenseDetails[selectedLicenseId]["commonLicenseName"] = licenseDetails["name"]
                    stockLicenseDetails[selectedLicenseId]["commonLicenseURL"] = licenseDetails["url"]
                    stockLicenseDetails[selectedLicenseId]["spdxIdentifier"] = licenseDetails["spdxIdentifier"]
                    stockLicenseDetails[selectedLicenseId]["reportNoticeText"] = licenseDetails["text"]
                    logger.debug("        Adding %s to stock license details" %licenseDetails["name"])

                    reportNoticeText =  licenseDetails["text"]

            # TODO Do we have anything?  Should we used as found?
            # Store the data for the inventory item for reporting
            inventoryData[inventoryID] = {
                "componentName" : componentName,
                "componentVersionName" : componentVersionName,
                "selectedLicenseName": selectedLicenseName,
                "selectedLicenseSPDXIdentifier" : selectedLicenseSPDXIdentifier,
                "selectedLicenseID" : selectedLicenseId,
                "selectedLicenseUrl" : selectedLicenseUrl,
                "componentUrl" : componentUrl,
                "noticesText" : reportNoticeText
            }

            notices[inventoryID] = reportNoticeText

    logger.info("    **** Determine if there are common liceses")
    # TODO Is it a common license?
    for inventoryID in notices:
        notice = notices[inventoryID]
       
        commonLicenesItems = [key for key, value in notices.items() if value == notice]
        
        # There is more than one item that contains the same notice text
        if len(commonLicenesItems) > 1:
            # Just grab the name from one of the inventory Items
            logger.info("    This inventory item %s is using a common license")

            commonLicenseID = inventoryData[inventoryID]["selectedLicenseID"]

            # Do we already have a entry for the SPDX ID in the common licenses dict?
            if commonLicenseID in commonNotices:
                # No need to go through this again
                logger.debug("There is already a common license entry for %s" %str(commonLicenseID))
                # TODO is it the same text?

            else:
                # We need to update the license details for all inventory items with the common ID
                # to link to the common text in the report

                commonNotices[commonLicenseID] = {}
                commonNotices[commonLicenseID]["noticesText"] = notice
                commonNotices[commonLicenseID]["selectedLicenseName"] = inventoryData[inventoryID]["selectedLicenseName"]
                commonNotices[commonLicenseID]["selectedLicenseSPDXIdentifier"] = inventoryData[inventoryID]["selectedLicenseSPDXIdentifier"]
                commonNotices[commonLicenseID]["selectedLicenseUrl"] = inventoryData[inventoryID]["selectedLicenseUrl"]
 
                for inventoryID in commonLicenesItems:
                    inventoryData[inventoryID]["commonLicenseID"] = commonLicenseID # The rest will be created in the artifact


    # Sort the dictionary based on the component name and version
    sortedInventoryItems = OrderedDict( sorted(inventoryData.items(), key=lambda x: (x[1]["componentName"], x[1]["componentVersionName"]) ))

    sortedcommonNotices = OrderedDict( sorted(commonNotices.items(), key=lambda x: (x[1]["selectedLicenseName"] )))

    

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