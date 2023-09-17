# Mail: tongdongdong@outlook.com
import random
import time
import json
import requests
import os
import traceback
from dns.qCloud import QcloudApiv3 # QcloudApiv3 DNSPod 的 API 更新了 github@z0z0r4
from dns.aliyun import AliApi
from dns.huawei import HuaWeiApi
import sys

#  New
import CloudFlare

#可以从https://shop.hostmonit.com获取
KEY = os.environ["KEY"]  #"o1zrmHAF"
#CM:移动 CU:联通 CT:电信 AB:境外 DEF:默认
#修改需要更改的dnspod域名和子域名
DOMAINS = json.loads(os.environ["DOMAINS"])  #{"hostmonit.com": {"@": ["CM","CU","CT"], "shop": ["CM", "CU", "CT"], "stock": ["CM","CU","CT"]},"4096.me": {"@": ["CM","CU","CT"], "vv": ["CM","CU","CT"]}}
#腾讯云后台获取 https://console.cloud.tencent.com/cam/capi
SECRETID = os.environ["SECRETID"]    #'AKIDV**********Hfo8CzfjgN'
SECRETKEY = os.environ["SECRETKEY"]   #'ZrVs*************gqjOp1zVl'
#默认为普通版本 不用修改
AFFECT_NUM = 2
#DNS服务商 如果使用DNSPod改为1 如果使用阿里云解析改成2  如果使用华为云解析改成3
DNS_SERVER = 1
#如果试用华为云解析 需要从API凭证-项目列表中获取
REGION_HW = 'cn-east-3'
#如果使用阿里云解析 REGION出现错误再修改 默认不需要修改 https://help.aliyun.com/document_detail/198326.html
REGION_ALI = 'cn-hongkong'
#解析生效时间，默认为600秒 如果不是DNS付费版用户 不要修改!!!
TTL = 600
#v4为筛选出IPv4的IP  v6为筛选出IPv6的IP
# --------new -----------------
CF_DOMAINS = json.loads(os.environ["CF_DOMAINS"])
CF_EMAIL = os.environ["CF_EMAIL"]   
CF_TOKEN = os.environ["CF_TOKEN"]   
CF_SUB_DOMAIN_NUM = 5
# -----------------------------
if len(sys.argv) >= 2:
    RECORD_TYPE = sys.argv[1]
else:
    RECORD_TYPE = "A"


