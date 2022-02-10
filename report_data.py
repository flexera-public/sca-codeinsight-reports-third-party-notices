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

import CodeInsight_RESTAPIs.project.get_child_projects
import CodeInsight_RESTAPIs.project.get_project_inventory
import CodeInsight_RESTAPIs.license.license_lookup
import CodeInsight_RESTAPIs.inventory.update_inventory
import CodeInsight_RESTAPIs.data_access.credentials.server_details
import CodeInsight_RESTAPIs.data_access.credentials.authorization
import CodeInsight_RESTAPIs.data_access.license.license_texts
import common_licenses

logger = logging.getLogger(__name__)

#-------------------------------------------------------------------#
def gather_data_for_report(baseURL, projectID, authToken, reportName, reportOptions):
    logger.info("Entering gather_data_for_report")

    # Parse report options
    includeChildProjects = reportOptions["includeChildProjects"]  # True/False
    overrideExistingNoticesText = reportOptions["overrideExistingNoticesText"]  # True/False

    projectList = [] # List to hold parent/child details for report
    inventoryData = {}  # Create a dictionary containing the inventory data using inventoryID as keys
    componentVersionLicenses = []
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
            componentVersionId = inventoryItem["componentVersionId"]

            # Is this a component?
            if inventoryItem["type"] != "Component":
                continue

            inventoryID = inventoryItem["id"]
            componentName = inventoryItem["componentName"]
            componentVersionName = inventoryItem["componentVersionName"]
            
            if componentVersionName == "N/A":
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


            # If this is a specific component and not custom add it to the list
            if componentVersionId != "N/A":
                # Sep stament to avoid issue with int vs str
                if componentVersionId < 1000000000:
                    componentVersionLicenses.append(componentVersionId)

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
    if len(componentVersionLicenses):

        # Create a list of strings of the component version IDs
        componentVersionsIDList = [str(id) for id in componentVersionLicenses]

        numComponentVersionIds = len(componentVersionsIDList)
        # Get auth token and notices for supplied list of component version IDs
        dataServicesURL = CodeInsight_RESTAPIs.data_access.credentials.server_details.get_data_service_url(baseURL, authToken)
        dataServicesAuthDetails = CodeInsight_RESTAPIs.data_access.credentials.authorization.get_data_service_token(baseURL, authToken)
        dataServicesAuthToken = dataServicesAuthDetails["access_token"]

        logger.info("    Collect notices for %s component versions IDs" %numComponentVersionIds)
        
        # The API supports a call with a max of 25 IDs at a time
        maxNumIDs = 25
        if numComponentVersionIds > maxNumIDs:
            gatheredNotices = []

            for index in range(0, numComponentVersionIds, maxNumIDs):
                componentVersionsIds = ", ".join(componentVersionsIDList[index:index+maxNumIDs])
                currentNoticesSet = CodeInsight_RESTAPIs.data_access.license.license_texts.get_license_text_by_componentVersionId(dataServicesURL, dataServicesAuthToken, componentVersionsIds)
                # Were there any notices pulled back at all?
                if currentNoticesSet:
                    gatheredNotices += currentNoticesSet

        else:
            componentVersionsIds = ", ".join(componentVersionsIDList)
            gatheredNotices = CodeInsight_RESTAPIs.data_access.license.license_texts.get_license_text_by_componentVersionId(dataServicesURL, dataServicesAuthToken, componentVersionsIds)

        # Any issues collecting the notice data?
        try:
            if "errorMsg" in gatheredNotices.keys():
                return gatheredNotices
        except:
            logger.debug("No error gathering notices")

        # Was there any notice data?
        try:
            len(gatheredNotices)
            logger.debug("Total number of collected notices obtained: %s" %len(gatheredNotices))
        except:
            logger.debug("No notice data gathered. Creating empty list")
            gatheredNotices = []


        processedNotices = process_notices(gatheredNotices)

    # Update each inventory notice text for the report with the gathered notices or the template notices
    for inventoryID in inventoryData:
        componentName = inventoryData[inventoryID]["componentName"]
        componentVersionName = inventoryData[inventoryID]["componentVersionName"]
        componentVersionId = inventoryData[inventoryID]["componentVersionId"]
        logger.debug("Processing notices for '%s - %s  (Inv ID: %s  - CompVerID: %s)'" %(componentName, componentVersionName, inventoryID, componentVersionId))
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

        elif componentVersionId in processedNotices: 
            # Replace any data that is already there
            logger.info("    Component has gathered license text")
            logger.info("        %s unique license found." %(len (processedNotices[componentVersionId])))

            if overrideExistingNoticesText or originalNoticesText in emptyNotices:
                logger.info("        Using license text obtained during collection process")
                # Update the notices with the gathered license text
                
                componentNotices = processedNotices[componentVersionId] # Dict of notices for this component
                
                logger.info("            Found %s licenses for component/version" %len(componentNotices))
     
                updateNoticesText = ""
                # Combine all license text into a single value
                for uniqueLicenseID in componentNotices:

                    if componentNotices[uniqueLicenseID]["licenseType"] in selectedLicenseSPDXIdentifier:
                        logger.info("            Selected license %s has a matching license type in gathered notices" %selectedLicenseSPDXIdentifier)
                        uniqueLicenseText = componentNotices[uniqueLicenseID]["licenseText"]
                    else:
                        uniqueLicenseText = componentNotices[uniqueLicenseID]["licenseText"]

                    updateNoticesText += uniqueLicenseText + "\n\n====================\n\n"

                # Can we update the notices text to be specific based on the slected license for the inventory item?

                # Create a dictionary of all licenses for the component using determined licenes type as key
                # Each value may be a list of possible texts gathered....
                licenseTextByType = {}
                
                for uniqueLicenseID in componentNotices:
                    licenseType = componentNotices[uniqueLicenseID]["licenseType"]
                    licenseText = componentNotices[uniqueLicenseID]["licenseText"]

                    if licenseType in licenseTextByType:
                        licenseTextByType[licenseType].append(licenseText)
                    else:
                        licenseTextByType[licenseType] = [licenseText]

                # Can we match data to the selected license for the inventory item?
                for licenseType in licenseTextByType:
                    if licenseType in selectedLicenseSPDXIdentifier:
                        logger.info("            Override notice text using SDPX Identifier for inventory item")
                        updateNoticesText = "\n\n====================\n\n".join(licenseTextByType[licenseType])
    

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
def process_notices(gatheredNotices):
    logger.debug("    Entering process_notices.")

    dedupedNotices = {}
    # Deduplicate the returned data based on the licenseTextId
    # and create a dictionary based on componentVersionIDs that contains
    # a list of the notice texts
    for notice in gatheredNotices:
        componentVersionID = notice["versionId"]
        licenseID = notice["licenseTextId"]

        if componentVersionID not in dedupedNotices:
            dedupedNotices[componentVersionID] = {}

        # Do we already have the license itself?
        if licenseID not in dedupedNotices[componentVersionID]:
            dedupedNotices[componentVersionID][licenseID] = {}
            dedupedNotices[componentVersionID][licenseID] ["filePath"] = notice["filePath"]
            dedupedNotices[componentVersionID][licenseID] ["licenseText"] = notice["text"]

            # Can a determination as to what license a specfic text is based on 
            # license file name or specific contents of the text?

            licenseType = determine_licenses(notice["filePath"], notice["text"] )

            logger.info("        For CompVerID: %s licenesID: %s -- Determined licenseType: %s" %(componentVersionID, licenseID, licenseType))
            
            dedupedNotices[componentVersionID][licenseID]["licenseType"] = licenseType

    HTMLFreeNotices = {}

    # If there is more than one licese text for a specific component remove any html versions
    for componentVersionID in dedupedNotices:
        HTMLFreeNotices[componentVersionID]={}
        if len(dedupedNotices[componentVersionID]) > 1:
            for licenseID in dedupedNotices[componentVersionID]:
                if not dedupedNotices[componentVersionID][licenseID]["filePath"].endswith(tuple(["html", "htm"])):
                    HTMLFreeNotices[componentVersionID][licenseID] = dedupedNotices[componentVersionID][licenseID]
        else:
            # There is just a single license so use it
            licenseID = list(dedupedNotices[componentVersionID].keys())[0]
            if dedupedNotices[componentVersionID][licenseID]["filePath"].endswith(tuple(["html", "htm"])):
                logger.info("        For CompVerID: %s licenesID: %s -- Only HTML file exists" %(componentVersionID, licenseID))
                HTMLFreeNotices[componentVersionID][licenseID] = {}
                HTMLFreeNotices[componentVersionID] = dedupedNotices[componentVersionID]
                HTMLFreeNotices[componentVersionID][licenseID]["licenseText"] = "*** The only available notices for this component is in HTML format.  Manual review required. ***"
            else:
                HTMLFreeNotices[componentVersionID] = dedupedNotices[componentVersionID]


    logger.info("        Exiting process_notices")
    return HTMLFreeNotices


