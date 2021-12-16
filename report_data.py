'''
Copyright 2021 Flexera Software LLC
See LICENSE.TXT for full license text
SPDX-License-Identifier: MIT

Author : sgeary  
Created On : Thu Dec 16 2021
File : report_data.py
'''
import logging

logger = logging.getLogger(__name__)

#-------------------------------------------------------------------#
def gather_data_for_report(baseURL, projectID, authToken, reportName, reportOptions):
    logger.info("Entering gather_data_for_report")


    projectName = "Test Project Name"
    projectList = ["1", "2"]

    # Build up the data to return for the
    reportData = {}
    reportData["projectName"] = projectName
    reportData["reportName"] = reportName
    reportData["projectList"] = projectList



    logger.info("Exiting gather_data_for_report")

    return reportData