def get_optimization_ip():
    try:
        headers = headers = {'Content-Type': 'application/json'}
        data = {"key": KEY, "type": "v4" if RECORD_TYPE == "A" else "v6"}
        response = requests.post('https://api.hostmonit.com/get_optimization_ip', json=data, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print("CHANGE OPTIMIZATION IP ERROR: REQUEST STATUS CODE IS NOT 200")
            return None
    except Exception as e:
        print("CHANGE OPTIMIZATION IP ERROR: " + str(e))
        return None

def changeDNS(line, s_info, c_info, domain, sub_domain, cloud):
    global AFFECT_NUM, RECORD_TYPE

    lines = {"CM": "移动", "CU": "联通", "CT": "电信", "AB": "境外", "DEF": "默认"}
    line = lines[line]

    try:
        create_num = AFFECT_NUM - len(s_info)
        if create_num == 0:
            for info in s_info:
                if len(c_info) == 0:
                    break
                cf_ip = c_info.pop(random.randint(0,len(c_info)-1))["ip"]
                if cf_ip in str(s_info):
                    continue
                ret = cloud.change_record(domain, info["recordId"], sub_domain, cf_ip, RECORD_TYPE, line, TTL)
                if(DNS_SERVER != 1 or ret["code"] == 0):
                    print("CHANGE DNS SUCCESS: ----Time: " + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) + "----DOMAIN: " + domain + "----SUBDOMAIN: " + sub_domain + "----RECORDLINE: "+line+"----RECORDID: " + str(info["recordId"]) + "----VALUE: " + cf_ip )
                else:
                    print("CHANGE DNS ERROR: ----Time: " + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) + "----DOMAIN: " + domain + "----SUBDOMAIN: " + sub_domain + "----RECORDLINE: "+line+"----RECORDID: " + str(info["recordId"]) + "----VALUE: " + cf_ip + "----MESSAGE: " + ret["message"] )
        elif create_num > 0:
            for i in range(create_num):
                if len(c_info) == 0:
                    break
                cf_ip = c_info.pop(random.randint(0,len(c_info)-1))["ip"]
                if cf_ip in str(s_info):
                    continue
                ret = cloud.create_record(domain, sub_domain, cf_ip, RECORD_TYPE, line, TTL)
                if(DNS_SERVER != 1 or ret["code"] == 0):
                    print("CREATE DNS SUCCESS: ----Time: " + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) + "----DOMAIN: " + domain + "----SUBDOMAIN: " + sub_domain + "----RECORDLINE: "+line+"----VALUE: " + cf_ip )
                else:
                    print("CREATE DNS ERROR: ----Time: " + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) + "----DOMAIN: " + domain + "----SUBDOMAIN: " + sub_domain + "----RECORDLINE: "+line+"----RECORDID: " + str(info["recordId"]) + "----VALUE: " + cf_ip + "----MESSAGE: " + ret["message"] )
        else:
            for info in s_info:
                if create_num == 0 or len(c_info) == 0:
                    break
                cf_ip = c_info.pop(random.randint(0,len(c_info)-1))["ip"]
                if cf_ip in str(s_info):
                    create_num += 1
                    continue
                ret = cloud.change_record(domain, info["recordId"], sub_domain, cf_ip, RECORD_TYPE, line, TTL)
                if(DNS_SERVER != 1 or ret["code"] == 0):
                    print("CHANGE DNS SUCCESS: ----Time: " + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) + "----DOMAIN: " + domain + "----SUBDOMAIN: " + sub_domain + "----RECORDLINE: "+line+"----RECORDID: " + str(info["recordId"]) + "----VALUE: " + cf_ip )
                else:
                    print("CHANGE DNS ERROR: ----Time: " + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) + "----DOMAIN: " + domain + "----SUBDOMAIN: " + sub_domain + "----RECORDLINE: "+line+"----RECORDID: " + str(info["recordId"]) + "----VALUE: " + cf_ip + "----MESSAGE: " + ret["message"] )
                create_num += 1
    except Exception as e:
            print("CHANGE DNS ERROR: ----Time: " + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) + "----MESSAGE: " + str(traceback.print_exc()))

