###########################################################################################
#getCostReportOCI.py
#
# Author    : Leo James
# Credit.   : Adi Zhoar,  Scripts was customized based on his original design
# Created   : 2022.03.12
# Modified  : 2022.03.28  Added support for specific day file download
#           : 2023.03.30  Added support for Monthly file download
#           : 2023.04.07  Completed support for Monthhly download with different CSV files.
#           :             Modifed SKU name to avoid SKU in there.
# 
#
# Supports Python 3.10
###########################################################################################

import sys
import argparse
import datetime
import oci
import os.path
import platform
import pandas as pd
import csv


# Define the function for the usecase
def val_dt(dateStr):
    # Take the char back to ASCII code and add up the shift, then get back the result in char
    try:
        #print(dateStr)
        return datetime.datetime.strptime(dateStr, "%Y-%m-%d").date()
    except ValueError:
        msg = "Given Date ({0}) not valid! Expected format, YYYY-MM-DD!".format(arg_date_str)
        raise argparse.ArgumentTypeError(msg)

def val_conf(fileLoc):
    try:
        file_exists = os.path.exists(fileLoc)
        print(fileLoc)
        return file_exists
    except ValueError:
        msg = "Given fileLocation ({1}) not valid!" 
        raise argparse.ArgumentTypeError(msg)


##########################################################################
# Create signer for Authentication
# Input - config_profile and is_instance_principals and is_delegation_token
# Output - config and signer objects
##########################################################################
def create_signer(config_file):
    signer = oci.signer.Signer(
        tenancy=config["tenancy"],
        user=config["user"],
        fingerprint=config["fingerprint"],
        private_key_file_location=config.get("key_file"),
        private_key_content=config.get("key_content")
    )
    return signer


##########################################################################
# Usage Daily by Product
##########################################################################
def usage_daily_product(usageClient, tenant_id, time_usage_started, time_usage_ended):
    # oci.usage_api.models.RequestSummarizedUsagesDetails
    requestSummarizedUsagesDetails = oci.usage_api.models.RequestSummarizedUsagesDetails(
        tenant_id=tenant_id,
        #granularity='DAILY',
        granularity='MONTHLY',
        query_type='COST',
        group_by=['skuPartNumber', 'skuName'],
        time_usage_started=time_usage_started.strftime('%Y-%m-%dT%H:%M:%SZ'),
        time_usage_ended=time_usage_ended.strftime('%Y-%m-%dT%H:%M:%SZ')
    )

    # usageClient.request_summarized_usages
    request_summarized_usages = usageClient.request_summarized_usages(
        requestSummarizedUsagesDetails,
        retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY
    )


    ################################
    # Add all data to array data
    ################################
    data = []
    min_date = None
    max_date = None
    currency = ""
    for item in request_summarized_usages.data.items:
        data.append({
            'sku': item.sku_part_number,
            'sku_name': item.sku_name,# if item.sku_part_number in item.sku_name else item.sku_part_number + " - " + item.sku_name,
            'cost': item.computed_amount if item.computed_amount else 0,
            'quantity': item.computed_quantity if item.computed_quantity else 0,
            'currency': item.currency,
            'time_usage_started': item.time_usage_started,
            'time_usage_ended': item.time_usage_ended                
        })
        #print(tenant_id,item.sku_name,item.computed_amount,item.computed_quantity,item.currency,item.time_usage_started.strftime('%Y-%m-%d'),item.time_usage_ended.strftime('%Y-%m-%d'))
        
        if item.currency:
            currency = item.currency
        if not min_date or item.time_usage_started < min_date:
            min_date = item.time_usage_started
        if not max_date or item.time_usage_started > max_date:
            max_date = item.time_usage_started
    return data
        
'''    
        #with open('PATH'+tenant_id +'.csv', 'w') as f:
            #[f.write('{0},{1}\n'.format(key, value)) for key, value in data.items()]

        #csv_file = open('/Users/lejames/jupyter/datasets/'+tenant_id +'.csv','wb')
        #w = csv_file.DictWriter(csv_file,data.keys())
        #w.writerow(data)
        #csv_file.close()
        #df = pd.DataFrame.from_dict(data)
        #df.to_csv('/Users/lejames/jupyter/datasets/'+tenant_id +'.csv', index = True, header = True)
        #df = pd.DataFrame(data)
        #df.to_csv('/Users/lejames/jupyter/datasets/'+tenant_id +'.csv', index=False)
        #print(data)
        with open('/Users/lejames/jupyter/datasets/'+tenant_id +'.csv','wb') as f:
            #Using dictionary keys as fieldnames for the CSV file header
            writer = csv.DictWriter(f, data[0].keys())
            writer.writeheader()
            for d in data:
                writer.writerow(d)

        

       

def rm_sp_chr(profile):
    try:
        for char in ' ?.!/;:[]':
            profile = profile.replace(char,'')
            return profile
    except ValueError:
        msg = "Given fileLocation ({1}) not valid!" 
        raise argparse.ArgumentTypeError(msg)
        
        
 '''  

#######################################################################################
# The Object Storage namespace used for the reports is bling.  Don't change the below
#######################################################################################
reporting_namespace = 'bling'

# Download all usage and cost files. You can comment out based on the specific need:

# prefix_file = ""                      #  For cost and usage files
prefix_file = "reports/cost-csv"        #  For cost
# prefix_file = "reports/usage-csv"     #  For usage

destintation_path = "/Users/lejames/datasets/"



# Get the user input
sdt = input("Enter start date : ")
edt = input("Enter end date : ")
cfl = input("Enter the confile location : ")

# Call the functions
# Date Validation 
sdt = val_dt(sdt)
edt = val_dt(edt)

request_summarized_usages = []
#step = datetime.timedelta(days=1)
#time_usage_ended = time_usage_started + datetime.timedelta(days=1)
#print(tdt)

# Config File Validation
if val_conf(cfl):
            print('Config file exists')


# Let us open the config file and extract the profile

f=open(cfl,"r")
data=f.read()
substring = "["
p1 = []
#fn = []  # to store the filenames to sorting.
ctr = 0
ctr1 = 0   # Another counter
# Not being used as some date has only 3 reports per day.
#ts_ctr = 0  # Will be used to print the last billing record at 4th iteration. ie. when ctr =  4
filename = ""

rows = data.split("\n")
for row in rows:
    if substring in row:
        p1.append(row)
        #print(p1,len(p1))

for item in p1:
    p = p1[ctr]
    for char in '[]':
        p = p.replace(char,"")
    #print(p)
    config = oci.config.from_file(file_location=cfl, profile_name=p)
    #print(config)
    
    signer = create_signer(config)
    
    usage_client = oci.usage_api.UsageapiClient(config, signer=signer)

    tenant_id = config['tenancy']

    data = usage_daily_product(usage_client,tenant_id,sdt,edt)  # Calling the daily usage function.

    #print(data)

    my_df = pd.DataFrame(data)

    my_df.to_csv('/home/opc/datasets/'+tenant_id +'.csv', index=False, header=True)
    


    ctr += 1
     








 







        

    
            
            