#-----------------------------------------------#
def determine_licenses(filePath, licenseText):
    logger.debug("            Entering determine_licenses.")

    strippedlicenesText = "".join(licenseText.split()).lower()

    licenseType = "unknown"

    licenseIndicators = {}
    licenseIndicators["MIT"] = "Permission is hereby granted, free of charge"

    licenseIndicators["Apache-1.0"] = "Copyright (c) 1995-1999 The Apache Group. All rights reserved."
    licenseIndicators["Apache-1.1"] = "Apache License 1.1 Copyright (c) 2000 The Apache Software Foundation. All rights reserved."
    licenseIndicators["Apache-2.0"] = "Apache License Version 2.0, January 2004"

    licenseIndicators["0BSD"] = "Redistribution and use in source and binary forms"
    licenseIndicators["BSD-1-Clause"] = "Redistributions of source code"
    licenseIndicators["BSD-2-Clause"] = "Redistributions in binary form"
    licenseIndicators["BSD-3-Clause"] = "Neither the name of the copyright holder nor the names"
    licenseIndicators["BSD-4-Clause"] = "All advertising materials mentioning features"

    licenseIndicators["GPL-1.0"] = "GNU GENERAL PUBLIC LICENSE Version 1, February 1989"
    licenseIndicators["GPL-2.0"] = "GNU GENERAL PUBLIC LICENSE Version 2, June 1991"
    licenseIndicators["GPL-3.0"] = "GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007"

    licenseIndicators["LGPL-2.0"] = "GNU LIBRARY GENERAL PUBLIC LICENSE Version 2, June 1991"
    licenseIndicators["LGPL-2.1"] = "GNU LESSER GENERAL PUBLIC LICENSE Version 2.1, February 1999"
    licenseIndicators["LGPL-3.0"] = "GNU LESSER GENERAL PUBLIC LICENSE Version 3, 29 June 2007"   
 
    # Can the licnse be determine by the file name
    if "mit" in filePath.lower():
        licenseType = "MIT"
    elif "gpl-3.0" in filePath.lower():
        licenseType = "GPL-3.0"
    elif "gpl-2.0" in filePath.lower():
        licenseType = "GPL-2.0"
    elif "lgpl-2.1" in filePath.lower():
        licenseType = "LGPL-2.1"
    elif "lgpl-3.0" in filePath.lower():
        licenseType = "LGPL-3.0"
    else:
        logger.info("                Unable to determine license type by file name.  Checking license text")    
        # Try to determine by the licesne text
        for licenseTypeOption in licenseIndicators:
            strippedIndicatorText = "".join(licenseIndicators[licenseTypeOption].split()).lower()    
            if strippedlicenesText.find(strippedIndicatorText) > -1:
                licenseType = licenseTypeOption

    logger.info("            Exiting determine_licenses")

    return licenseType