def main(cloud):
    global AFFECT_NUM, RECORD_TYPE
    if len(DOMAINS) > 0:
        try:
            cfips = get_optimization_ip()
            if cfips == None or cfips["code"] != 200:
                print("GET CLOUDFLARE IP ERROR: ----Time: " + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) )
                return
            cf_cmips = cfips["info"]["CM"]
            cf_cuips = cfips["info"]["CU"]
            cf_ctips = cfips["info"]["CT"]
            for domain, sub_domains in DOMAINS.items():
                for sub_domain, lines in sub_domains.items():
                    temp_cf_cmips = cf_cmips.copy()
                    temp_cf_cuips = cf_cuips.copy()
                    temp_cf_ctips = cf_ctips.copy()
                    temp_cf_abips = cf_ctips.copy()
                    temp_cf_defips = cf_ctips.copy()
                    if DNS_SERVER == 1:
                        ret = cloud.get_record(domain, 20, sub_domain, "CNAME")
                        if ret["code"] == 0:
                            for record in ret["data"]["records"]:
                                if record["line"] == "移动" or record["line"] == "联通" or record["line"] == "电信":
                                    retMsg = cloud.del_record(domain, record["id"])
                                    if(retMsg["code"] == 0):
                                        print("DELETE DNS SUCCESS: ----Time: "  + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) + "----DOMAIN: " + domain + "----SUBDOMAIN: " + sub_domain + "----RECORDLINE: "+record["line"] )
                                    else:
                                        print("DELETE DNS ERROR: ----Time: "  + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) + "----DOMAIN: " + domain + "----SUBDOMAIN: " + sub_domain + "----RECORDLINE: "+record["line"] + "----MESSAGE: " + retMsg["message"] )
                    ret = cloud.get_record(domain, 100, sub_domain, RECORD_TYPE)
                    if DNS_SERVER != 1 or ret["code"] == 0 :
                        if DNS_SERVER == 1 and "Free" in ret["data"]["domain"]["grade"] and AFFECT_NUM > 2:
                            AFFECT_NUM = 2
                        cm_info = []
                        cu_info = []
                        ct_info = []
                        ab_info = []
                        def_info = []
                        for record in ret["data"]["records"]:
                            if record["line"] == "移动":
                                info = {}
                                info["recordId"] = record["id"]
                                info["value"] = record["value"]
                                cm_info.append(info)
                            if record["line"] == "联通":
                                info = {}
                                info["recordId"] = record["id"]
                                info["value"] = record["value"]
                                cu_info.append(info)
                            if record["line"] == "电信":
                                info = {}
                                info["recordId"] = record["id"]
                                info["value"] = record["value"]
                                ct_info.append(info)
                            if record["line"] == "境外":
                                info = {}
                                info["recordId"] = record["id"]
                                info["value"] = record["value"]
                                ab_info.append(info)
                            if record["line"] == "默认":
                                info = {}
                                info["recordId"] = record["id"]
                                info["value"] = record["value"]
                                def_info.append(info)
                        for line in lines:
                            if line == "CM":
                                changeDNS("CM", cm_info, temp_cf_cmips, domain, sub_domain, cloud)
                            elif line == "CU":
                                changeDNS("CU", cu_info, temp_cf_cuips, domain, sub_domain, cloud)
                            elif line == "CT":
                                changeDNS("CT", ct_info, temp_cf_ctips, domain, sub_domain, cloud)
                            elif line == "AB":
                                changeDNS("AB", ab_info, temp_cf_abips, domain, sub_domain, cloud)
                            elif line == "DEF":
                                if record["name"] == "cu":
                                    changeDNS("DEF", def_info, temp_cf_cuips, domain, sub_domain, cloud)
                                elif record["name"] == "ct":
                                    changeDNS("DEF", def_info, temp_cf_ctips, domain, sub_domain, cloud)
                                elif record["name"] == "cm":
                                    changeDNS("DEF", def_info, temp_cf_cmips, domain, sub_domain, cloud)
                                elif record["name"] == "ab":
                                    changeDNS("DEF", def_info, temp_cf_abips, domain, sub_domain, cloud) 
                                else:
                                    changeDNS("DEF", def_info, temp_cf_defips, domain, sub_domain, cloud)        
        except Exception as e:
            print("CHANGE DNS ERROR: ----Time: " + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) + "----MESSAGE: " + str(traceback.print_exc()))

