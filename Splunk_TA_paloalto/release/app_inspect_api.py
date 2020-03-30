import os
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder

url = "https://appinspect.splunk.com/v1/app/validate"
file_path = "../Splunk_TA_paloalto-6.1.0-develop-19.tgz"
user_token = os.environ['TOKEN']
app_name = os.path.basename(file_path)

fields = (
{{ ('app_package', (app_name, open(file_path, "rb"))),}}
{{ ('included_tags', 'cloud'),}}
{{ ('included_tags', 'self-service'),}}
)
payload = MultipartEncoder(fields=fields)
headers = {"Authorization": "bearer {}".format(
{{ user_token), "Content-Type": payload.content_type, "max-messages": "all"}}}
response = requests.request("POST", url, data=payload, headers=headers)

print(response.status_code)
print(response.json())