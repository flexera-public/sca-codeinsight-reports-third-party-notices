'''
Copyright 2021 Flexera Software LLC
See LICENSE.TXT for full license text
SPDX-License-Identifier: MIT

Author : sgeary  
Created On : Thu Dec 16 2021
File : report_artifacts.py
'''
import logging

import report_artifacts_html
import report_artifacts_text
import report_artifacts_error


logger = logging.getLogger(__name__)

#--------------------------------------------------------------------------------#
def create_report_artifacts(reportData):
    logger.info("Entering create_report_artifacts")

    # Dict to hold the complete list of reports
    reports = {}

    htmlFile = report_artifacts_html.generate_html_report(reportData)
    textFile = report_artifacts_text.generate_text_report(reportData)

    reports["viewable"] = htmlFile
    reports["allFormats"] = [htmlFile, textFile]

    logger.info("Exiting create_report_artifacts")
    
    return reports 

#--------------------------------------------------------------------------------#
def create_error_artifacts(reportData):
    logger.info("Entering create_error_report")

    # Dict to hold the complete list of reports
    reports = {}

    htmlFile = report_artifacts_error.generate_error_report(reportData)
    
    reports["viewable"] = htmlFile
    reports["allFormats"] = [htmlFile]

    logger.info("Exiting create_report_artifacts")
    
    return reports 