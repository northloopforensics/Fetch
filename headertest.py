import re
import geocoder
from email import parser
import pandas
import json

invalid_ips = ['0', '10.', '172.16', '172.17', '172.18', '172.19', '172.2',  '172.21', '172.22', '172.23', '172.24', '172.25',
            '172.26', '172.27', '172.28', '172.29', '172.30',  '172.31', '192.168', '169.254', "255.255" ,"fc00"]

header = """X-Ms-Exchange-Crosstenant-Originalarrivaltime: 11 May 2023 18:31:12.2717 (UTC)
X-Proofpoint-Orig-Guid: jrVOzC7TNIxEIyc_lQ0FfWn3Jsniir5_
X-Ms-Exchange-Transport-Crosstenantheadersstamped: BN2P110MB1301
X-Forefront-Antispam-Report: CIP:255.255.255.255;CTRY:;LANG:en;SCL:1;SRV:;IPV:NLI;SFV:NSPM;H:BN2P110MB1495.NAMP110.PROD.OUTLOOK.COM;PTR:;CAT:NONE;SFS:(13230028)(4636009)(366004)(451199021)(8676002)(8936002)(66556008)(5660300002)(55016003)(52536014)(33656002)(40140700001)(38070700005)(53546011)(86362001)(9686003)(83380400001)(38100700002)(6506007)(186003)(7696005)(99936003)(26005)(82960400001)(66446008)(64756008)(76116006)(66946007)(66476007)(71200400001)(45080400002)(498600001)(122000001)(6862004)(2906002);DIR:OUT;SFP:1102;
Authentication-Results: mx.google.com; dkim=pass header.i=@usdoj.gov header.s=doj header.b=MFwBzaYs; arc=fail (signature failed); spf=pass (google.com: domain of kimberly.purdie@usdoj.gov designates 2607:f330:6000:1023:1a66:daff:feb7:73b1 as permitted sender) smtp.mailfrom=Kimberly.Purdie@usdoj.gov; dmarc=pass (p=REJECT sp=REJECT dis=NONE) header.from=usdoj.gov
X-Ms-Exchange-Crosstenant-Authsource: BN2P110MB1495.NAMP110.PROD.OUTLOOK.COM
X-Received: by 2002:a05:6214:c8d:b0:5e3:d150:3168 with SMTP id r13-20020a0562140c8d00b005e3d1503168mr29635675qvr.18.1683829912704; Thu, 11 May 2023 11:31:52 -0700 (PDT)
Return-Path: <Kimberly.Purdie@usdoj.gov>
X-Proofpoint-Guid: jrVOzC7TNIxEIyc_lQ0FfWn3Jsniir5_
X-Ms-Exchange-Crosstenant-Fromentityheader: Hosted
X-Ms-Tnef-Correlator: 
X-Ms-Exchange-Crosstenant-Id: 15ef12a1-af58-44c4-b029-712fc0605570
<DM8PR09MB68214A8995DE4F13D55D2972CC749@DM8PR09MB6821.namprd09.prod.outlook.com>
X-Ms-Exchange-Antispam-Messagedata-Chunkcount: 1
X-Ms-Publictraffictype: Email
X-Google-Smtp-Source: ACHHUZ68AbPGeZ6fL33k6HBM/HlqmroUh7IFTxjcoWrjipT0w+a5/H43Qi9UYOMnlwgoemCB1v01
X-Ms-Exchange-Crosstenant-Authas: Internal
Arc-Seal: i=1; a=rsa-sha256; s=arcselector5401; d=microsoft.com; cv=none; b=jYyRYSV1WQ+4G+oKqx2I5lAxT9hmYALlnMyf42Uv5PJaHm274ng7vAovs2vHPDazP9X1ID1wQFVjK/kQf0GZWHu2rMFAHhS/pFJPPKXvVJ+CqmoV1ww2QK7dpDSb7Moqgl+6YA2+jPjTYf7LzHebOzqxJzB8AWqajqv5vejfFob/PqhdqXW+iY+Nm/88NQoj8XT1HZDx/c9J4A/tTAhea4s8jZWtn+X0nNu2StotFRcZPDf8F9nMu1tgMQSFoh/+brg6NOZtZaFrULw+ULrMBP0KuNn75eV7R3DhRVRJ209DdRwHHQ4lg5FoJ9A3jPkBrXLNokWUkBwXj7j8LcqspQ==
<DM8PR09MB68214A8995DE4F13D55D2972CC749@DM8PR09MB6821.namprd09.prod.outlook.com>
Thread-Index: AdmEK+rb0uLU44XxR1SvXt/2alxjRgACsf3g
X-Ms-Exchange-Senderadcheck: 1
X-Ms-Exchange-Antispam-Messagedata-0: K7QtU/rhjt57XCBrxcJwRY7wse8HGc8DX4mCc1I33NPs4l4Cc37cR0ThHE0FEdTM+EZnMMGnVNMc/Wg3oCAkRH4JLo+HZOuvMGOCOGL/pUkWO3JkTcrSRzuJiNoib0hSFx32m1sy6SKETju7BdlW83eQj6X0UmlAlPfMeMMV5rrLcnqiiKrgmLj6PcpGY3nmDY0b0ssOqGU3eT4yC6TAhX6jbQ7NbtOFmcLWbBvzU7cEGarx+VKaAi1hSU9YQ6SnSGeHYsbaNxb/wJHX16xm/OX2s9n74eAXf2lL056hyqX13p1Au4HNYHruo6hCeupXG3FF4DNCJVjQZ40FXgwybOZBbmXux8cJUlq7NAcKEanrHaS4+yAycuNzqARzoSy6e15QCFmtSXrJou3nehiTW4ovmKeyKiJLUseGBL0mFHE=
Accept-Language: en-US
X-Microsoft-Antispam-Message-Info: R++/gOCioDQsYs84VtXgjHv9HfF80qBWLyf0iwhj23e6/ANWSGXK5oD4UNeIFsy38dbEjHpdQH35y66ya8PbRlf/pI1pmrHU4a2GdnODudgD16ZcnWJsb4y3ikdb5HJF1vl59TiVJ94rgsLMWjT2PTpuKc/QK5XMDxZN7p0qvnOoT4ZRyoImVPs6hKE6v4N465y86/VE3Go2z+YEAxtQjHMT7TJEvKhA7lB+CLDHaib3BQpNQ8EuPs+OGR+ydGafn8T1Bqz2hqAlsSQWJO3dyBez0XZX1nG6410zwRKgpR9tdox+a2unzQgKQIVh9pBqk/KMASf3mGZj4Yh3rEv2jo85OR8fa6sOtMMppFgdHuhvf1Cu6lOuiIni80F/eHCNzB7gOkzjJcEFUditV6YKNCUFeLUNiunhxY+Pf50FprwdkPVCDBA4WwFRH0vrudyQRToK4w7IbH7svF/Ppcow6OLD3UsVdWVhysOIyQCybiPVu3o6v6oZ4oEq/TuLA3ZbwISm0BuI4EsXIg3I18btqMyoTkXZWx0QH4scTrcb+qMujIFMt3kLhakWJjiAM5nBVJm4pXVCbmKO+DrXjWo3C5TwBuB3ZixWvnPhIAF6Y/6ESVMpER4HFTqgvqFQ6ihW
<BN2P110MB1495336749DE2E61305DB0FDF6749@BN2P110MB1495.NAMP110.PROD.OUTLOOK.COM>
X-Microsoft-Antispam: BCL:0;
Content-Language: en-US
Arc-Authentication-Results: i=1; mx.microsoft.com 1; spf=pass smtp.mailfrom=usa.doj.gov; dmarc=pass action=none header.from=usa.doj.gov; dkim=pass header.d=usa.doj.gov; arc=none
Mime-Version: 1.0
X-Proofpoint-Virus-Version: vendor=baseguard engine=ICAP:2.0.254,Aquarius:18.0.942,Hydra:6.0.573,FMLib:17.11.170.22 definitions=2023-05-11_15,2023-05-05_01,2023-02-09_01
X-Proofpoint-Virus-Version: vendor=baseguard engine=ICAP:2.0.254,Aquarius:18.0.942,Hydra:6.0.573,FMLib:17.11.170.22 definitions=2023-05-11_15,2023-05-05_01,2023-02-09_01
X-Ms-Office365-Filtering-Correlation-Id: f5c88637-d6f3-4f87-d618-08db524de5b4
X-Proofpoint-Spam-Details: rule=notspam policy=default score=0 spamscore=0 mlxlogscore=999 bulkscore=0 adultscore=0 suspectscore=0 phishscore=0 malwarescore=0 mlxscore=0 classifier=spam adjust=0 reason=mlx scancount=1 engine=8.12.0-2304280000 definitions=main-2305110158
Received: by 2002:a05:6919:2902:b0:179:7f82:7469 with SMTP id pg2csp4209325ysb; Thu, 11 May 2023 11:31:53 -0700 (PDT)
Received: from mx-jcotsb.usdoj.gov (mx-jcotsb.usdoj.gov. [2607:f330:6000:1023:1a66:daff:feb7:73b1]) by mx.google.com with ESMTPS id t4-20020ad45bc4000000b006165793d228si4220041qvt.329.2023.05.11.11.31.52 for <charlierubisoff@gmail.com> (version=TLS1_2 cipher=ECDHE-RSA-AES128-GCM-SHA256 bits=128/128); Thu, 11 May 2023 11:31:52 -0700 (PDT)
Received: from mx.doj.gov ([10.187.137.62]) by DJJMDCJC02-PPOINT07.jcots.jutnet.net (8.17.1.5/8.17.1.5) with ESMTP id 34BIVpM3016882 for <charlierubisoff@gmail.com>; Thu, 11 May 2023 18:31:51 GMT
Received: from CP-CAR-DC03.car.doj.gov ([10.222.1.23]) by pp-cefw-11.mail.doj.gov (8.17.1.5/8.17.1.5) with ESMTPS id 34BIV4HF021076 (version=TLSv1.2 cipher=ECDHE-RSA-AES256-SHA384 bits=256 verify=NOT) for <charlierubisoff@gmail.com>; Thu, 11 May 2023 18:31:48 GMT
Received: from USG02-CY1-obe.outbound.protection.office365.us (10.222.1.61) by CP-CAR-DC03.car.doj.gov (10.222.1.23) with Microsoft SMTP Server (TLS) id 14.3.498.0; Thu, 11 May 2023 14:31:12 -0400
Received: from BN2P110MB1495.NAMP110.PROD.OUTLOOK.COM (2001:489a:200:17d::9) by BN2P110MB1301.NAMP110.PROD.OUTLOOK.COM (2001:489a:200:179::11) with Microsoft SMTP Server (version=TLS1_2, cipher=TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384) id 15.20.6363.32; Thu, 11 May 2023 18:31:12 +0000
Received: from BN2P110MB1495.NAMP110.PROD.OUTLOOK.COM ([fe80::ec19:e127:3e09:5994]) by BN2P110MB1495.NAMP110.PROD.OUTLOOK.COM ([fe80::ec19:e127:3e09:5994%4]) with mapi id 15.20.6363.035; Thu, 11 May 2023 18:31:12 +0000
Content-Type: multipart/related; boundary="_004_BN2P110MB1495336749DE2E61305DB0FDF6749BN2P110MB1495NAMP_"; type="multipart/alternative"
X-Ms-Has-Attach: yes
Thread-Topic: NEXT Wednesday, May 17th -  Greater Jackson Law Enforcement Officers Association Luncheon
X-Ms-Exchange-Antispam-Externalhop-Messagedata-0: ETE/k6vxmpX2wnxlpQ2gn8echHtRR+tGlEgHBxc29IcOigguHvMaQcIHJmhK42EnJMLEsPX8rlyTTeLdrBvs2NAgvtn3UxBz0CIch4zN6Gyh8dLghQu4Ow7e3S9SIfyNvgjcyvrgxhyR0tpJopr3+MevxWA1h6yMBA1s1tiF5Rw52pxn2KKKtakycEAHDZLsDOtK5uXoIdaMQD42Qy1GvBMR4T4pr9Cl5CNQx4g59+6J9XPuEZcDT0N7l2CO0jKaXsQIzkIst2n3gGKFX54bcEhrdjhtsgDnZ34q8iC7Ki9pcwTCA3k1ZudToHmjHrnBlAEW/VCRSIMbGks4gNaxeGqZPJ4/q53aqqKKHM/o5VxQOSEg2GkB8vaNGwRi9XrVXRalwaHmJiMyubnNYq36YV4p7Qsk8JmX7Ho9z6VnZN7BMd4/VkOa26xOIlJHM9urlnLdI0T5FsgscMYaSujMucOscc9xyNBi3zdqjRQz1zREBnJuGOOdtjojL4gsAaZth52sz+AqnL4KKFKbgoXbZpb7ANgzl4odbSYkk3cfGEHFXG5PNLAEc87588d7t945M57WfcBUJmWHp+ddUajtNVbMDsjS6LDKZSTVvW5Rgr8fQJL+tG6XoatQX/t84UWbhAvUc3pqc5NS17vcVaLu6vcWNKef+vkUm+Cimn9+axwdkey41QzdReoAET+lImUPIda6MdTqRSRHDLk8BTJZ7BPDWwMvWkiGeFCLG60Etze/uXpWw8PtzBo3hOzESh0G
X-Ms-Traffictypediagnostic: BN2P110MB1495:EE_|BN2P110MB1301:EE_
Delivered-To: charlierubisoff@gmail.com
Received-Spf: pass (google.com: domain of kimberly.purdie@usdoj.gov designates 2607:f330:6000:1023:1a66:daff:feb7:73b1 as permitted sender) client-ip=2607:f330:6000:1023:1a66:daff:feb7:73b1;
X-Ms-Exchange-Antispam-Externalhop-Messagedata-Chunkcount: 1
X-Ms-Exchange-Crosstenant-Network-Message-Id: f5c88637-d6f3-4f87-d618-08db524de5b4
Arc-Message-Signature: i=1; a=rsa-sha256; c=relaxed/relaxed; d=microsoft.com; s=arcselector5401; h=From:Date:Subject:Message-ID:Content-Type:MIME-Version:X-MS-Exchange-AntiSpam-MessageData-ChunkCount:X-MS-Exchange-AntiSpam-MessageData-0:X-MS-Exchange-AntiSpam-MessageData-1; bh=8YfQtPEF4Vvs8btrRHFZl7gBxgP37s0hSIp/Hvhi/0g=; b=SdIWcJyZUskc/3F7ni+hIxIvWSLbR0sIhcExKmi/nAlU/5o3Itam1kHOE35vsdTbgfp5xJfWHbIXiHW9q3Wcnu41H7rtEI1zV90F/l0S6xim9IcRa27Dxbp+sSIa4YFuYBIjySnX4JEBba1vXjcu2i3z56hidr/7eG5/dzb5sbYAyOpAkqNRhoFpMNH0wmR9X8v7BD8s7J2wdn5p6DYQFqlLxzehsLvOtyQTF+5JHUIHhc/2w/N1HH54zsKJAiKpCP1OnhLSvKmMRLQH1ETudDdgDmTaYdvO+3i/TEXHxr/wK8L2GZZ6FcGLSn83Iv/J4d6GFyP0/PdevJwB52UMiw==
Dkim-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed; d=usdoj.gov; h=from : to : subject : date : message-id : references : in-reply-to : content-type : mime-version; s=doj; bh=8YfQtPEF4Vvs8btrRHFZl7gBxgP37s0hSIp/Hvhi/0g=; b=MFwBzaYsb/zPtlReqcy5w1ULOSJrkJ3Jaw7+I1dlnA+dhyc9cLjy29pGwblHwpF51SGc ITOKsVElPK5QuOp1RA6InY5hk1jf7pYQMtFf9fyHTlebEJoU3Qv0ZYQeGpWGiv9N7DZI OeLt9muulo/u9HcLu7Tnl53Wh7xTYAJ/+lBNlZpPTFUvLg4L6coEW4GlxLxlC+0WPvzi ufJC7bDw6MKCuHGEz71WL+kIIfgIGaFm4EHp3QAKjy6XswCCt9MO1+aRFPiWoGZ6NolG 1q4L6BHG9sMvboX8Nja3DK5a4sRMUExxyZ5NVq9/KQajqzNTxplLIAVC/pOrb71K2NdU 8Q== """

