'''
Copyright 2021 Flexera Software LLC
See LICENSE.TXT for full license text
SPDX-License-Identifier: MIT

Author : sgeary  
Created On : Thu Dec 16 2021
File : API_license_text.py
'''
import logging
import pymysql
logger = logging.getLogger(__name__)

#---------------------------------------------------

def get_license_text(componentVersionLicenses):
    logger.info("Entering get_licese_text")

    licenseTextResults = get_all_license_text_data(componentVersionLicenses.keys()) 

    if type(licenseTextResults) is tuple:
        logger.info("    Tuple returned")

        # Take the tuple from the DB query and make a dictionary
        licenseData = {}
        # Cycle thru each row to create a dict per license 
        for versionID, licenseText in licenseTextResults:

            if versionID in licenseData:
                licenseData[versionID].append(licenseText)
            else:
                licenseData[versionID] = [licenseText]

        return licenseData

    # Any issues collecting the notice data?
    elif type(licenseTextResults) is dict:
        if "errorMsg" in licenseTextResults.keys():
            return licenseTextResults

    else:
        logger.error("    This should never be reached")


#-----------------------------------------------------------------   
# This will be replaced by an API
def get_all_license_text_data(componentVersionLicenses):
    logger.info("Entering get_all_license_text_data")

    mySQLHOST = "UPDATE ME"
    mySQLUSER = "UPDATE ME"
    mySQLPASSWORD = "UPDATE ME"
    mySQLDATABASE = "UPDATE ME"
    
    if "UPDATE ME" in [mySQLHOST, mySQLUSER, mySQLPASSWORD, mySQLDATABASE]:
        logger.error("Contact Revenera for required database credentials")
        return {"errorMsg": ["Contact Revenera for required database credentials"]}

    # Open database connection
    try:
        db = pymysql.connect(host=mySQLHOST, user=mySQLUSER, password=mySQLPASSWORD, database=mySQLDATABASE)
    except:
        return {"errorMsg": ["Connection error.  Please confirm database information"]}


    # prepare a cursor object using cursor() method
    cursor = db.cursor()

   
    sqlQuery = """SELECT v.version_id, l.text 'license_text'
                    FROM components c
                    JOIN versions v ON c.component_id = v.component_id
                    JOIN releases r ON r.version_id = v.version_id
                    JOIN release_to_license_text_map m ON m.release_id = r.release_id
                    JOIN license_texts l ON l.id = m.license_text_id
                    WHERE v.version_id IN (""" +  ", ".join("{0}".format(Id) for Id in componentVersionLicenses) + """);"""

    try:
        # Execute the SQL command
        cursor.execute(sqlQuery)
        # Fetch all the rows in a list of lists.
        queryResults = cursor.fetchall()
        
        logger.info("Exiting get_all_license_text_data")

        return queryResults

    except pymysql.InternalError as error:
        logger.error(error)
        return {"errorMsg": ["Database Error. See logfile"]}

    logger.info("Exiting get_all_license_text_data")

