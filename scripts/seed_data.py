#!/usr/bin/env python3
"""
Seed the tracker with a real SEG SaaS Index snapshot + first-pass judgment tags.

Data: pulled from softwareequity.com/saas-index (source: Tiingo), LTM/TTM basis.
Tags (vh_class, model_purity) are a FIRST PASS for your review — override freely.
Once scrape_seg.py runs on a cron, it overwrites the market fields; the tag map
below is the sticky judgment layer and is re-joined by ticker.

Run:  python3 scripts/seed_data.py   ->  ../data/companies.json
"""
import json, os, datetime

# ticker, name, ev_rev, growth%, gross_margin%, ebitda_margin%, nrr% (None=N/A),
# ytd%, mcap($M), vh_class, model_purity, review_flag
ROWS = [
    ("EGHT","8x8",0.8,2.9,64.6,7.3,None,16.4,305,"horizontal","pure-saas",False),
    ("ACIW","ACI Worldwide",2.8,7.1,49.0,25.1,None,-6.5,4300,"vertical","payments-blended",False),
    ("ADBE","Adobe",4.1,13.7,89.4,40.9,None,-26.6,100400,"horizontal","pure-saas",False),
    ("AFRM","Affirm",7.1,32.1,48.4,17.0,94,-11.9,21700,"vertical","lending",False),
    ("ALRM","Alarm.com",2.2,8.6,65.8,22.1,None,-14.5,2200,"vertical","pure-saas",True),
    ("ALKT","Alkami",4.4,32.7,57.8,-1.8,117,-25.9,1800,"vertical","pure-saas",True),
    ("AMPL","Amplitude",2.0,16.4,73.6,-20.1,104,-38.7,896,"horizontal","pure-saas",False),
    ("APPF","AppFolio",5.8,20.7,63.7,20.2,None,-28.4,5900,"vertical","pure-saas",False),
    ("APPN","Appian",2.2,20.4,71.8,4.6,111,-37.3,1600,"horizontal","pure-saas",False),
    ("ASAN","Asana",1.7,12.4,89.0,-17.8,96,-48.9,1600,"horizontal","pure-saas",False),
    ("TEAM","Atlassian",3.7,24.7,84.0,-0.3,120,-44.8,22500,"infrastructure","pure-saas",False),
    ("ADSK","Autodesk",7.1,20.4,91.0,25.0,108,-16.0,51100,"vertical","pure-saas",True),
    ("AVPT","AvePoint",4.0,27.1,73.7,15.2,111,-22.2,2200,"infrastructure","pure-saas",True),
    ("BAND","Bandwidth",2.9,4.9,38.2,6.4,107,331.7,1900,"infrastructure","comms-blended",False),
    ("BILL","Bill.com",1.5,12.5,80.7,7.8,94,-28.5,3600,"horizontal","pure-saas",False),
    ("BL","BlackLine",2.6,8.1,75.4,15.7,105,-46.3,1700,"horizontal","pure-saas",False),
    ("BLKB","Blackbaud",1.8,-0.7,59.2,27.8,None,-50.3,1400,"vertical","payments-blended",True),
    ("BOX","Box",3.2,9.3,79.2,12.1,104,-10.2,3700,"horizontal","pure-saas",False),
    ("BRZE","Braze",3.3,31.9,67.1,-14.8,109,-25.2,2700,"horizontal","pure-saas",False),
    ("AI","C3.ai",2.2,-16.2,43.5,-136.5,None,-32.4,1300,"horizontal","services-blended",True),
    ("LAW","CS Disco",0.9,11.1,74.9,-22.1,98,-47.4,243,"vertical","pure-saas",False),
    ("CCLD","CareCloud",0.8,10.3,47.0,22.5,None,-21.6,97,"vertical","services-blended",False),
    ("NET","Cloudflare",32.4,31.6,73.3,9.0,119,10.3,76100,"infrastructure","pure-saas",False),
    ("BIGC","BigCommerce",0.7,3.5,78.1,2.3,111,-26.6,245,"horizontal","pure-saas",True),
    ("COUR","Coursera",0.1,9.8,54.8,-3.8,93,-24.9,895,"vertical","consumer",False),
    ("CRWD","CrowdStrike",33.8,29.2,74.7,4.1,115,46.3,167300,"security","pure-saas",False),
    ("DDOG","Datadog",20.4,29.5,79.9,7.2,120,66.2,78400,"infrastructure","pure-saas",False),
    ("DH","Definitive Healthcare",0.5,-3.9,76.0,-44.4,90,-64.1,123,"vertical","pure-saas",False),
    ("DSGX","Descartes",7.9,12.0,77.1,41.9,None,-16.3,6100,"vertical","pure-saas",True),
    ("DOCN","DigitalOcean",16.2,17.6,58.5,39.0,99,223.6,14600,"infrastructure","pure-saas",False),
    ("DCBO","Docebo",2.8,-17.6,107.6,4.5,99,-22.4,500,"horizontal","pure-saas",True),  # GM 107.6 = data artifact, verify
    ("DOCU","Docusign",2.9,9.9,79.4,15.1,101,-23.6,9900,"horizontal","pure-saas",False),
    ("DOMO","Domo",0.8,0.8,75.0,-13.2,96,-56.3,152,"horizontal","pure-saas",False),
    ("DBX","Dropbox",3.7,-0.6,79.7,35.1,None,1.9,6600,"horizontal","pure-saas",False),
    ("DT","Dynatrace",5.6,18.8,81.6,16.0,111,-2.7,12300,"infrastructure","pure-saas",False),
    ("ESTC","Elastic",3.1,17.3,76.0,2.9,112,-24.5,5800,"infrastructure","pure-saas",False),
    ("EVCM","EverCommerce",3.9,-11.5,77.5,22.1,97,-7.4,1900,"vertical","pure-saas",True),
    ("FSLY","Fastly",3.9,17.7,59.4,0.4,111,60.2,2500,"infrastructure","pure-saas",True),
    ("FIVN","Five9",1.5,9.3,55.3,13.9,107,21.0,1700,"horizontal","comms-blended",False),
    ("FTV","Fortive",4.5,-23.4,61.8,24.3,None,6.8,18200,"horizontal","diversified",True),  # growth distorted by 2025 spinoff
    ("FRSH","Freshworks",2.1,15.9,85.0,9.4,108,-21.7,2600,"horizontal","pure-saas",False),
    ("GTLB","Gitlab",3.4,33.2,87.4,-3.6,118,-26.1,4500,"infrastructure","pure-saas",False),
    ("GWRE","Guidewire",8.7,23.7,63.8,17.0,None,-25.2,11900,"vertical","pure-saas",False),
    ("HCAT","Health Catalyst",0.5,-2.8,49.9,-64.2,100,-43.4,95,"vertical","services-blended",False),
    ("HSTM","HealthStream",2.1,6.6,64.9,22.4,None,4.5,699,"vertical","pure-saas",False),
    ("HUBS","HubSpot",2.8,21.1,83.7,8.1,104,-47.2,10700,"horizontal","pure-saas",False),
    ("INTA","Intapp",2.7,15.9,75.0,-1.4,124,-53.5,1600,"vertical","pure-saas",False),
    ("FROG","Jfrog",14.4,25.0,77.5,-4.0,119,24.2,8900,"infrastructure","pure-saas",False),
    ("KLTR","Kaltura",1.1,-1.3,71.2,-0.1,97,-7.1,216,"horizontal","pure-saas",True),
    ("KVYO","Klaviyo",2.8,30.3,74.6,3.2,108,-49.3,4500,"horizontal","pure-saas",True),
    ("LPSN","LivePerson",1.3,-19.2,71.7,-1.5,78,-44.0,26,"horizontal","pure-saas",False),
    ("MSCI","MSCI",15.3,10.9,82.9,61.8,93,4.1,43200,"vertical","data-ip",False),
    ("MNDY","Monday.com",2.3,25.4,89.1,1.7,110,-44.9,4000,"horizontal","pure-saas",False),
    ("MDB","MongoDB",9.8,28.0,71.7,-0.6,120,-18.4,26500,"infrastructure","pure-saas",False),
    ("NCNO","Ncino",3.4,13.0,60.6,11.1,112,-34.8,1800,"vertical","pure-saas",False),
    ("NTNX","Nutanix",4.6,15.9,87.1,14.0,107,-6.9,12700,"infrastructure","pure-saas",False),
    ("OKTA","Okta",4.9,16.2,77.4,12.2,106,10.3,16300,"security","pure-saas",False),
    ("ORCL","Oracle",10.4,14.9,67.1,47.8,102,-1.9,551900,"horizontal","pure-saas",True),
    ("PTC","PTC",6.2,27.7,84.7,59.2,None,-12.9,17600,"vertical","pure-saas",True),
    ("PD","Pagerduty",1.2,7.2,84.9,9.2,100,-41.9,661,"infrastructure","pure-saas",False),
    ("PANW","Palo Alto Networks",17.9,15.4,73.5,23.1,119,45.3,181600,"security","pure-saas",False),
    ("PAYC","Paycom",3.9,9.4,83.4,40.1,None,-9.6,7500,"horizontal","pure-saas",False),
    ("PCTY","Paylocity",3.4,11.3,69.3,27.7,91,-22.4,6100,"horizontal","pure-saas",False),
    ("PEGA","Pegasystems",3.2,3.5,75.0,13.0,109,-38.7,5800,"horizontal","pure-saas",False),
    ("PCOR","Procore",4.8,14.9,79.8,3.1,95,-33.1,7000,"vertical","pure-saas",False),
    ("QTWO","Q2 Holdings",3.5,14.0,55.6,16.5,113,-33.6,2900,"vertical","pure-saas",True),
    ("QLYS","Qualys",4.7,10.2,83.1,39.0,103,-21.9,3700,"security","pure-saas",False),
    ("RPD","Rapid7",0.9,1.2,69.7,9.6,None,-49.1,479,"security","pure-saas",False),
    ("RNG","RingCentral",1.9,4.9,71.6,14.8,99,57.8,3700,"horizontal","pure-saas",False),
    ("RSKD","Riskified",1.3,5.1,52.4,-4.9,96,-1.0,705,"horizontal","payments-blended",True),
    ("ROP","Roper Technologies",5.4,12.1,69.4,31.5,None,-24.8,33700,"horizontal","diversified",True),
    ("RBRK","Rubrik",9.7,48.5,80.1,-20.7,120,-11.8,13300,"security","pure-saas",True),
    ("SAP","SAP",4.6,15.3,72.8,30.1,None,-25.7,205400,"horizontal","pure-saas",False),
    ("SPSC","SPS Commerce",2.4,13.8,69.3,23.8,None,-38.9,2000,"vertical","pure-saas",False),
    ("CRM","Salesforce",4.2,12.2,77.7,31.7,None,-29.0,168700,"horizontal","pure-saas",False),
    ("IOT","Samsara",10.6,46.2,76.7,1.5,115,-8.2,18000,"vertical","pure-saas",True),
    ("S","SentinelOne",5.7,30.3,74.1,-22.0,110,27.8,6400,"security","pure-saas",False),
    ("NOW","ServiceNow",7.5,21.7,76.6,23.0,98,-30.7,106800,"horizontal","pure-saas",False),
    ("TTAN","ServiceTitan",5.8,24.5,70.1,-6.3,110,-37.8,5900,"vertical","pure-saas",False),
    ("SHOP","Shopify",10.2,31.8,48.0,13.5,None,-34.5,134300,"horizontal","payments-blended",True),
    ("SNOW","Snowflake",12.3,36.9,67.2,-21.8,125,-20.5,58900,"infrastructure","pure-saas",False),
    ("CXM","Sprinklr",1.0,10.8,67.4,11.0,103,-28.0,1300,"horizontal","pure-saas",False),
    ("SPT","Sprout Social",0.7,12.3,77.5,-4.6,104,-34.1,406,"horizontal","pure-saas",False),
    ("TENB","Tenable",2.9,10.7,78.2,7.0,106,12.0,2900,"security","pure-saas",False),
    ("TDC","Teradata",1.7,-0.8,60.1,40.1,100,12.6,3100,"infrastructure","pure-saas",False),
    ("TTD","The Trade Desk",3.3,15.5,77.8,26.8,95,-40.6,10700,"horizontal","pure-saas",False),
    ("TOST","Toast",1.8,23.4,26.3,7.4,111,-31.9,13600,"vertical","payments-blended",False),
    ("TWLO","Twilio",5.1,15.7,48.7,5.9,108,35.8,28500,"infrastructure","comms-blended",False),
    ("TYL","Tyler Technologies",5.5,8.7,46.8,23.5,None,-28.1,13500,"vertical","services-blended",False),
    ("PATH","UiPath",2.8,12.7,83.2,8.4,107,-31.2,5800,"horizontal","pure-saas",False),
    ("UPLD","Upland",1.1,-24.6,75.9,17.4,96,-53.0,21,"horizontal","pure-saas",False),
    ("VRNS","Varonis",5.1,15.2,78.1,-18.6,110,-3.2,3600,"security","pure-saas",False),
    ("VEEV","Veeva",6.2,21.8,75.5,39.0,102,-27.0,26300,"vertical","pure-saas",False),
    ("VRSK","Verisk",8.9,5.9,70.0,54.4,None,-22.6,23600,"vertical","data-ip",False),
    ("VERI","Veritone",2.5,-7.2,67.6,-85.5,None,-55.3,197,"horizontal","services-blended",True),
    ("VERX","Vertex",2.9,11.8,64.3,12.4,105,-29.3,2100,"horizontal","pure-saas",False),
    ("WAY","Waystar",4.4,18.6,68.7,35.7,112,-37.6,3800,"vertical","pure-saas",False),
    ("WEAV","Weave",1.7,16.8,72.3,-2.8,93,-20.4,449,"vertical","pure-saas",True),
    ("WIX","Wix",1.2,13.6,67.4,-3.5,105,-47.3,2900,"horizontal","pure-saas",False),
    ("WDAY","Workday",3.3,13.3,75.8,17.6,None,-37.7,33700,"horizontal","pure-saas",False),
    ("WK","Workiva",3.0,20.3,79.4,4.4,113,-39.4,2900,"horizontal","pure-saas",False),
    ("YEXT","Yext",1.1,6.1,74.5,18.8,97,-53.1,451,"horizontal","pure-saas",False),
    ("ZD","Ziff Davis",1.4,-1.8,85.3,23.2,None,28.6,1600,"horizontal","diversified",True),
    ("ZM","Zoom",4.8,5.0,77.4,56.6,98,26.8,31300,"horizontal","pure-saas",False),
    ("GTM","ZoomInfo",2.0,3.6,83.8,26.6,90,-62.4,1100,"horizontal","pure-saas",False),
    ("ZS","Zscaler",9.1,23.9,76.5,6.9,114,-17.3,29100,"security","pure-saas",False),
]