def parse_text_for_IPs(header_text):  
    ipv4_pattern = r'(?:\d{1,3}\.){3}\d{1,3}\b'
    ipv6_pattern = r'(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))'

    ipv4_addresses = re.findall(ipv4_pattern, header_text)
    ipv6_addresses = re.findall(ipv6_pattern, header_text)
    
    ipv6_list = []
    ip_list = list(set(ipv4_addresses))

    for address in ipv6_addresses:
        clean_ipv6 = [item for item in address if len(item) > 16]
        if clean_ipv6:      # checks for empty lists
            ipv6_list.append(clean_ipv6)
    unique_ip6_list = [str(inner_list[0]) for inner_list in ipv6_list]
    unique_ip6_list = list(set(unique_ip6_list))
    ip_list.extend(unique_ip6_list)
    return ip_list

stuff = parse_text_for_IPs(header)
# print(stuff)

# geo_data = {}
geo_list = []
def get_IP_locale(invalidList, IPs):
    valid_only = [address for address in IPs if not any(address.startswith(inval) for inval in invalidList)]
    for thing in valid_only:
        pull_geo_data = geocoder.ipinfo(thing)
        geo_list.append(pull_geo_data.json)
    # print(geo_list)
get_IP_locale(invalid_ips, stuff)

df = pandas.json_normalize(geo_list)
print(df)