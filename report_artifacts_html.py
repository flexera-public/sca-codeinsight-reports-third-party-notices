'''
Copyright 2021 Flexera Software LLC
See LICENSE.TXT for full license text
SPDX-License-Identifier: MIT

Author : sgeary  
Created On : Thu Dec 16 2021
File : report_artifacts_html.py
'''
import logging
import os
import base64

import _version

logger = logging.getLogger(__name__)

#------------------------------------------------------------------#
def generate_html_report(reportData):
    logger.info("    Entering generate_html_report")

    reportName = reportData["reportName"]
    projectName = reportData["projectName"]
    reportFileNameBase = reportData["reportFileNameBase"]
    reportDate = reportData["reportDate"]
    reportTimeStamp =  reportData["reportTimeStamp"]
    inventoryItems = reportData["inventoryData"] 
    commonNotices = reportData["commonNotices"] 

    scriptDirectory = os.path.dirname(os.path.realpath(__file__))
    cssFile =  os.path.join(scriptDirectory, "report_branding/css/revenera_common.css")
    logoImageFile =  os.path.join(scriptDirectory, "report_branding/images/logo_reversed.svg")
    iconFile =  os.path.join(scriptDirectory, "report_branding/images/favicon-revenera.ico")

    htmlFile = reportFileNameBase + ".html"

    #########################################################
    #  Encode the image files
    encodedLogoImage = encodeImage(logoImageFile)
    encodedfaviconImage = encodeImage(iconFile)

    #---------------------------------------------------------------------------------------------------
    # Create a simple HTML file to display
    #---------------------------------------------------------------------------------------------------
    try:
        html_ptr = open(htmlFile, "w", encoding='utf-8')
    except:
        logger.error("Failed to open htmlfile %s:" %htmlFile)
        raise

    html_ptr.write("<!DOCTYPE html>\n") 
    html_ptr.write("<html lang=\"en\">\n") 
    html_ptr.write("<html>\n") 
    html_ptr.write("    <head>\n")

    html_ptr.write("        <!-- Required meta tags --> \n")
    html_ptr.write("        <meta charset='utf-8'>  \n")
    html_ptr.write("        <meta name='viewport' content='width=device-width, initial-scale=1, shrink-to-fit=no'> \n")

    html_ptr.write(''' 
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.1/css/bootstrap.min.css" integrity="sha384-VCmXjywReHh4PwowAiWNagnWcLhlEJLA5buUprzK8rxFgeH0kww/aWY76TfkUoSX" crossorigin="anonymous">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/4.1.3/css/bootstrap.css">
        <link rel="stylesheet" href="https://cdn.datatables.net/1.10.21/css/dataTables.bootstrap4.min.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/jstree/3.2.1/themes/default/style.min.css">
    ''')


    html_ptr.write("        <style>\n")

    # Add the contents of the css file to the head block
    try:
        f_ptr = open(cssFile)
        for line in f_ptr:
            html_ptr.write("            %s" %line)
        f_ptr.close()
    except:
        logger.error("Unable to open %s" %cssFile)
        print("Unable to open %s" %cssFile)


    html_ptr.write("        </style>\n")  

    html_ptr.write("    	<link rel='icon' type='image/png' href='data:image/png;base64, {}'>\n".format(encodedfaviconImage.decode('utf-8')))
    html_ptr.write("        <title>%s</title>\n" %(reportName))
    html_ptr.write("    </head>\n") 

    html_ptr.write("<body>\n")
    html_ptr.write("<div class=\"container-fluid\">\n")

    #---------------------------------------------------------------------------------------------------
    # Report Header
    #---------------------------------------------------------------------------------------------------
    html_ptr.write("<!-- BEGIN HEADER -->\n")
    html_ptr.write("<div class='header'>\n")
    html_ptr.write("  <div class='logo'>\n")
    html_ptr.write("    <img src='data:image/svg+xml;base64,{}' style='width: 400px;'>\n".format(encodedLogoImage.decode('utf-8')))
    html_ptr.write("  </div>\n")
    html_ptr.write("  <div class='report-title'>%s</div>\n" %reportName)
    html_ptr.write("</div>\n")
    html_ptr.write("<!-- END HEADER -->\n")

    #---------------------------------------------------------------------------------------------------
    # Body of Report
    #---------------------------------------------------------------------------------------------------
    html_ptr.write("<!-- BEGIN BODY -->\n")  
    html_ptr.write("<div class=\"container-fluid\">\n")

    html_ptr.write("    <H1>%s</H1>\n" %projectName)
    html_ptr.write("    <H1>Third-Party Notices</H1>\n")
    html_ptr.write("    <H4>%s</H4>\n" %reportDate)
    html_ptr.write("    <hr>\n")


    html_ptr.write("    <div class=\"container-fluid\">\n")
    html_ptr.write("        This document provides notices information for the third-party components used by %s.\n" %projectName)       
    html_ptr.write("    </div>\n")   

    html_ptr.write("    <p>\n") 

    html_ptr.write("    <br>\n")
    html_ptr.write("    <div class=\"container-fluid\">\n")
    html_ptr.write("        <b>Third Party Components</b>\n")
    html_ptr.write("        <div class=\"container-fluid\">\n")

    for inventoryItemID in inventoryItems:
        componentName = inventoryItems[inventoryItemID]["componentName"]
        componentVersionName = inventoryItems[inventoryItemID]["componentVersionName"]
        componentVersionId = inventoryItems[inventoryItemID]["componentVersionId"]
        selectedLicenseSPDXIdentifier = inventoryItems[inventoryItemID]["selectedLicenseSPDXIdentifier"]
        
        # Link to the license details below using the inventory ID
        html_ptr.write("            <a href='#%s'>%s  %s  (%s)</a> <!-- CompVerID:  %s --><br>\n" %(inventoryItemID, componentName, componentVersionName, selectedLicenseSPDXIdentifier, componentVersionId))

    html_ptr.write("        </div>\n")

    html_ptr.write("        <br>\n")
    html_ptr.write("        <b>Common Licenses</b>\n")
    html_ptr.write("        <br>\n")
    html_ptr.write("        <div class=\"container-fluid\">\n")

    for licenseID in commonNotices:
        selectedLicenseName = commonNotices[licenseID]["commonLicenseName"]
        selectedLicenseSPDXIdentifier = commonNotices[licenseID]["spdxIdentifier"]

        html_ptr.write("        <a href='#%s'>%s  (%s)</a>\n" %(selectedLicenseSPDXIdentifier.replace(" ", ""), selectedLicenseName, selectedLicenseSPDXIdentifier))
        html_ptr.write("        <br>\n")


    html_ptr.write("        </div>\n")

    html_ptr.write("    </div>\n")



    html_ptr.write("    <hr>\n")

    #--  The main body of the report

    html_ptr.write("    <H2>Third-Party Components</H2>\n")
    html_ptr.write("    <div class=\"container-fluid\">\n")
    html_ptr.write("        The following is a list of the third-party components used by %s.\n" %projectName)
    html_ptr.write("        <p>\n") 

    for inventoryItemID in inventoryItems:
        componentName = inventoryItems[inventoryItemID]["componentName"]
        componentVersionName = inventoryItems[inventoryItemID]["componentVersionName"]
        componentVersionId = inventoryItems[inventoryItemID]["componentVersionId"]


        logger.info("        Processing inventory item: '%s - %s  (%s)'" %(componentName, componentVersionName, inventoryItemID))
        selectedLicenseSPDXIdentifier = inventoryItems[inventoryItemID]["selectedLicenseSPDXIdentifier"]
        selectedLicenseName = inventoryItems[inventoryItemID]["selectedLicenseName"]
        noticesText = inventoryItems[inventoryItemID]["noticesText"]
        componentUrl = inventoryItems[inventoryItemID]["componentUrl"]

        html_ptr.write("        <h5 id=%s>%s  %s  (%s)</h5>  <!-- CompVerID:  %s -->\n" %(inventoryItemID, componentName, componentVersionName, selectedLicenseSPDXIdentifier, componentVersionId))
        html_ptr.write("        <div class=\"container-fluid\">\n")
        html_ptr.write("            <a href='%s' target='_blank'>%s</a><br>\n" %(componentUrl, componentUrl))
        html_ptr.write("            <p>\n")
        html_ptr.write("            <p>\n")

        if inventoryItems[inventoryItemID]["isCommonLicense"]:
            logger.info("            Using common license text for %s (%s)" %(selectedLicenseName, selectedLicenseSPDXIdentifier))
            html_ptr.write("            For the full text of the %s license, see <a href='#%s'>%s  (%s)</a>\n" %(selectedLicenseSPDXIdentifier, selectedLicenseSPDXIdentifier.replace(" ", "") ,selectedLicenseName, selectedLicenseSPDXIdentifier))
        else:
            logger.info("            Non common license so use popluated value")
            html_ptr.write("            <pre>%s</pre>\n" %noticesText)    

        html_ptr.write("        </div>\n") 
        html_ptr.write("        <p>\n") 
    
    html_ptr.write("</div>\n")   
    html_ptr.write("<p>") 
    html_ptr.write("<hr>\n")

    html_ptr.write("<H2>Common Licenses</H2>\n")
    html_ptr.write("<div class=\"container-fluid\">\n")
    html_ptr.write("This section shows the text of common third-party licenes used by %s\n" %projectName)
    html_ptr.write("<p>") 

    # Add section for the common licenes
    # TODO remove common license if no components use it
    for licenseID in commonNotices:

        noticesText = commonNotices[licenseID]["reportNoticeText"]
        selectedLicenseName = commonNotices[licenseID]["commonLicenseName"]
        selectedLicenseSPDXIdentifier = commonNotices[licenseID]["spdxIdentifier"]
        selectedLicenseUrl = commonNotices[licenseID]["commonLicenseURL"]

        html_ptr.write("<H3 id=%s>%s  (%s) </H3>\n" %(selectedLicenseSPDXIdentifier.replace(" ", "") , selectedLicenseName, selectedLicenseSPDXIdentifier) )
        html_ptr.write("<a href='%s' >%s</a>\n" %(selectedLicenseUrl, selectedLicenseUrl))
        html_ptr.write("<div style='white-space: pre-wrap; width: 65%;'>\n")   
        html_ptr.write("%s\n" %noticesText)
        html_ptr.write("</div>\n")  
        html_ptr.write("<br>\n")  

    html_ptr.write("</div>\n")   
    html_ptr.write("<p>\n") 


    html_ptr.write("</div>\n") # End of body fluid container
    html_ptr.write("<!-- END BODY -->\n")  
    html_ptr.write("</div>\n") # End of main fluid container

    #---------------------------------------------------------------------------------------------------
    # Report Footer
    #---------------------------------------------------------------------------------------------------
    html_ptr.write("<!-- BEGIN FOOTER -->\n")
    html_ptr.write("<div class='report-footer'>\n")
    html_ptr.write("  <div style='float:right'>Generated on %s</div>\n" %reportTimeStamp)
    html_ptr.write("  <br>\n")
    html_ptr.write("  <div style='float:right'>Report Version: %s</div>\n" %_version.__version__)
    html_ptr.write("</div>\n")
    html_ptr.write("<!-- END FOOTER -->\n")   

    html_ptr.write("</div>\n") # End of container fluid class

    html_ptr.write("</body>\n") 
    html_ptr.write("</html>\n") 
    html_ptr.close() 

    logger.info("    Exiting generate_html_report")
    return htmlFile


####################################################################
def encodeImage(imageFile):

    #############################################
    # Create base64 variable for branding image
    try:
        with open(imageFile,"rb") as image:
            encodedImage = base64.b64encode(image.read())
            return encodedImage
    except:
        logger.error("Unable to open %s" %imageFile)
        raise