def size_bucket(mcap):
    if mcap >= 50000: return "Mega (>$50B)"
    if mcap >= 10000: return "Large ($10-50B)"
    if mcap >= 2000:  return "Mid ($2-10B)"
    return "Small (<$2B)"

def growth_bucket(g):
    if g < 10:  return "<10%"
    if g < 20:  return "10-20%"
    if g < 30:  return "20-30%"
    return "30%+"

def main():
    out = []
    for (tk,name,evrev,g,gm,eb,nrr,ytd,mcap,vh,purity,review) in ROWS:
        out.append({
            "ticker": tk, "name": name,
            "ev_rev": evrev, "rev_growth": g, "gross_margin": gm,
            "ebitda_margin": eb, "nrr": nrr, "ytd_change": ytd, "mcap_m": mcap,
            # judgment layer (first-pass, reviewable)
            "vh_class": vh, "model_purity": purity, "review": review,
            # derived
            "size_bucket": size_bucket(mcap),
            "growth_bucket": growth_bucket(g),
            "r40_ebitda": round(g + eb, 1),           # standard R40 on EBITDA basis (FCF basis added in v1)
            "clean_comp": purity == "pure-saas",       # eligible for percentile ranking
        })
    payload = {
        "as_of": datetime.date.today().isoformat(),
        "source": "SEG SaaS Index (softwareequity.com) / Tiingo — TTM basis",
        "basis": "LTM/TTM",
        "n": len(out),
        "companies": sorted(out, key=lambda x: x["name"].lower()),
    }
    here = os.path.dirname(os.path.abspath(__file__))
    dest = os.path.join(here, "..", "data", "companies.json")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w") as f:
        json.dump(payload, f, indent=2)
    # quick integrity report
    pure = sum(1 for c in out if c["clean_comp"])
    review = sum(1 for c in out if c["review"])
    print(f"Wrote {len(out)} companies -> {os.path.normpath(dest)}")
    print(f"  clean-comp (pure-saas): {pure}   flagged-for-review: {review}")
    from collections import Counter
    print("  vh_class:", dict(Counter(c['vh_class'] for c in out)))
    print("  model_purity:", dict(Counter(c['model_purity'] for c in out)))

if __name__ == "__main__":
    main()
