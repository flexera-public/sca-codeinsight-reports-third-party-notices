'''
Copyright 2022 Flexera Software LLC
See LICENSE.TXT for full license text
SPDX-License-Identifier: MIT

Author : sgeary  
Created On : Tue Jan 04 2022
File : report_artifacts_text.py
'''

import logging

import _version

logger = logging.getLogger(__name__)

#------------------------------------------------------------------#
def generate_text_report(reportData):
    logger.info("    Entering generate_text_report")

    reportName = reportData["reportName"]
    projectName = reportData["projectName"]
    reportFileNameBase = reportData["reportFileNameBase"]
    reportDate = reportData["reportDate"]
    reportTimeStamp =  reportData["reportTimeStamp"]
    inventoryItems = reportData["inventoryData"] 
    commonNotices = reportData["commonNotices"] 

    textFile = reportFileNameBase + ".txt"


    #---------------------------------------------------------------------------------------------------
    # Create a text file for report details
    #---------------------------------------------------------------------------------------------------
    try:
        text_ptr = open(textFile, "w", encoding='utf-8')
    except:
        logger.error("Failed to open textfile %s:" %textFile)
        raise

    text_ptr.write("%s\n" %projectName)
    text_ptr.write("Third-Party Notices\n")
    text_ptr.write("%s\n" %reportDate)

    text_ptr.write("\n")

    text_ptr.write("This document provides notices information for the third-party components used by %s.\n" %projectName)       
    text_ptr.write("\n")

    text_ptr.write("Third Party Components\n")

    for inventoryItemID in inventoryItems:
        componentName = inventoryItems[inventoryItemID]["componentName"]
        componentVersionName = inventoryItems[inventoryItemID]["componentVersionName"]
        selectedLicenseSPDXIdentifier = inventoryItems[inventoryItemID]["selectedLicenseSPDXIdentifier"]
        
        # Link to the license details below using the inventory ID
        text_ptr.write("    %s  %s  (%s)\n" %(componentName, componentVersionName, selectedLicenseSPDXIdentifier))

    text_ptr.write("\n")
    text_ptr.write("Common Licenses\n")

    for licenseID in commonNotices:
        selectedLicenseName = commonNotices[licenseID]["commonLicenseName"]
        selectedLicenseSPDXIdentifier = commonNotices[licenseID]["spdxIdentifier"]

        text_ptr.write("    %s  (%s)\n" %(selectedLicenseName, selectedLicenseSPDXIdentifier))


    text_ptr.write("\n")
    text_ptr.write("-----------------------------------------\n")



    text_ptr.write("Third-Party Components\n")
    text_ptr.write("    The following is a list of the third-party components used by %s.\n" %projectName)
    text_ptr.write("\n") 


    for inventoryItemID in inventoryItems:
        componentName = inventoryItems[inventoryItemID]["componentName"]
        componentVersionName = inventoryItems[inventoryItemID]["componentVersionName"]

        logger.info("        Processing inventory item: '%s - %s  (%s)'" %(componentName, componentVersionName, inventoryItemID))
        selectedLicenseSPDXIdentifier = inventoryItems[inventoryItemID]["selectedLicenseSPDXIdentifier"]
        selectedLicenseName = inventoryItems[inventoryItemID]["selectedLicenseName"]
        noticesText = inventoryItems[inventoryItemID]["noticesText"]
        componentUrl = inventoryItems[inventoryItemID]["componentUrl"]

        text_ptr.write("%s  %s  (%s)\n" %(componentName, componentVersionName, selectedLicenseSPDXIdentifier))
        text_ptr.write("\n")
        text_ptr.write("    %s\n" %(componentUrl))
        text_ptr.write("\n")

        if inventoryItems[inventoryItemID]["isCommonLicense"]:
            logger.info("            Using common license text for %s (%s)" %(selectedLicenseName, selectedLicenseSPDXIdentifier))
            text_ptr.write("    For the full text of the %s license, see %s  (%s)\n" %(selectedLicenseSPDXIdentifier.replace(" ", "") ,selectedLicenseName, selectedLicenseSPDXIdentifier))
        else:
            logger.info("            Non common license so use popluated value")
            text_ptr.write("    %s\n" %noticesText)    

        text_ptr.write("\n")
    text_ptr.write("\n")
    text_ptr.write("-----------------------------------------\n")

    text_ptr.write("Common Licenses\n")
    text_ptr.write("\n")
    text_ptr.write("This section shows the text of common third-party licenes used by %s\n" %projectName)
    text_ptr.write("\n")

    # Add section for the common licenes
    for licenseID in commonNotices:

        noticesText = commonNotices[licenseID]["reportNoticeText"]
        selectedLicenseName = commonNotices[licenseID]["commonLicenseName"]
        selectedLicenseSPDXIdentifier = commonNotices[licenseID]["spdxIdentifier"]
        selectedLicenseUrl = commonNotices[licenseID]["commonLicenseURL"]

        text_ptr.write("%s  (%s)\n" %(selectedLicenseName, selectedLicenseSPDXIdentifier) )
        text_ptr.write("%s\n" %(selectedLicenseUrl))
        text_ptr.write("\n")   
        text_ptr.write("%s\n" %noticesText)
        text_ptr.write("\n")  
        text_ptr.write("====================\n")  
        text_ptr.write("\n")  




    text_ptr.close() 
    logger.info("    Exiting generate_text_report")
    return textFile