# ------------------   New  ---------------
def cf_update():    
    cf = CloudFlare.CloudFlare(
        email = str(CF_EMAIL),
        token = str(CF_TOKEN)
    )
    #zones = cf.zones.get()
    #for zone in zones:
    #    zone_id = zone['id']
    #    zone_name = zone['name']
    #    print("zone_id=%s zone_name=%s" % (zone_id, zone_name))
    sub_domain_num = CF_SUB_DOMAIN_NUM
    if len(CF_DOMAINS) > 0:
        try:
            cfips = get_optimization_ip()
            if cfips == None or cfips["code"] != 200:
                print("GET CLOUDFLARE IP ERROR: ----Time: " + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) + "----MESSAGE: " + str(cfips["info"]))
                return
            cf_cmips = cfips["info"]["CM"]
            cf_cuips = cfips["info"]["CU"]
            cf_ctips = cfips["info"]["CT"]

            cf_cmips_arr = list(map(lambda x:x["ip"] ,cf_cmips)  )
            cf_cuips_arr = list(map(lambda x:x["ip"] ,cf_cuips)  )
            cf_ctips_arr = list(map(lambda x:x["ip"] ,cf_ctips)  )
            cf_allip_arr = cf_cmips_arr + cf_cuips_arr + cf_ctips_arr
            
            #list(map(function,list1[]))
            #print(cf_cmips_arr)

            # print(cf_cuips,cf_ctips,cf_cmips,len(cf_cuips))   # 20个ip
            # print(cf_cuips,len(cf_cuips)) 
            if sub_domain_num > len(cf_cuips):
                sub_domain_num = len(cf_cuips)

            for domain, sub_domains in CF_DOMAINS.items():   #xxx.top   @  // xxx  cu
                # Get zone ID (for the domain). This is why we need the API key and the domain API token won't be sufficient
                #zone = ".".join("cu.xxx.top".split(".")[-2:]) # domain = test.mydomain.com => zone = mydomain.com
                zone = domain
                print("zone: ",zone) #xxx.top
                # query for the zone name and expect only one value back
                try:
                    #zones = cf.zones.get(params = {'name':zone_name,'per_page':1})
                    zones = cf.zones.get(params={"name": zone})
                except CloudFlare.exceptions.CloudFlareAPIError as e:
                    exit('/zones.get %d %s - api call failed' % (e, e))
                except Exception as e:
                    exit('/zones.get - %s - api call failed' % (e))
                
                if len(zones) == 0:
                    print(f"Could not find CloudFlare zone {zone}, please check domain {domain}" )
                    sys.exit(2)
                zone_id = zones[0]["id"]  # zone id :940fbc9916da0e619ea9544460bafcfd
                # print("zone_id: ",zone_id)

                for sub_domain, lines in sub_domains.items():    # cu  dea // ct ct  // cm cm
                    # print(sub_domain, ":sub domain  -  lines:   ", lines)  # cu   [DEF]
                    # Fetch existing A record
                    #a_records = cf.zones.dns_records.get(zone_id, params={"name": "cu.xxx.top", "type": "A"})
                    fdomain =  ".".join([sub_domain,zone])   #cu.xxx.top
                    print("domain full: ",fdomain)
                    a_records = cf.zones.dns_records.get(zone_id, params={"name": fdomain, "type": "A"}) 
                    #print("Records  in domain: " ,fdomain , "------" ,a_records)
                    i = 1
                    rec_ips = list(map(lambda x:x["content"] , a_records ))
                    # print("Record ips  in domain: " ,fdomain , "------" ,rec_ips)

                    for a_record in a_records:
                        #if len(a_records): # Have an existing record
                        print("Found existing record, updating...", len(a_records),"  %d "%i,a_record["id"], cf_cuips[i]["ip"] )

                        #a_record = a_records[0]
                        # Update record & save to cloudflare
                        #a_record["content"] 
                        if a_record["content"] in cf_allip_arr:
                            # str = "the length of (%s) is %d" %('runoob',len('runoob'))
                            print("Found same ip in  existing record: (%s)   (%s)  (%s)"%(a_record["name"],a_record["id"] ,a_record["content"]) )
                        else:
                            #cf.zones.dns_records.put(zone_id, a_record["id"], data=a_record)
                            if i< len( lines):
                                if lines[i-1] == "CM":
                                    newip =  cf_cmips[i]["ip"] 
                                    #changeDNS("CM", cm_info, temp_cf_cmips, domain, sub_domain, cloud)
                                elif lines[i-1] == "CU":
                                    newip =  cf_cuips[i]["ip"] 
                                    #changeDNS("CU", cu_info, temp_cf_cuips, domain, sub_domain, cloud)
                                elif lines[i-1] == "CT":
                                    newip =  cf_ctips[i]["ip"] 
                                    #changeDNS("CT", ct_info, temp_cf_ctips, domain, sub_domain, cloud)
                                elif lines[i-1] == "AB":
                                    newip =  cf_cuips[i]["ip"] 
                                    #changeDNS("AB", ab_info, temp_cf_abips, domain, sub_domain, cloud)
                                elif lines[i-1] == "DEF":
                                    newip =  cf_cuips[i]["ip"] 
                                a_record["content"] = newip
                                cf.zones.dns_records.put(zone_id, a_record["id"], data=a_record)
                                print("UPDATE DNS SUCCESS: ----Time: " + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) + "----DOMAIN: " + domain + "----SUBDOMAIN: " + sub_domain + "----RECORDLINE: "+lines[i-1]+"----VALUE: " + a_record["content"])
                                #log_cf2dns.logger.error("CREATE DNS ERROR: ----Time: " + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) + "----DOMAIN: " + domain + "----SUBDOMAIN: " + sub_domain + "----RECORDLINE: "+lines[i-1]+"----RECORDID: " + str(a_record["id"]) + "----VALUE: " + a_record["content"] + "----MESSAGE: "  )#+ ret["message"]
                            else:
                                print("New config length changed")
                                r = cf.zones.dns_records.delete(zone_id, a_record["id"])
                                print("DELETE DNS SUCCESS: ----Time: " + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) + "----DOMAIN: " + domain + "----SUBDOMAIN: " + sub_domain + "----RECORDLINE: "+lines[i-1]+"----VALUE: " + a_record["content"])

                                #cf.zones.dns_records.put(zone_id, a_record["id"], data=a_record)
                                #cf.zones.dns_records.put(zone_id, a_record["id"], data=a_record)
                            #a_record["content"] =  cf_cuips[i]["ip"] 
                            # if a_record["content"] == newip :
                            #     print(" existing ip in record ",newip)
                            # else:
                            #     a_record["content"]  = newip
                            #     cf.zones.dns_records.put(zone_id, a_record["id"], data=a_record)
                        i = i+1


                    if i<len(lines)+1:       #                else: # No existing record. Create !
                        for ii in range(i,len(lines)+1):  
                            print("Record doesn't existing, creating new record...new", ii,  cf_cuips[ii]["ip"])
                            
                            a_record = {}
                            a_record["type"] = "A"
                            a_record["name"] = fdomain
                            a_record["ttl"] = 1 # 1 == auto
                            a_record["content"] = cf_cuips[ii]["ip"] 
                            #cf.zones.dns_records.post(zone_id, data=a_record)


                            if lines[i-1] == "CM":
                                newip =  cf_cmips[ii]["ip"]
                                #changeDNS("CM", cm_info, temp_cf_cmips, domain, sub_domain, cloud)
                            elif lines[i-1] == "CU":
                                newip =  cf_cuips[ii]["ip"] 
                                #changeDNS("CU", cu_info, temp_cf_cuips, domain, sub_domain, cloud)
                            elif lines[i-1] == "CT":
                                newip =  cf_ctips[ii]["ip"] 
                                #changeDNS("CT", ct_info, temp_cf_ctips, domain, sub_domain, cloud)
                            elif lines[i-1] == "AB":
                                newip =  cf_cuips[ii]["ip"] 
                                #changeDNS("AB", ab_info, temp_cf_abips, domain, sub_domain, cloud)
                            elif lines[i-1] == "DEF":
                                newip =  cf_cuips[ii]["ip"] 
                            a_record["content"] = newip

                            cf.zones.dns_records.post(zone_id, data=a_record)    
                            print("CREATE DNS SUCCESS: ----Time: " + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) + "----DOMAIN: " + domain + "----SUBDOMAIN: " + sub_domain + "----RECORDLINE: "+lines[i-1]+"----VALUE: " + a_record["content"])
  
        except Exception as e:
            traceback.print_exc()  
            print("CHANGE DNS ERROR: ----Time: " + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) + "----MESSAGE: " + str(e))
#-------------------------------------------

if __name__ == '__main__':
    if DNS_SERVER == 1:
        cloud = QcloudApiv3(SECRETID, SECRETKEY)
    elif DNS_SERVER == 2:
        cloud = AliApi(SECRETID, SECRETKEY, REGION_ALI)
    elif DNS_SERVER == 3:
        cloud = HuaWeiApi(SECRETID, SECRETKEY, REGION_HW)
    main(cloud)
    #---------------------------
    cf_update()
